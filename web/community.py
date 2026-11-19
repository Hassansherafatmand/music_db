"""The listeners: the Listeners page, and each listener's public profile.

A profile shows what a listener loves, plays and writes. Their email is private and is
never shown here (only on their own "My account" page, and to the admin).
"""

from flask import Blueprint, abort, render_template

from . import db, lists
from .catalog import _page_or_first, my_playlists
from .security import current_listener_id

bp = Blueprint("community", __name__)

LISTENER_SORTS = {"favorites": "Most favorites (♥)", "plays": "Most plays (▶)",
                  "reviews": "Most reviews", "comments": "Most comments",
                  "newest": "Newest members", "name": "Username (A to Z)"}


@bp.get("/listeners")
def listeners():
    statement = "community.browse_listeners"
    genres = db.all("catalog.genre_choices")
    years = [row["joined_year"] for row in db.all("community.joined_year_choices")]
    chosen = {
        "genre": lists.number("genre", {r["genre_id"] for r in genres}),
        "joined": lists.number("joined", years),
    }
    sort, sort_options = lists.sort_choice(statement, LISTENER_SORTS, "favorites")
    where = [key for key in chosen if chosen[key] is not None]

    page = lists.page_number()
    rows, total = db.browse(statement, where=where, sort=sort, page=page, per_page=24, **chosen)
    fields = [
        lists.menu("genre", "Top genre", "Any taste",
                   [(r["genre_id"], r["genre_name"]) for r in genres], chosen["genre"]),
        lists.menu("joined", "Joined", "Any year", [(y, str(y)) for y in years],
                   chosen["joined"]),
    ]
    return _page_or_first(rows, page) or render_template(
        "listeners.html", listeners=rows, pages=lists.Pages(total, 24), fields=fields,
        sort=sort, sort_options=sort_options)


@bp.get("/listeners/<username>")
def profile(username):
    found = db.one("community.profile", username=username)
    if found is None:
        abort(404)
    them = found["listener_id"]
    me = current_listener_id()
    days = db.all("community.last_30_days", listener_id=them)
    return render_template(
        "listener.html",
        person=found,
        is_me=(me == them),
        genres=db.all("community.top_genres", listener_id=them),
        favorites=db.all("community.favorites", listener_id=them, me=me),
        top=db.all("library.my_top_songs", listener_id=them),
        reviews=db.all("community.reviews", listener_id=them),
        comments=db.all("community.comments", listener_id=them),
        days=days,
        busiest_day=max((d["plays"] for d in days), default=0),
        both_love=(db.all("community.songs_we_both_love", me=me, listener_id=them)
                   if me and me != them else None),
        playlists=my_playlists(),
    )
