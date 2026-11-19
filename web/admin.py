"""The admin page: add artists, albums and songs, and set a song's genres.

It is protected by one password, ADMIN_PASSWORD in the private .env file.
"""

import re
import secrets
from datetime import date

from flask import (Blueprint, abort, current_app, flash, redirect, render_template,
                   request, session, url_for)

from . import db
from .security import admin_required, safe_next

bp = Blueprint("admin", __name__, url_prefix="/admin")


# ---------------------------------------------------------------- log in / out

@bp.route("/login", methods=["GET", "POST"])
def login():
    password = current_app.config["ADMIN_PASSWORD"]
    error = None
    if request.method == "POST":
        typed = request.form.get("password", "")
        if password and secrets.compare_digest(typed, password):
            session["is_admin"] = True
            flash("Admin mode is on.", "success")
            return redirect(safe_next(request.args.get("next"), url_for("admin.dashboard")))
        error = "That is not the admin password."
    return render_template("admin/login.html", error=error, disabled=not password)


@bp.post("/logout")
def logout():
    session.pop("is_admin", None)
    flash("Admin mode is off.", "info")
    return redirect(url_for("catalog.home"))


# ---------------------------------------------------------------- the dashboard

@bp.get("/")
@admin_required
def dashboard():
    return render_template(
        "admin/dashboard.html",
        stats=db.one("catalog.site_stats"),
        artists=db.all("admin.artist_choices"),
        albums=db.all("admin.album_choices"),
        genres=db.all("admin.genre_choices"),
        newest=db.all("admin.newest_songs"),
        this_year=date.today().year,
    )


def _year(raw, label):
    year = int(raw) if (raw or "").strip().isdigit() else None
    if year is None or not 1900 <= year <= date.today().year + 1:
        flash(f"{label}: please type a year like 2024.", "error")
        return None
    return year


def _seconds(raw):
    """'3:45' or '225' -> 225 seconds."""
    raw = (raw or "").strip()
    match = re.fullmatch(r"(\d{1,2}):([0-5]\d)", raw)
    if match:
        seconds = int(match.group(1)) * 60 + int(match.group(2))
    elif raw.isdigit():
        seconds = int(raw)
    else:
        return None
    return seconds if 1 <= seconds <= 3600 else None


@bp.post("/artists")
@admin_required
def add_artist():
    name = " ".join(request.form.get("artist_name", "").split())[:100]
    state = request.form.get("origin_state", "").strip().upper() or None
    year = _year(request.form.get("debut_year"), "Debut year")
    if not name:
        flash("The artist needs a name.", "error")
    elif state and not re.fullmatch(r"[A-Z]{2}", state):
        flash("State: two letters, like WA (or leave it empty).", "error")
    elif year:
        _, artist_id = db.execute("admin.add_artist",
                                  artist_name=name, origin_state=state, debut_year=year)
        flash(f'Added the artist "{name}".', "success")
        return redirect(url_for("catalog.artist", artist_id=artist_id))
    return redirect(url_for("admin.dashboard") + "#add-artist")


@bp.post("/albums")
@admin_required
def add_album():
    name = " ".join(request.form.get("album_name", "").split())[:100]
    artist_id = request.form.get("artist_id", type=int)
    year = _year(request.form.get("release_year"), "Release year")
    if not name:
        flash("The album needs a name.", "error")
    elif artist_id is None:
        flash("Please choose the artist.", "error")
    elif year:
        try:
            _, album_id = db.execute("admin.add_album",
                                     album_name=name, release_year=year, artist_id=artist_id)
        except db.IntegrityError as err:
            if db.missing_parent(err):
                flash("That artist does not exist.", "error")
                return redirect(url_for("admin.dashboard") + "#add-album")
            raise
        flash(f'Added the album "{name}". Now add its songs.', "success")
        return redirect(url_for("catalog.album", album_id=album_id))
    return redirect(url_for("admin.dashboard") + "#add-album")


@bp.post("/songs")
@admin_required
def add_song():
    name = " ".join(request.form.get("song_name", "").split())[:100]
    album_id = request.form.get("album_id", type=int)
    track = request.form.get("track_number", type=int)
    seconds = _seconds(request.form.get("duration"))
    genre_ids = sorted({int(g) for g in request.form.getlist("genre_ids") if g.isdigit()})

    if not name:
        flash("The song needs a name.", "error")
    elif album_id is None:
        flash("Please choose the album.", "error")
    elif track is None or track < 1:
        flash("The track number must be 1 or more.", "error")
    elif seconds is None:
        flash('Length: type it like 3:45 (or in seconds, like 225).', "error")
    elif not genre_ids:
        flash("Please choose at least one genre.", "error")
    else:
        try:
            # One transaction: the song and its genres are saved together, or not at all.
            with db.transaction():
                _, song_id = db.execute("admin.add_song", song_name=name,
                                        duration_seconds=seconds, track_number=track,
                                        album_id=album_id)
                for genre_id in genre_ids:
                    db.execute("admin.add_song_genre", song_id=song_id, genre_id=genre_id)
        except db.IntegrityError as err:
            if db.duplicate_key(err):  # UNIQUE (album_id, track_number)
                flash(f"That album already has a track {track}.", "error")
            elif db.missing_parent(err):
                flash("That album or genre does not exist.", "error")
            else:
                raise
        else:
            flash(f'Added the song "{name}".', "success")
            return redirect(url_for("catalog.album", album_id=album_id) + f"#song-{song_id}")
    return redirect(url_for("admin.dashboard") + "#add-song")


# ---------------------------------------------------------------- a song's genres

@bp.get("/songs/find")
@admin_required
def find_song():
    song_id = request.args.get("song_id", type=int)
    if song_id is None or db.one("admin.song_for_admin", song_id=song_id) is None:
        flash("There is no song with that number.", "error")
        return redirect(url_for("admin.dashboard") + "#set-genres")
    return redirect(url_for("admin.song_genres", song_id=song_id))


@bp.route("/songs/<int:song_id>/genres", methods=["GET", "POST"])
@admin_required
def song_genres(song_id):
    song = db.one("admin.song_for_admin", song_id=song_id)
    if song is None:
        abort(404)
    if request.method == "POST":
        genre_ids = sorted({int(g) for g in request.form.getlist("genre_ids") if g.isdigit()})
        if not genre_ids:
            flash("A song needs at least one genre.", "error")
        else:
            try:
                # Remove the old genres and save the new ones, in one transaction.
                with db.transaction():
                    db.execute("admin.clear_song_genres", song_id=song_id)
                    for genre_id in genre_ids:
                        db.execute("admin.add_song_genre", song_id=song_id, genre_id=genre_id)
            except db.IntegrityError as err:
                if not db.missing_parent(err):
                    raise
                flash("One of those genres does not exist.", "error")
            else:
                flash("The genres are saved.", "success")
                return redirect(url_for("catalog.album", album_id=song["album_id"])
                                + f"#song-{song_id}")
    current = {row["genre_id"] for row in db.all("admin.genres_of_song", song_id=song_id)}
    return render_template("admin/song_genres.html", song=song, current=current,
                           genres=db.all("admin.genre_choices"))
