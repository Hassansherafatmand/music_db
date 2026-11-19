"""Pages everyone can see: home, songs, albums, artists, genres, charts and search."""

import re
from collections import defaultdict
from urllib.parse import urlencode

from flask import Blueprint, abort, g, redirect, render_template, request, session

from . import db, lists
from .security import current_listener_id

bp = Blueprint("catalog", __name__)

# MySQL's FULLTEXT search skips words shorter than 3 letters and very common words
# (its "stopword" list), so the search leaves them out too.
STOPWORDS = {"about", "are", "com", "for", "from", "how", "that", "the", "this", "was",
             "what", "when", "where", "who", "will", "with", "und", "www"}


def my_playlists():
    """The logged-in listener's playlists, for the "Add to playlist" menus."""
    listener_id = current_listener_id()
    if listener_id is None:
        return []
    if "my_playlists" not in g:
        g.my_playlists = db.all("library.playlist_names", listener_id=listener_id)
    return g.my_playlists


def _page_or_first(rows, page):
    """A page number after the last page shows nothing: go back to page 1."""
    if not rows and page > 1:
        args = request.args.to_dict()
        args.pop("page", None)
        return redirect(request.path + ("?" + urlencode(args) if args else ""))
    return None


# ---------------------------------------------------------------- home

@bp.get("/")
def home():
    return render_template(
        "home.html",
        stats=db.one("catalog.site_stats"),
        most_played=db.all("catalog.most_played_songs"),
        most_loved=db.all("catalog.most_loved_songs"),
        loved_albums=db.all("catalog.most_loved_albums"),
        newest=db.all("catalog.newest_albums"),
        top_rated=db.all("catalog.top_rated_albums"),
        feed=db.all("catalog.whats_new"),
        genres=db.all("catalog.genres_with_counts"),
    )


# ---------------------------------------------------------------- songs

SONG_SORTS = {"loved": "Most loved (♥)", "played": "Most played (▶)",
              "streams": "Most streams", "newest": "Newest albums first",
              "name": "Name (A to Z)", "length": "Longest first"}
LENGTHS = {"short": "Short (under 3:00)", "medium": "Medium (3:00 to 5:00)",
           "long": "Long (over 5:00)"}


@bp.get("/songs")
def songs():
    statement = "catalog.browse_songs"
    genres = db.all("catalog.genre_choices")
    artists = db.all("catalog.artist_choices")
    states = [row["origin_state"] for row in db.all("catalog.state_choices")]
    decades = [int(row["decade"]) for row in db.all("catalog.decade_choices")]

    chosen = {
        "genre": lists.number("genre", {r["genre_id"] for r in genres}),
        "artist": lists.number("artist", {r["artist_id"] for r in artists}),
        "state": lists.choice("state", states),
        "decade": lists.number("decade", decades),
        "length": lists.choice("length", LENGTHS),
    }
    sort, sort_options = lists.sort_choice(statement, SONG_SORTS, "loved")
    where = [key for key in ("genre", "artist", "state", "decade") if chosen[key] is not None]
    if chosen["length"]:
        where.append(chosen["length"])  # the piece is called short, medium or long

    page = lists.page_number()
    rows, total = db.browse(statement, where=where, sort=sort, page=page, per_page=25,
                            listener_id=current_listener_id(),
                            **{k: v for k, v in chosen.items() if k != "length"})
    fields = [
        lists.menu("genre", "Genre", "All genres",
                   [(r["genre_id"], r["genre_name"]) for r in genres], chosen["genre"]),
        lists.menu("artist", "Artist", "All artists",
                   [(r["artist_id"], r["artist_name"]) for r in artists], chosen["artist"]),
        lists.menu("state", "Artist's state", "All states", [(x, x) for x in states],
                   chosen["state"]),
        lists.menu("decade", "Album year", "All years", [(d, f"{d}s") for d in decades],
                   chosen["decade"]),
        lists.menu("length", "Length", "Any length", LENGTHS.items(), chosen["length"]),
    ]
    return _page_or_first(rows, page) or render_template(
        "songs.html", songs=rows, pages=lists.Pages(total, 25), fields=fields, sort=sort,
        sort_options=sort_options, playlists=my_playlists())


