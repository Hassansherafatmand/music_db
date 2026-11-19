"""Write, change or delete a review of an album (1 to 5 stars), and comment on reviews."""

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


# ---------------------------------------------------------------- comments under reviews

@bp.post("/albums/<int:album_id>/reviews/<int:reviewer_id>/comments")
@login_required
def add_comment(album_id, reviewer_id):
    text = " ".join((request.form.get("comment_text") or "").split())[:500]
    anchor = f"#review-{reviewer_id}"
    if not text:
        flash("A comment needs some words.", "error")
        return redirect(url_for("catalog.album", album_id=album_id) + anchor)
    try:
        _, comment_id = db.execute("reviews.add_comment", reviewer_id=reviewer_id,
                                   album_id=album_id, listener_id=current_listener_id(),
                                   comment_text=text)
    except mysql.connector.errors.DatabaseError as err:
        if db.missing_parent(err):  # the two-column foreign key: no such review
            abort(404)
        if err.errno != CHECK_FAILED:  # CHECK: a comment needs words
            raise
        flash("A comment needs some words.", "error")
        return redirect(url_for("catalog.album", album_id=album_id) + anchor)
    flash("Your comment is posted.", "success")
    return redirect(url_for("catalog.album", album_id=album_id) + f"#comment-{comment_id}")


@bp.post("/comments/<int:comment_id>/delete")
@login_required
def delete_comment(comment_id):
    found = db.one("reviews.comment_by_id", comment_id=comment_id)
    if found is None:
        abort(404)
    deleted, _ = db.execute("reviews.delete_my_comment", comment_id=comment_id,
                            listener_id=current_listener_id())
    flash("Your comment is deleted." if deleted else "You can only delete your own comments.",
          "info" if deleted else "error")
    return redirect(url_for("catalog.album", album_id=found["album_id"])
                    + f"#review-{found['reviewer_id']}")
