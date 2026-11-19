"""What belongs to a listener: favorites (♥), plays (▶), playlists and top songs."""

from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

from . import db
from .security import back, current_listener_id, login_required

bp = Blueprint("library", __name__)

WEEKDAYS = [(2, "Mon"), (3, "Tue"), (4, "Wed"), (5, "Thu"), (6, "Fri"), (7, "Sat"), (1, "Sun")]


# ---------------------------------------------------------------- ♥ and ▶

@bp.post("/songs/<int:song_id>/favorite")
@login_required
def toggle_favorite(song_id):
    me = current_listener_id()
    removed, _ = db.execute("library.remove_favorite", listener_id=me, song_id=song_id)
    if removed:
        flash("Removed from your favorites.", "info")
    else:
        try:
            db.execute("library.add_favorite", listener_id=me, song_id=song_id)
        except db.IntegrityError as err:
            if db.missing_parent(err):  # the foreign key: no such song
                abort(404)
            raise
        flash("Added to your favorites ♥", "success")
    return back()


@bp.post("/songs/<int:song_id>/play")
@login_required
def play(song_id):
    try:
        db.execute("library.record_play", listener_id=current_listener_id(), song_id=song_id)
    except db.IntegrityError as err:
        if db.missing_parent(err):
            abort(404)
        raise
    session["now_playing"] = song_id
    return back()


@bp.get("/me/favorites")
@login_required
def favorites():
    from .catalog import my_playlists
    return render_template(
        "favorites.html",
        songs=db.all("library.favorites_of_listener", listener_id=current_listener_id()),
        playlists=my_playlists(),
    )


# ---------------------------------------------------------------- playlists

def _owned_playlist(playlist_id):
    """The playlist, if it is mine. Other people's playlists are private (404)."""
    found = db.one("library.playlist_of_owner",
                   playlist_id=playlist_id, listener_id=current_listener_id())
    if found is None:
        abort(404)
    return found


def _lock(playlist_id):
    """Inside a transaction: lock my playlist's row (SELECT ... FOR UPDATE).
    Another browser that changes the same playlist now waits until we are finished."""
    if db.one("library.lock_my_playlist", playlist_id=playlist_id,
              listener_id=current_listener_id()) is None:
        abort(404)


def _clean_name(raw):
    name = " ".join((raw or "").split())  # no extra spaces
    if not 1 <= len(name) <= 50:
        flash("A playlist name needs 1 to 50 characters.", "error")
        return None
    return name


@bp.get("/me/playlists")
@login_required
def playlists():
    rows = db.all("library.playlists_of_listener", listener_id=current_listener_id())
    for row in rows:
        # The first 4 different albums, for the 4-cover picture.
        ids = []
        for album_id in (row["album_ids"] or "").split(","):
            if album_id and int(album_id) not in ids:
                ids.append(int(album_id))
        row["covers"] = ids[:4]
    return render_template("playlists.html", playlists=rows)


@bp.post("/me/playlists")
@login_required
def create_playlist():
    name = _clean_name(request.form.get("playlist_name"))
    if name is None:
        return redirect(url_for("library.playlists"))
    try:
        _, playlist_id = db.execute("library.create_playlist",
                                    listener_id=current_listener_id(), playlist_name=name)
    except db.IntegrityError as err:
        if db.duplicate_key(err):
            flash(f'You already have a playlist called "{name}".', "error")
            return redirect(url_for("library.playlists"))
        raise
    flash(f'Playlist "{name}" is ready. Add songs from any album page.', "success")
    return redirect(url_for("library.playlist", playlist_id=playlist_id))


@bp.get("/playlists/<int:playlist_id>")
@login_required
def playlist(playlist_id):
    found = _owned_playlist(playlist_id)
    tracks = db.all("library.playlist_tracks",
                    playlist_id=playlist_id, listener_id=current_listener_id())
    covers = []
    for track in tracks:
        if track["album_id"] not in covers:
            covers.append(track["album_id"])
    return render_template(
        "playlist.html",
        playlist=found,
        tracks=tracks,
        covers=covers[:4],
        seconds=sum(t["duration_seconds"] or 0 for t in tracks),
    )


