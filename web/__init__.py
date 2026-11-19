"""music_db website: a Flask app on top of the music_db MySQL database.

Start it from the repo folder:   flask --app web run --port 5050
"""

import os
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlencode

from dotenv import load_dotenv
from flask import Flask, g, render_template, request, session

from . import db
from .security import check_csrf, csrf_token, here

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def create_app():
    load_dotenv(PROJECT_ROOT / ".env")

    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", ""),
        ADMIN_PASSWORD=os.environ.get("ADMIN_PASSWORD", ""),
        MYSQL_HOST=os.environ.get("MYSQL_HOST", "127.0.0.1"),
        MYSQL_PORT=int(os.environ.get("MYSQL_PORT", "3306")),
        MYSQL_USER=os.environ.get("MYSQL_USER", "music_app"),
        MYSQL_PASSWORD=os.environ.get("MYSQL_PASSWORD", ""),
        MYSQL_DATABASE=os.environ.get("MYSQL_DATABASE", "music_db"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    if not app.config["SECRET_KEY"]:
        raise RuntimeError(
            "SECRET_KEY is missing. Copy .env.example to .env and fill it in (see README.md)."
        )

    db.init_app(app)

    from . import account, admin, catalog, community, lab, library, reviews
    for module in (catalog, community, account, library, reviews, admin, lab):
        app.register_blueprint(module.bp)

    app.before_request(check_csrf)
    _add_template_helpers(app)
    _add_error_pages(app)
    return app


# ---------------------------------------------------------------- template helpers

def _add_template_helpers(app):

    @app.context_processor
    def page_globals():
        user = None
        if session.get("listener_id"):
            user = {"id": session["listener_id"], "username": session.get("username")}
        return {
            "current_user": user,
            "is_admin": bool(session.get("is_admin")),
            "csrf_token": csrf_token,
            "here": here,
            "url_with": url_with,
            "now_playing": _now_playing(),
        }

    def url_with(**changes):
        """This page's address with some filters changed: url_with(genre=3, page=None).
        None removes a filter. Used by the filter chips and the page numbers."""
        args = request.args.to_dict()
        for key, value in changes.items():
            if value is None or value == "":
                args.pop(key, None)
            else:
                args[key] = value
        return request.path + ("?" + urlencode(args) if args else "")

    @app.template_filter("duration")
    def duration(seconds):
        """215 -> '3:35'"""
        if seconds is None:
            return "-"
        minutes, secs = divmod(int(seconds), 60)
        return f"{minutes}:{secs:02d}"

    @app.template_filter("total_time")
    def total_time(seconds):
        """4980 -> '1 h 23 min'"""
        minutes = int(seconds or 0) // 60
        hours, minutes = divmod(minutes, 60)
        return f"{hours} h {minutes} min" if hours else f"{minutes} min"

    @app.template_filter("compact")
    def compact(number):
        """1847621533 -> '1.8B', 23400 -> '23.4K'"""
        number = int(number or 0)
        for limit, letter in ((1_000_000_000, "B"), (1_000_000, "M"), (1_000, "K")):
            if number >= limit:
                text = f"{number / limit:.1f}".rstrip("0").rstrip(".")
                return f"{text}{letter}"
        return str(number)

    @app.template_filter("thousands")
    def thousands(number):
        return f"{int(number or 0):,}"

    @app.template_filter("hue")
    def hue(item_id):
        """Every album and artist gets its own color, made from its id."""
        return (int(item_id or 0) * 47 + 200) % 360

    @app.template_filter("pattern")
    def pattern(item_id):
        return int(item_id or 0) % 4

    @app.template_filter("initials")
    def initials(name):
        words = [w for w in (name or "").split() if w[0].isalnum()]
        return "".join(w[0] for w in words[:2]).upper() or "♪"

    @app.template_filter("or_untitled")
    def or_untitled(name):
        return name if name else "Untitled"

    @app.template_filter("nice_date")
    def nice_date(value):
        """date(2026, 11, 9) -> 'Nov 9, 2026'"""
        if not isinstance(value, (date, datetime)):
            return value or ""
        return f"{value:%b} {value.day}, {value.year}"

    @app.template_filter("ago")
    def ago(value):
        """A date or time -> 'today', 'yesterday', '3 days ago', or 'Nov 9, 2026'."""
        if not isinstance(value, (date, datetime)):
            return value or ""
        day = value.date() if isinstance(value, datetime) else value
        days = (date.today() - day).days
        if days <= 0:
            return "today"
        if days == 1:
            return "yesterday"
        if days < 7:
            return f"{days} days ago"
        if days < 35:
            weeks = days // 7
            return f"{weeks} week{'s' if weeks > 1 else ''} ago"
        return nice_date(day)

    @app.template_filter("genre_list")
    def genre_list(packed):
        """'3:Pop|7:Rock' (from GROUP_CONCAT in SQL) -> [(3, 'Pop'), (7, 'Rock')]"""
        pairs = []
        for item in (packed or "").split("|"):
            if ":" in item:
                genre_id, name = item.split(":", 1)
                pairs.append((int(genre_id), name))
        return pairs

    @app.template_filter("plural")
    def plural(count, word):
        count = int(count or 0)
        return f"{count:,} {word}" + ("" if count == 1 else "s")


def _now_playing():
    """The song the listener pressed Play on last, for the bar at the bottom."""
    song_id = session.get("now_playing")
    if not song_id:
        return None
    if "now_playing" not in g:
        g.now_playing = db.one("library.now_playing", song_id=song_id)
    return g.now_playing


# ---------------------------------------------------------------- error pages

def _add_error_pages(app):
    messages = {
        400: ("Something was wrong with that request.", "Go back and try again."),
        404: ("We couldn't find that page.", "It may have moved, or it never existed."),
        500: ("Something broke on our side.", "Please try again in a moment."),
    }

    def show(error):
        code = getattr(error, "code", 500) or 500
        title, text = messages.get(code, messages[500])
        if code == 400 and getattr(error, "description", None):
            text = error.description
        return render_template("error.html", code=code, title=title, text=text), code

    for code in messages:
        app.register_error_handler(code, show)
