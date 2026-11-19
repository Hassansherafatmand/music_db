"""Write, change or delete a review of an album (1 to 5 stars)."""

import mysql.connector
from flask import Blueprint, abort, flash, redirect, request, url_for

from . import db
from .security import current_listener_id, login_required

bp = Blueprint("reviews", __name__)

CHECK_FAILED = 3819  # MySQL's error number for "Check constraint ... is violated"


@bp.post("/albums/<int:album_id>/review")
@login_required
def save(album_id):
    stars = request.form.get("stars", type=int)
    text = (request.form.get("review_text") or "").strip()[:500] or None  # empty -> NULL
    if stars is None:
        flash("Please choose 1 to 5 stars.", "error")
    else:
        try:
            db.execute("reviews.save_review", listener_id=current_listener_id(),
                       album_id=album_id, stars=stars, review_text=text)
            flash("Thanks! Your review is saved.", "success")
        except mysql.connector.errors.DatabaseError as err:
            if db.missing_parent(err):  # the foreign key: no such album
                abort(404)
            if err.errno != CHECK_FAILED:  # CHECK (stars BETWEEN 1 AND 5)
                raise
            flash("Stars must be 1 to 5.", "error")
    return redirect(url_for("catalog.album", album_id=album_id) + "#reviews")


@bp.post("/albums/<int:album_id>/review/delete")
@login_required
def delete(album_id):
    db.execute("reviews.delete_review", listener_id=current_listener_id(), album_id=album_id)
    flash("Your review is deleted.", "info")
    return redirect(url_for("catalog.album", album_id=album_id) + "#reviews")
