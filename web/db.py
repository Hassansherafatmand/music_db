"""The database part of the website: a pool of MySQL connections, and the SQL files.

Every SQL statement the website runs lives in a .sql file in web/sql/, under a name:

    -- name: album_by_id
    -- One album, with its artist.
    SELECT ... FROM album WHERE album_id = %(album_id)s;

The Python code runs it by its name:  db.one("catalog.album_by_id", album_id=5)

%(album_id)s is a parameter. The driver sends the value separately from the SQL text,
so what a user types can never change the SQL (no SQL injection). It is the same idea
as the "?" from class, written the way the Python MySQL driver writes it.

List pages with filters and sorts (Songs, Albums, Artists, Listeners) use pieces that
are written in the same .sql file, right after their statement:

    -- where: state
    ar.origin_state = %(state)s
    -- sort: name
    ar.artist_name, ar.artist_id

The statement has places for them: {where}, {and_where}, {having} and {order}.
The visitor only chooses a piece by its name (like ?sort=name). A name that is not in
the file is not used, so a visitor can never put their own SQL into the statement.
The values (like the state) are still parameters.
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
_MARKER = re.compile(r"--\s*(name|where|having|sort):\s*(\w+)\s*$")
_PARAM = re.compile(r"%\((\w+)\)s")
_SECRET = ("password", "hash")  # parameters with these words are never shown on a page

_queries = {}  # "catalog.album_by_id" -> {"sql", "about", "pieces"}
_pool = None


# ---------------------------------------------------------------- the SQL files

def load_queries():
    """Read every web/sql/*.sql file: each named statement, and its filter/sort pieces."""
    _queries.clear()
    for path in sorted(_SQL_DIR.glob("*.sql")):
        block, statement = None, None
        for line in path.read_text(encoding="utf-8").splitlines() + ["-- name: _end"]:
            match = _MARKER.match(line.strip())
            if not match:
                if block:
                    block[2].append(line)
                continue
            if block:  # the block before this marker is finished
                kind, name, lines = block
                if kind == "name":
                    statement = _remember(path.stem, name, lines)
                elif statement is not None:
                    statement["pieces"][kind][name] = _without_comments(lines)
            block = (match.group(1), match.group(2), [])


def _without_comments(lines):
    # Comments are notes for people, so they are not sent to MySQL.
    return "\n".join(l for l in lines if not l.strip().startswith("--")).strip()


def _remember(file_stem, name, lines):
    # The comment lines right under "-- name:" describe the statement. They are shown
    # on the page ("Under the hood").
    about = []
    for line in lines:
        if not line.strip().startswith("--"):
            break
        about.append(line.strip()[2:].strip())
    statement = {"sql": _without_comments(lines).rstrip(";").strip(), "about": " ".join(about),
                 "pieces": {"where": {}, "having": {}, "sort": {}}}
    _queries[f"{file_stem}.{name}"] = statement
    return statement


def sql_text(name):
    """The SQL of a named statement, to show it on a page (the Charts, Reports and Lab)."""
    return _queries[name]["sql"]


def about(name):
    """The description of a named statement (the comment lines under its name)."""
    return _queries[name]["about"]


def pieces(name, kind):
    """The names of a statement's filter or sort pieces, like ['name', 'state']."""
    return list(_queries[name]["pieces"][kind])


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
    """This page's connection. If all connections in the pool are busy (many pages at the
    same moment), wait a little for one to come back, like waiting in a line."""
    if "db" not in g:
        deadline = time.monotonic() + 10
        while True:
            try:
                g.db = _pool.get_connection()
                break
            except mysql.connector.errors.PoolError:
                if time.monotonic() > deadline:
                    raise
                time.sleep(0.02)
    return g.db


def _give_back_connection(_error=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()  # for a pooled connection, close() means "give it back"


# ---------------------------------------------------------------- running SQL

def _run(name, params, fetch, sql=None, label=None):
    if name not in _queries:
        raise KeyError(f"No SQL statement called {name!r} in web/sql/")
    query = _queries[name]
    sql = sql or query["sql"]
    cursor = _connection().cursor(dictionary=True)
    start = time.perf_counter()
    try:
        cursor.execute(sql, params or None)
        rows = cursor.fetchall() if fetch else []
        count, last_id = cursor.rowcount, cursor.lastrowid
    finally:
        cursor.close()
    # Remember what ran, for the "Under the hood" box at the bottom of every page.
    used = dict.fromkeys(_PARAM.findall(sql))
    g.setdefault("sql_log", []).append({
        "name": label or name,
        "about": query["about"],
        "sql": sql,
        "params": {key: ("(hidden)" if any(word in key for word in _SECRET) else params.get(key))
                   for key in used} if params else {},
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


def explain(name, **params):
    """EXPLAIN a SELECT: how MySQL will find the rows (which index, how many rows).
    FORMAT=TRADITIONAL asks for the classic table (MySQL 9 shows a "tree" by default)."""
    sql = "EXPLAIN FORMAT=TRADITIONAL " + _queries[name]["sql"]
    return _run(name, params, fetch=True, sql=sql, label=f"EXPLAIN {name}")[0]


def build(name, where=(), having=(), sort=None):
    """Put the chosen filter and sort pieces into a statement. Returns the SQL text.

    where, having: names of pieces (only names from the .sql file are allowed).
    sort: the name of a sort piece."""
    query = _queries[name]
    found = query["pieces"]
    conditions = [found["where"][key] for key in where]
    groups = [found["having"][key] for key in having]
    sql = query["sql"]
    sql = sql.replace("{where}", "WHERE " + "\n  AND ".join(conditions) if conditions else "")
    sql = sql.replace("{and_where}", "".join(f"\n  AND {c}" for c in conditions))
    sql = sql.replace("{having}", "HAVING " + "\n   AND ".join(groups) if groups else "")
    sql = sql.replace("{order}", found["sort"][sort])
    return "\n".join(line for line in sql.splitlines() if line.strip())  # no empty lines


def browse(name, where=(), having=(), sort=None, page=1, per_page=24, **params):
    """A list page: the rows of one page, and the total number of rows.

    The statement counts all rows with COUNT(*) OVER () (a window function), so one
    query gives both the page and the total."""
    sql = build(name, where, having, sort)
    params.update(limit=per_page, offset=(page - 1) * per_page)
    rows = _run(name, params, fetch=True, sql=sql)[0]
    total = rows[0]["total_rows"] if rows else 0
    return rows, total


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


def still_used(err):
    """If err is 'Cannot delete a parent row' (a foreign key with RESTRICT said no),
    return the name of that foreign key (like 'fk_favorite_song'). Else None."""
    if getattr(err, "errno", None) == errorcode.ER_ROW_IS_REFERENCED_2:
        match = re.search(r"CONSTRAINT `([^`]+)`", str(err))
        return match.group(1) if match else "?"
    return None
