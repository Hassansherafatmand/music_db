"""The database part of the website: a pool of MySQL connections, and the SQL files.

Every SQL statement the website runs lives in a .sql file in web/sql/, under a name:

    -- name: album_by_id
    -- One album, with its artist.
    SELECT ... FROM album WHERE album_id = %(album_id)s;

The Python code runs it by its name:  db.one("catalog.album_by_id", album_id=5)

%(album_id)s is a parameter. The driver sends the value separately from the SQL text,
so what a user types can never change the SQL (no SQL injection). It is the same idea
as the "?" from class, written the way the Python MySQL driver writes it.
"""

import re
import time
from contextlib import contextmanager
from pathlib import Path

import mysql.connector
from mysql.connector import errorcode, pooling
from flask import g

IntegrityError = mysql.connector.errors.IntegrityError

_SQL_DIR = Path(__file__).parent / "sql"
_NAME_LINE = re.compile(r"--\s*name:\s*(\w+)\s*$")

_queries = {}  # "catalog.album_by_id" -> {"sql": ..., "about": ...}
_pool = None


# ---------------------------------------------------------------- the SQL files

def load_queries():
    """Read every web/sql/*.sql file and remember each named statement."""
    _queries.clear()
    for path in sorted(_SQL_DIR.glob("*.sql")):
        name, lines = None, []
        for line in path.read_text(encoding="utf-8").splitlines():
            match = _NAME_LINE.match(line)
            if match:
                if name:
                    _remember(path.stem, name, lines)
                name, lines = match.group(1), []
            elif name:
                lines.append(line)
        if name:
            _remember(path.stem, name, lines)


def _remember(file_stem, name, lines):
    # The comment lines right under "-- name:" describe the statement. They are shown
    # on the page. Comments are notes for people, so they are not sent to MySQL.
    about = []
    for line in lines:
        if not line.strip().startswith("--"):
            break
        about.append(line.strip()[2:].strip())
    sql = "\n".join(l for l in lines if not l.strip().startswith("--")).strip()
    _queries[f"{file_stem}.{name}"] = {"sql": sql.rstrip(";").strip(), "about": " ".join(about)}


# ---------------------------------------------------------------- connections

def init_app(app):
    """Load the SQL files and open the connection pool when the website starts."""
    global _pool
    load_queries()
    try:
        # A pool keeps a few connections open, because opening a new one for every
        # page is slow. Each page borrows one and gives it back at the end.
        _pool = pooling.MySQLConnectionPool(
            pool_name="music_db",
            pool_size=8,
            host=app.config["MYSQL_HOST"],
            port=app.config["MYSQL_PORT"],
            user=app.config["MYSQL_USER"],
            password=app.config["MYSQL_PASSWORD"],
            database=app.config["MYSQL_DATABASE"],
            autocommit=True,
            charset="utf8mb4",
        )
    except mysql.connector.Error as err:
        raise RuntimeError(
            f"Could not connect to MySQL ({err}). Is MySQL running, and are the "
            "MYSQL_* settings in your .env file right? See README.md."
        ) from err
    app.teardown_appcontext(_give_back_connection)


def _connection():
    if "db" not in g:
        g.db = _pool.get_connection()
    return g.db


def _give_back_connection(_error=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()  # for a pooled connection, close() means "give it back"


# ---------------------------------------------------------------- running SQL

def _run(name, params, fetch):
    if name not in _queries:
        raise KeyError(f"No SQL statement called {name!r} in web/sql/")
    query = _queries[name]
    cursor = _connection().cursor(dictionary=True)
    start = time.perf_counter()
    try:
        cursor.execute(query["sql"], params or None)
        rows = cursor.fetchall() if fetch else []
        count, last_id = cursor.rowcount, cursor.lastrowid
    finally:
        cursor.close()
    # Remember what ran, for the "Under the hood" box at the bottom of every page.
    g.setdefault("sql_log", []).append({
        "name": name,
        "about": query["about"],
        "sql": query["sql"],
        "ms": (time.perf_counter() - start) * 1000,
        "rows": len(rows) if fetch else count,
        "fetch": fetch,
    })
    return rows, count, last_id


def all(name, **params):
    """Run a SELECT and return every row (a list of dicts)."""
    return _run(name, params, fetch=True)[0]


def one(name, **params):
    """Run a SELECT and return the first row, or None."""
    rows = _run(name, params, fetch=True)[0]
    return rows[0] if rows else None


def execute(name, **params):
    """Run an INSERT, UPDATE or DELETE. Returns (rows changed, new AUTO_INCREMENT id)."""
    _, count, last_id = _run(name, params, fetch=False)
    return count, last_id


@contextmanager
def transaction():
    """Run several statements as one unit: all of them are saved, or none."""
    conn = _connection()
    conn.start_transaction()
    try:
        yield
        conn.commit()
    except Exception:
        conn.rollback()
        raise


# ---------------------------------------------------------------- errors

def duplicate_key(err):
    """If err is 'Duplicate entry ... for key X', return X (like 'listener.uq_listener_email')."""
    if getattr(err, "errno", None) == errorcode.ER_DUP_ENTRY:
        match = re.search(r"for key '([^']+)'", str(err))
        return match.group(1) if match else "?"
    return None


def missing_parent(err):
    """True if err is a foreign key error: the row points at a parent that does not exist."""
    return getattr(err, "errno", None) == errorcode.ER_NO_REFERENCED_ROW_2
