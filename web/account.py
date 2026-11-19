"""Sign up, log in, log out, and "My account" (change email or password, delete it)."""

import re

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from . import db
from .security import current_listener_id, login_required, safe_next

bp = Blueprint("account", __name__)

USERNAME = re.compile(r"^[A-Za-z0-9_]{3,30}$")
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _log_in(listener_id, username):
    session.clear()  # a fresh session at login
    session["listener_id"] = listener_id
    session["username"] = username


@bp.route("/signup", methods=["GET", "POST"])
def signup():
    form = {"username": "", "email": ""}
    errors = {}
    if request.method == "POST":
        form = {
            "username": request.form.get("username", "").strip(),
            "email": request.form.get("email", "").strip().lower(),
        }
        password = request.form.get("password", "")

        if not USERNAME.match(form["username"]):
            errors["username"] = "3 to 30 letters, numbers or _ (no spaces)."
        if not EMAIL.match(form["email"]) or len(form["email"]) > 100:
            errors["email"] = "Please type a real email address."
        if len(password) < 8:
            errors["password"] = "At least 8 characters."
        elif password != request.form.get("password2", ""):
            errors["password2"] = "The two passwords are not the same."

        if not errors:
            try:
                _, listener_id = db.execute(
                    "account.create_listener",
                    username=form["username"],
                    email=form["email"],
                    password_hash=generate_password_hash(password),
                )
            except db.IntegrityError as err:
                # The UNIQUE constraints in the database have the last word.
                key = db.duplicate_key(err) or ""
                if "username" in key:
                    errors["username"] = "This username is taken. Try another one."
                elif "email" in key:
                    errors["email"] = "There is already an account with this email."
                else:
                    raise
            else:
                _log_in(listener_id, form["username"])
                flash(f"Welcome to music_db, {form['username']}! 🎉", "success")
                return redirect(safe_next(request.args.get("next"), url_for("catalog.home")))

    return render_template("signup.html", form=form, errors=errors)


@bp.route("/login", methods=["GET", "POST"])
def login():
    username = ""
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        found = db.one("account.listener_by_username", username=username)
        # One message for both cases, so nobody can test which usernames exist.
        if found and found["password_hash"] and \
                check_password_hash(found["password_hash"], password):
            _log_in(found["listener_id"], found["username"])
            flash(f"Welcome back, {found['username']}!", "success")
            return redirect(safe_next(request.args.get("next"), url_for("catalog.home")))
        error = "Wrong username or password."

    return render_template("login.html", username=username, error=error)


@bp.post("/logout")
def logout():
    session.clear()
    flash("You are logged out. See you soon!", "info")
    return redirect(url_for("catalog.home"))


# ---------------------------------------------------------------- my account

def _password_ok(typed):
    row = db.one("account.my_password_hash", listener_id=current_listener_id())
    return bool(row and row["password_hash"] and check_password_hash(row["password_hash"], typed))


@bp.get("/me/account")
@login_required
def my_account():
    me = current_listener_id()
    return render_template("account.html",
                           me=db.one("account.my_account", listener_id=me),
                           goes=db.one("account.what_goes_too", listener_id=me))


@bp.post("/me/account/email")
@login_required
def change_email():
    email = request.form.get("email", "").strip().lower()
    if not EMAIL.match(email) or len(email) > 100:
        flash("Please type a real email address.", "error")
    else:
        try:
            db.execute("account.update_email", email=email, listener_id=current_listener_id())
            flash("Your email is changed.", "success")
        except db.IntegrityError as err:
            if not db.duplicate_key(err):
                raise
            flash("There is already an account with this email.", "error")  # UNIQUE (email)
    return redirect(url_for("account.my_account"))


@bp.post("/me/account/password")
@login_required
def change_password():
    new = request.form.get("new_password", "")
    if not _password_ok(request.form.get("password", "")):
        flash("Your current password is not right.", "error")
    elif len(new) < 8:
        flash("The new password needs at least 8 characters.", "error")
    elif new != request.form.get("new_password2", ""):
        flash("The two new passwords are not the same.", "error")
    else:
        db.execute("account.update_password", password_hash=generate_password_hash(new),
                   listener_id=current_listener_id())
        flash("Your password is changed.", "success")
    return redirect(url_for("account.my_account"))


@bp.post("/me/account/delete")
@login_required
def delete_account():
    if not _password_ok(request.form.get("password", "")):
        flash("That password is not right, so nothing was deleted.", "error")
        return redirect(url_for("account.my_account") + "#delete")
    username = session.get("username")
    with db.transaction():
        # The audit trigger writes who did it. ON DELETE CASCADE deletes the rest.
        db.execute("account.set_audit_actor", actor=f"{username} (deleted their own account)")
        db.execute("account.delete_listener", listener_id=current_listener_id())
    session.clear()
    flash("Your account and everything in it are deleted. Goodbye! 👋", "info")
    return redirect(url_for("catalog.home"))
