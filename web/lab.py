"""The Lab: pages that show how the website and the database work together.

  /lab               the start page
  /lab/security      SQL injection, the ORDER BY list, password hashes, CSRF, MySQL rights
  /lab/speed         indexes: the same question with and without an index, with EXPLAIN
  /lab/two-browsers  two browsers, two logins, one server and one database
"""

import hashlib
import re
from datetime import date

from flask import Blueprint, g, render_template, request, session
from werkzeug.security import generate_password_hash

from . import db
from .catalog import SONG_SORTS
from .security import csrf_token, current_listener_id

bp = Blueprint("lab", __name__, url_prefix="/lab")

ATTACK = "' OR '1'='1' -- "


@bp.get("/")
def index():
    return render_template("lab/index.html")


# ---------------------------------------------------------------- security

@bp.get("/security")
def security():
    typed = request.args.get("username", ATTACK)[:80]
    # How a CARELESS website would build the SQL: by gluing the typed text into it.
    # This text is only SHOWN on the page. It is never sent to MySQL.
    glued = f"SELECT listener_id, username\nFROM listener\nWHERE username = '{typed}';"
    # How music_db really does it: the typed text is a parameter.
    found = db.all("lab.safe_login_lookup", username=typed)
    demo = db.one("lab.demo_hash", username="sunny_cactus40")
    return render_template(
        "lab/security.html",
        typed=typed, glued=glued, found=found, attack=ATTACK,
        safe_sql=db.sql_text("lab.safe_login_lookup"),
        sorts=list(SONG_SORTS),
        demo=demo,
        fresh_hashes=[generate_password_hash("music330") for _ in range(2)],
        grants=[list(row.values())[0] for row in db.all("lab.my_grants")],
        token_start=csrf_token()[:8],
    )


# ---------------------------------------------------------------- speed

def _timed(name, **params):
    """Run a statement and EXPLAIN it. Returns what the page shows about it."""
    rows = db.all(name, **params)
    ms = g.sql_log[-1]["ms"]  # how long it took (the statement that just ran)
    plan = db.explain(name, **params)
    return {"name": name, "sql": db.sql_text(name), "about": db.about(name), "rows": rows,
            "plan": plan, "ms": ms}


@bp.get("/speed")
def speed():
    word = request.args.get("word", "gold").strip().lower()
    if not re.fullmatch(r"[a-z0-9]{3,20}", word):
        word = "gold"
    day = request.args.get("day", "2026-11-09")
    try:
        day = date.fromisoformat(day).isoformat()
    except ValueError:
        day = "2026-11-09"
    names = [
        _timed("lab.names_starting", starts=f"{word}%"),
        _timed("lab.names_containing", contains=f"%{word}%"),
        _timed("lab.names_fulltext", words=f"+{word}*"),
    ]
    plays = [
        _timed("lab.plays_range", day=day),
        _timed("lab.plays_function", day=day),
        _timed("lab.plays_no_index", day=day),
    ]
    return render_template("lab/speed.html", word=word, day=day, names=names, plays=plays)


# ---------------------------------------------------------------- two browsers

def _browser_name(agent):
    agent = agent or ""
    for name, mark in (("Edge", "Edg/"), ("Opera", "OPR/"), ("Firefox", "Firefox/"),
                       ("Chrome", "Chrome/"), ("Safari", "Safari/")):
        if mark in agent:
            return name
    return "a browser"


@bp.get("/two-browsers")
def two_browsers():
    top = db.all("catalog.most_loved_songs")
    song = dict(top[0]) if top else None
    if song:
        song["is_favorite"] = bool(db.one("library.is_favorite", song_id=song["song_id"],
                                          listener_id=current_listener_id()))
    return render_template(
        "lab/two_browsers.html",
        browser=_browser_name(request.headers.get("User-Agent")),
        # A short "name" for this browser's session: made from its secret token,
        # so it is different in every browser, but the token itself stays secret.
        session_name=hashlib.sha256(csrf_token().encode()).hexdigest()[:6].upper(),
        live=db.one("lab.live_numbers"),
        song=song,
        username=session.get("username"),
    )
