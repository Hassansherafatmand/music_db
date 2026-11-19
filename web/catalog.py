"""Pages everyone can see: home, artists, albums, genres and search."""

from flask import Blueprint, abort, g, render_template, request

from . import db
from .security import current_listener_id

bp = Blueprint("catalog", __name__)


def my_playlists():
    """The logged-in listener's playlists, for the "Add to playlist" menus."""
    listener_id = current_listener_id()
    if listener_id is None:
        return []
    if "my_playlists" not in g:
        g.my_playlists = db.all("library.playlist_names", listener_id=listener_id)
    return g.my_playlists


@bp.get("/")
def home():
    return render_template(
        "home.html",
        stats=db.one("catalog.site_stats"),
        most_played=db.all("catalog.most_played_songs"),
        newest=db.all("catalog.newest_albums"),
        top_rated=db.all("catalog.top_rated_albums"),
        genres=db.all("catalog.genres_with_counts"),
    )


@bp.get("/artists")
def artists():
    return render_template("artists.html", artists=db.all("catalog.all_artists"))


@bp.get("/artists/<int:artist_id>")
def artist(artist_id):
    found = db.one("catalog.artist_by_id", artist_id=artist_id)
    if found is None:
        abort(404)
    return render_template(
        "artist.html",
        artist=found,
        albums=db.all("catalog.albums_by_artist", artist_id=artist_id),
        popular=db.all("catalog.popular_songs_by_artist",
                       artist_id=artist_id, listener_id=current_listener_id()),
        playlists=my_playlists(),
    )


@bp.get("/albums/<int:album_id>")
def album(album_id):
    found = db.one("catalog.album_by_id", album_id=album_id)
    if found is None:
        abort(404)
    listener_id = current_listener_id()

    # Star bars: how many reviews gave 5, 4, 3, 2 and 1 stars.
    counts = {row["stars"]: row["reviews"]
              for row in db.all("reviews.star_counts", album_id=album_id)}
    star_bars = [(stars, counts.get(stars, 0)) for stars in (5, 4, 3, 2, 1)]

    return render_template(
        "album.html",
        album=found,
        tracks=db.all("catalog.album_tracks", album_id=album_id, listener_id=listener_id),
        reviews=db.all("reviews.album_reviews", album_id=album_id),
        star_bars=star_bars,
        most_stars=max(counts.values(), default=0),
        my_review=(db.one("reviews.my_review", listener_id=listener_id, album_id=album_id)
                   if listener_id else None),
        playlists=my_playlists(),
    )


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


@bp.get("/search")
def search():
    words = request.args.get("q", "").strip()
    results = None
    if len(words) >= 2:
        # In LIKE, % and _ are wildcards. A backslash makes a typed % or _ normal text.
        escaped = words.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped}%"
        results = {
            "songs": db.all("catalog.search_songs",
                            pattern=pattern, listener_id=current_listener_id()),
            "artists": db.all("catalog.search_artists", pattern=pattern),
            "albums": db.all("catalog.search_albums", pattern=pattern),
        }
    return render_template("search.html", words=words, results=results,
                           playlists=my_playlists())
