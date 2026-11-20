"""The admin pages: CRUD for music and listeners, moderation, reports and the audit log.

CRUD = Create, Read, Update, Delete. The admin can:
  - add, edit and delete artists, albums and songs, and set a song's genres
  - add, edit and delete listeners (deleting shows what ON DELETE CASCADE removes)
  - delete any review or comment (moderation)
  - read the reports (questions answered with SQL) and the audit log (triggers)

It is protected by one admin account: ADMIN_USERNAME and ADMIN_PASSWORD in the private
.env file. The demo account (in .env.example) is admin / music330.
"""

import re
import secrets
from datetime import date

from flask import (Blueprint, abort, current_app, flash, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import generate_password_hash

from . import db, lists
from .account import EMAIL, USERNAME
from .security import admin_required, back, safe_next

bp = Blueprint("admin", __name__, url_prefix="/admin")


# ---------------------------------------------------------------- log in / out

DEMO_ADMIN = ("admin", "music330")   # the demo account in .env.example


def _same(typed, real):
    """Compare two texts in constant time (as bytes, so any character is allowed)."""
    return secrets.compare_digest(typed.encode(), real.encode())


@bp.route("/login", methods=["GET", "POST"])
def login():
    username = current_app.config["ADMIN_USERNAME"]
    password = current_app.config["ADMIN_PASSWORD"]
    error = None
    if request.method == "POST":
        # Check both, always, so the answer doesn't say which one was wrong.
        name_ok = _same(request.form.get("username", "").strip(), username)
        password_ok = _same(request.form.get("password", ""), password)
        if password and name_ok and password_ok:
            session["is_admin"] = True
            flash("Admin mode is on.", "success")
            return redirect(safe_next(request.args.get("next"), url_for("admin.dashboard")))
        error = "That username or password is wrong."
    return render_template("admin/login.html", error=error, disabled=not password,
                           demo=(username, password) == DEMO_ADMIN)


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
        unfinished=db.all("admin.unfinished_albums"),
        audit=db.one("admin.audit_counts"),
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


# ---------------------------------------------------------------- deleting, safely

# When a foreign key with RESTRICT says no, MySQL names it. What each one means:
STILL_USED = {
    "fk_album_artist": "this artist still has albums",
    "fk_song_album": "this album still has songs",
    "fk_review_album": "this album still has reviews",
    "fk_favorite_song": "listeners still \u2665 this song",
    "fk_playlist_song_song": "this song is still in playlists",
    "fk_play_song": "this song has plays",
}


def _delete(statement, label, **params):
    """Try a DELETE. The audit trigger writes who did it. If a foreign key with RESTRICT
    says no, show MySQL's answer. Returns True if the row is gone."""
    try:
        with db.transaction():
            db.execute("account.set_audit_actor", actor="admin")
            deleted, _ = db.execute(statement, **params)
    except db.IntegrityError as err:
        fk = db.still_used(err)
        if not fk:
            raise
        flash(f"MySQL said no: {STILL_USED.get(fk, 'other rows still use it')} "
              f"(foreign key {fk}, RESTRICT). Nothing was deleted.", "error")
        return False
    if deleted:
        flash(f"Deleted {label}. The audit log has a new row.", "success")
    return bool(deleted)


def _name(field, limit=100):
    return " ".join(request.form.get(field, "").split())[:limit]


# ---------------------------------------------------------------- listeners (CRUD)

LISTENER_SORTS = {"newest": "Newest first", "oldest": "Oldest first", "name": "Username",
                  "active": "Most plays"}


@bp.get("/listeners")
@admin_required
def listeners():
    statement = "admin.browse_listeners"
    words = request.args.get("q", "").strip()[:60]
    sort, sort_options = lists.sort_choice(statement, LISTENER_SORTS, "newest")
    where, params = [], {}
    if words:
        escaped = words.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        where, params = ["search"], {"pattern": f"%{escaped}%"}
    page = lists.page_number()
    rows, total = db.browse(statement, where=where, sort=sort, page=page, per_page=30, **params)
    return render_template("admin/listeners.html", listeners=rows, words=words, sort=sort,
                           sort_options=sort_options, pages=lists.Pages(total, 30))


@bp.post("/listeners/new")
@admin_required
def add_listener():
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    if not USERNAME.match(username):
        flash("Username: 3 to 30 letters, numbers or _.", "error")
    elif not EMAIL.match(email):
        flash("Please type a real email address.", "error")
    elif len(password) < 8:
        flash("The password needs at least 8 characters.", "error")
    else:
        try:
            _, listener_id = db.execute("account.create_listener", username=username,
                                        email=email,
                                        password_hash=generate_password_hash(password))
        except db.IntegrityError as err:
            if not db.duplicate_key(err):
                raise
            flash("That username or email is already taken (UNIQUE).", "error")
        else:
            flash(f'Added the listener "{username}".', "success")
            return redirect(url_for("admin.listener", listener_id=listener_id))
    return redirect(url_for("admin.listeners"))


@bp.get("/listeners/<int:listener_id>")
@admin_required
def listener(listener_id):
    found = db.one("admin.listener_for_admin", listener_id=listener_id)
    if found is None:
        abort(404)
    return render_template(
        "admin/listener.html", person=found,
        goes=db.one("account.what_goes_too", listener_id=listener_id),
        reviews=db.all("community.reviews", listener_id=listener_id),
        comments=db.all("community.comments", listener_id=listener_id))


@bp.post("/listeners/<int:listener_id>/edit")
@admin_required
def edit_listener(listener_id):
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip().lower()
    if not USERNAME.match(username):
        flash("Username: 3 to 30 letters, numbers or _.", "error")
    elif not EMAIL.match(email):
        flash("Please type a real email address.", "error")
    else:
        try:
            db.execute("admin.update_listener", username=username, email=email,
                       listener_id=listener_id)
            flash("Saved.", "success")
        except db.IntegrityError as err:
            if not db.duplicate_key(err):
                raise
            flash("That username or email is already taken (UNIQUE).", "error")
    return redirect(url_for("admin.listener", listener_id=listener_id))


@bp.post("/listeners/<int:listener_id>/delete")
@admin_required
def delete_listener(listener_id):
    found = db.one("admin.listener_for_admin", listener_id=listener_id)
    if found is None:
        abort(404)
    if _delete("account.delete_listener", f'the listener "{found["username"]}" and '
               "everything that belonged to them (ON DELETE CASCADE)", listener_id=listener_id):
        if session.get("listener_id") == listener_id:  # the admin deleted their own login
            session.pop("listener_id", None)
            session.pop("username", None)
        return redirect(url_for("admin.listeners"))
    return redirect(url_for("admin.listener", listener_id=listener_id))


# ---------------------------------------------------------------- moderation

@bp.post("/reviews/<int:listener_id>/<int:album_id>/delete")
@admin_required
def delete_review(listener_id, album_id):
    db.execute("admin.delete_review", listener_id=listener_id, album_id=album_id)
    flash("Deleted the review (and its comments: ON DELETE CASCADE).", "info")
    return back(url_for("catalog.album", album_id=album_id) + "#reviews")


@bp.post("/comments/<int:comment_id>/delete")
@admin_required
def delete_comment(comment_id):
    db.execute("admin.delete_comment", comment_id=comment_id)
    flash("Deleted the comment.", "info")
    return back(url_for("admin.dashboard"))


# ---------------------------------------------------------------- edit and delete music

@bp.route("/artists/<int:artist_id>", methods=["GET", "POST"])
@admin_required
def edit_artist(artist_id):
    found = db.one("catalog.artist_by_id", artist_id=artist_id)
    if found is None:
        abort(404)
    if request.method == "POST":
        name = _name("artist_name")
        state = request.form.get("origin_state", "").strip().upper() or None
        year = _year(request.form.get("debut_year"), "Debut year")
        if not name:
            flash("The artist needs a name.", "error")
        elif state and not re.fullmatch(r"[A-Z]{2}", state):
            flash("State: two letters, like WA (or leave it empty).", "error")
        elif year:
            db.execute("admin.update_artist", artist_name=name, origin_state=state,
                       debut_year=year, artist_id=artist_id)
            flash("Saved.", "success")
            return redirect(url_for("catalog.artist", artist_id=artist_id))
    return render_template("admin/edit_artist.html", artist=found,
                           uses=db.one("admin.artist_uses", artist_id=artist_id))


@bp.post("/artists/<int:artist_id>/delete")
@admin_required
def delete_artist(artist_id):
    found = db.one("catalog.artist_by_id", artist_id=artist_id)
    if found is None:
        abort(404)
    if _delete("admin.delete_artist", f'the artist "{found["artist_name"]}"',
               artist_id=artist_id):
        return redirect(url_for("catalog.artists"))
    return redirect(url_for("admin.edit_artist", artist_id=artist_id))


@bp.route("/albums/<int:album_id>", methods=["GET", "POST"])
@admin_required
def edit_album(album_id):
    found = db.one("admin.album_for_admin", album_id=album_id)
    if found is None:
        abort(404)
    if request.method == "POST":
        name = _name("album_name")
        artist_id = request.form.get("artist_id", type=int)
        year = _year(request.form.get("release_year"), "Release year")
        if not name:
            flash("The album needs a name.", "error")
        elif year and artist_id:
            try:
                db.execute("admin.update_album", album_name=name, release_year=year,
                           artist_id=artist_id, album_id=album_id)
            except db.IntegrityError as err:
                if not db.missing_parent(err):
                    raise
                flash("That artist does not exist.", "error")
            else:
                flash("Saved.", "success")
                return redirect(url_for("catalog.album", album_id=album_id))
    return render_template("admin/edit_album.html", album=found,
                           artists=db.all("admin.artist_choices"),
                           uses=db.one("admin.album_uses", album_id=album_id))


@bp.post("/albums/<int:album_id>/delete")
@admin_required
def delete_album(album_id):
    found = db.one("admin.album_for_admin", album_id=album_id)
    if found is None:
        abort(404)
    if _delete("admin.delete_album", f'the album "{found["album_name"] or "Untitled"}"',
               album_id=album_id):
        return redirect(url_for("catalog.artist", artist_id=found["artist_id"]))
    return redirect(url_for("admin.edit_album", album_id=album_id))


@bp.route("/songs/<int:song_id>", methods=["GET", "POST"])
@admin_required
def edit_song(song_id):
    found = db.one("admin.song_details_for_admin", song_id=song_id)
    if found is None:
        abort(404)
    if request.method == "POST":
        name = _name("song_name")
        album_id = request.form.get("album_id", type=int)
        track = request.form.get("track_number", type=int)
        seconds = _seconds(request.form.get("duration"))
        if not name:
            flash("The song needs a name.", "error")
        elif track is None or track < 1:
            flash("The track number must be 1 or more.", "error")
        elif seconds is None:
            flash("Length: type it like 3:45 (or in seconds, like 225).", "error")
        elif album_id:
            try:
                db.execute("admin.update_song", song_name=name, duration_seconds=seconds,
                           track_number=track, album_id=album_id, song_id=song_id)
            except db.IntegrityError as err:
                if db.duplicate_key(err):
                    flash(f"That album already has a track {track} (UNIQUE).", "error")
                elif db.missing_parent(err):
                    flash("That album does not exist.", "error")
                else:
                    raise
            else:
                flash("Saved.", "success")
                return redirect(url_for("catalog.album", album_id=album_id) + f"#song-{song_id}")
    return render_template("admin/edit_song.html", song=found,
                           albums=db.all("admin.album_choices"),
                           uses=db.one("admin.song_uses", song_id=song_id))


@bp.post("/songs/<int:song_id>/delete")
@admin_required
def delete_song(song_id):
    found = db.one("admin.song_details_for_admin", song_id=song_id)
    if found is None:
        abort(404)
    if _delete("admin.delete_song", f'the song "{found["song_name"] or "Untitled"}"',
               song_id=song_id):
        return redirect(url_for("catalog.album", album_id=found["album_id"]))
    return redirect(url_for("admin.edit_song", song_id=song_id))


# ---------------------------------------------------------------- reports and audit log

REPORTS = [
    ("unreviewed_albums", "Albums nobody reviewed", "LEFT JOIN ... WHERE ... IS NULL"),
    ("loved_never_played", "Loved, but never played", "NOT EXISTS"),
    ("album_hits", "The hits of each album", "a correlated subquery"),
    ("length_groups", "Short, medium or long songs", "CASE + GROUP BY"),
    ("reviewers_who_never_comment", "Reviewers who never comment", "EXCEPT (a set operation)"),
    ("busiest_hours", "When do people listen?", "HOUR() + GROUP BY"),
]


@bp.get("/reports")
@admin_required
def reports():
    results = []
    for key, title, technique in REPORTS:
        rows = db.all(f"reports.{key}")
        results.append({"key": key, "title": title, "technique": technique, "rows": rows,
                        "total": rows[0]["total_rows"] if rows else 0,
                        "question": db.about(f"reports.{key}"),
                        "sql": db.sql_text(f"reports.{key}")})
    return render_template("admin/reports.html", reports=results)


@bp.get("/audit")
@admin_required
def audit():
    return render_template("admin/audit.html", rows=db.all("admin.audit_log"))