@bp.post("/playlists/<int:playlist_id>/add")
@login_required
def add_to_playlist(playlist_id):
    found = _owned_playlist(playlist_id)
    song_id = request.form.get("song_id", type=int)
    try:
        with db.transaction():
            _lock(playlist_id)  # so two browsers can't take the same next position
            position = db.one("library.next_position", playlist_id=playlist_id)["next_position"]
            db.execute("library.add_to_playlist",
                       playlist_id=playlist_id, song_id=song_id, position=position)
    except db.IntegrityError as err:
        if db.duplicate_key(err):
            flash(f'That song is already in "{found["playlist_name"]}".', "info")
            return back()
        if db.missing_parent(err):
            abort(404)
        raise
    flash(f'Added to "{found["playlist_name"]}".', "success")
    return back()


@bp.post("/playlists/<int:playlist_id>/songs/<int:song_id>/remove")
@login_required
def remove_from_playlist(playlist_id, song_id):
    with db.transaction():
        _lock(playlist_id)
        row = db.one("library.position_of_song", playlist_id=playlist_id, song_id=song_id)
        if row:
            db.execute("library.remove_from_playlist", playlist_id=playlist_id, song_id=song_id)
            db.execute("library.close_gap", playlist_id=playlist_id, position=row["position"])
    flash("Removed from the playlist.", "info")
    return back()


@bp.post("/playlists/<int:playlist_id>/songs/<int:song_id>/move")
@login_required
def move_in_playlist(playlist_id, song_id):
    step = -1 if request.form.get("direction") == "up" else 1
    with db.transaction():
        _lock(playlist_id)
        row = db.one("library.position_of_song", playlist_id=playlist_id, song_id=song_id)
        if row:
            here_pos = row["position"]
            other = db.one("library.song_at_position",
                           playlist_id=playlist_id, position=here_pos + step)
            if other:
                # Swap the two songs. UNIQUE (playlist_id, position) refuses two songs in
                # one place, so this song waits at a free place (after the last) first.
                free = db.one("library.next_position", playlist_id=playlist_id)["next_position"]
                db.execute("library.set_position", playlist_id=playlist_id,
                           song_id=song_id, position=free)
                db.execute("library.set_position", playlist_id=playlist_id,
                           song_id=other["song_id"], position=here_pos)
                db.execute("library.set_position", playlist_id=playlist_id,
                           song_id=song_id, position=other["position"])
    return back()


@bp.post("/playlists/<int:playlist_id>/rename")
@login_required
def rename_playlist(playlist_id):
    _owned_playlist(playlist_id)
    name = _clean_name(request.form.get("playlist_name"))
    if name:
        try:
            db.execute("library.rename_playlist", playlist_id=playlist_id,
                       listener_id=current_listener_id(), playlist_name=name)
            flash(f'Renamed to "{name}".', "success")
        except db.IntegrityError as err:
            if not db.duplicate_key(err):
                raise
            flash(f'You already have a playlist called "{name}".', "error")
    return redirect(url_for("library.playlist", playlist_id=playlist_id))


@bp.post("/playlists/<int:playlist_id>/delete")
@login_required
def delete_playlist(playlist_id):
    found = _owned_playlist(playlist_id)
    db.execute("library.delete_playlist",
               playlist_id=playlist_id, listener_id=current_listener_id())
    flash(f'Deleted "{found["playlist_name"]}".', "info")
    return redirect(url_for("library.playlists"))


# ---------------------------------------------------------------- my top songs

@bp.get("/me/top")
@login_required
def top_songs():
    me = current_listener_id()
    by_day = {row["weekday"]: row["plays"]
              for row in db.all("library.my_plays_by_weekday", listener_id=me)}
    weekdays = [(label, by_day.get(number, 0)) for number, label in WEEKDAYS]
    latest_day = db.all("library.my_latest_day", listener_id=me)
    return render_template(
        "top.html",
        stats=db.one("library.my_stats", listener_id=me),
        top=db.all("library.my_top_songs", listener_id=me),
        genres=db.all("library.my_top_genres", listener_id=me),
        weekdays=weekdays,
        busiest=max((plays for _, plays in weekdays), default=0),
        latest_day=latest_day,
        recent=db.all("library.my_recent_plays", listener_id=me),
    )