# ---------------------------------------------------------------- albums

ALBUM_SORTS = {"rated": "Best rated (★)", "reviews": "Most reviews", "loved": "Most loved (♥)",
               "newest": "Newest first", "name": "Name (A to Z)"}


@bp.get("/albums")
def albums():
    statement = "catalog.browse_albums"
    genres = db.all("catalog.genre_choices")
    states = [row["origin_state"] for row in db.all("catalog.state_choices")]
    decades = [int(row["decade"]) for row in db.all("catalog.decade_choices")]
    chosen = {
        "genre": lists.number("genre", {r["genre_id"] for r in genres}),
        "decade": lists.number("decade", decades),
        "state": lists.choice("state", states),
        "stars": lists.number("stars", {2, 3, 4}),
    }
    sort, sort_options = lists.sort_choice(statement, ALBUM_SORTS, "rated")
    where = [key for key in ("genre", "decade", "state") if chosen[key] is not None]
    having = ["stars"] if chosen["stars"] else []

    page = lists.page_number()
    rows, total = db.browse(statement, where=where, having=having, sort=sort, page=page,
                            per_page=24, **chosen)
    fields = [
        lists.menu("genre", "Genre", "All genres",
                   [(r["genre_id"], r["genre_name"]) for r in genres], chosen["genre"]),
        lists.menu("decade", "Year", "All years", [(d, f"{d}s") for d in decades],
                   chosen["decade"]),
        lists.menu("state", "Artist's state", "All states", [(x, x) for x in states],
                   chosen["state"]),
        lists.menu("stars", "Stars", "Any rating",
                   [(n, f"{n}★ or more") for n in (4, 3, 2)], chosen["stars"]),
    ]
    return _page_or_first(rows, page) or render_template(
        "albums.html", albums=rows, pages=lists.Pages(total, 24), fields=fields, sort=sort,
        sort_options=sort_options)


# ---------------------------------------------------------------- artists

ARTIST_SORTS = {"name": "Name (A to Z)", "fans": "Most fans (♥)", "albums": "Most albums",
                "streams": "Most streams", "state": "State", "debut": "Debut year"}


@bp.get("/artists")
def artists():
    statement = "catalog.browse_artists"
    states = [row["origin_state"] for row in db.all("catalog.state_choices")]
    decades = list(range(1950, 2030, 10))
    chosen = {
        "state": lists.choice("state", states),
        "decade": lists.number("decade", decades),
    }
    sort, sort_options = lists.sort_choice(statement, ARTIST_SORTS, "name")
    where = [key for key in chosen if chosen[key] is not None]

    page = lists.page_number()
    rows, total = db.browse(statement, where=where, sort=sort, page=page, per_page=24, **chosen)
    fields = [
        lists.menu("state", "State", "All states", [(x, x) for x in states], chosen["state"]),
        lists.menu("decade", "Debut", "Any year", [(d, f"{d}s") for d in decades],
                   chosen["decade"]),
    ]
    return _page_or_first(rows, page) or render_template(
        "artists.html", artists=rows, pages=lists.Pages(total, 24), fields=fields, sort=sort,
        sort_options=sort_options)


@bp.get("/artists/<int:artist_id>")
def artist(artist_id):
    found = db.one("catalog.artist_by_id", artist_id=artist_id)
    if found is None:
        abort(404)
    return render_template(
        "artist.html",
        artist=found,
        # Visitors see finished albums (3+ songs); the admin sees all of them.
        albums=db.all("catalog.albums_by_artist", artist_id=artist_id,
                      min_songs=0 if session.get("is_admin") else 3),
        popular=db.all("catalog.popular_songs_by_artist",
                       artist_id=artist_id, listener_id=current_listener_id()),
        playlists=my_playlists(),
    )


# ---------------------------------------------------------------- one album

