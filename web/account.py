"""Sign up, log in and log out."""

import re

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from . import db
from .security import safe_next

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