@bp.get("/albums/<int:album_id>")
def album(album_id):
    found = db.one("catalog.album_by_id", album_id=album_id)
    if found is None:
        abort(404)
    # An album with fewer than 3 songs is not finished: only the admin can see it.
    if found["song_count"] < 3 and not session.get("is_admin"):
        abort(404)
    listener_id = current_listener_id()

    # Star bars: how many reviews gave 5, 4, 3, 2 and 1 stars.
    counts = {row["stars"]: row["reviews"]
              for row in db.all("reviews.star_counts", album_id=album_id)}
    star_bars = [(stars, counts.get(stars, 0)) for stars in (5, 4, 3, 2, 1)]

    # Each comment goes under its review: (reviewer_id) -> [comments].
    comments = defaultdict(list)
    for c in db.all("reviews.album_comments", album_id=album_id):
        comments[c["reviewer_id"]].append(c)

    return render_template(
        "album.html",
        album=found,
        tracks=db.all("catalog.album_tracks", album_id=album_id, listener_id=listener_id),
        reviews=db.all("reviews.album_reviews", album_id=album_id),
        comments=comments,
        lovers=db.all("catalog.album_lovers", album_id=album_id),
        star_bars=star_bars,
        most_stars=max(counts.values(), default=0),
        my_review=(db.one("reviews.my_review", listener_id=listener_id, album_id=album_id)
                   if listener_id else None),
        playlists=my_playlists(),
    )


# ---------------------------------------------------------------- genres

@bp.get("/genres")
def genres():
    return render_template("genres.html", genres=db.all("catalog.genres_with_counts"))


@bp.get("/genres/<int:genre_id>")
def genre(genre_id):
    found = db.one("catalog.genre_by_id", genre_id=genre_id)
    if found is None:
        abort(404)
    return render_template(
        "genre.html",
        genre=found,
        songs=db.all("catalog.songs_in_genre",
                     genre_id=genre_id, listener_id=current_listener_id()),
        playlists=my_playlists(),
    )


# ---------------------------------------------------------------- charts

@bp.get("/charts")
def charts():
    per_genre = defaultdict(list)
    for row in db.all("charts.top_songs_per_genre"):
        per_genre[(row["genre_id"], row["genre_name"])].append(row)
    days = db.all("charts.plays_per_day")
    return render_template(
        "charts.html",
        per_genre=per_genre,
        decades=db.all("charts.best_album_per_decade"),
        days=days,
        busiest_day=max((d["plays"] for d in days), default=0),
        shares=db.all("charts.genre_share"),
        sql={name: db.sql_text(f"charts.{name}") for name in
             ("top_songs_per_genre", "best_album_per_decade", "plays_per_day", "genre_share")},
    )


# ---------------------------------------------------------------- search

def fulltext_words(text):
    """'golden train' -> '+golden* +train*' (every word must be there, * = starts with).
    Only letters and digits are kept, so the visitor can't use FULLTEXT operators."""
    words = [w for w in re.findall(r"[A-Za-z0-9]+", text.lower())
             if len(w) >= 3 and w not in STOPWORDS]
    return " ".join(f"+{w}*" for w in words)


@bp.get("/search")
def search():
    text = request.args.get("q", "").strip()[:100]
    results, method = None, None
    me = current_listener_id()
    if len(text) >= 2:
        words = fulltext_words(text)
        if words:
            method = "fulltext"
            results = {
                "songs": db.all("catalog.search_songs", words=words, listener_id=me),
                "artists": db.all("catalog.search_artists", words=words),
                "albums": db.all("catalog.search_albums", words=words),
            }
        if not words or not any(results.values()):
            # In LIKE, % and _ are wildcards. A backslash makes a typed % or _ normal text.
            method = "like"
            escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            pattern = f"%{escaped}%"
            results = {
                "songs": db.all("catalog.search_songs_like", pattern=pattern, listener_id=me),
                "artists": db.all("catalog.search_artists_like", pattern=pattern),
                "albums": db.all("catalog.search_albums_like", pattern=pattern),
            }
    return render_template("search.html", words=text, results=results, method=method,
                           playlists=my_playlists())
