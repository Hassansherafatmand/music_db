"""Small safety helpers: login checks, form protection (CSRF) and safe redirects."""

import secrets
from functools import wraps
from urllib.parse import urlparse

from flask import abort, flash, redirect, request, session, url_for


# ---------------------------------------------------------------- who is logged in

def current_listener_id():
    """The logged-in listener's id, or None."""
    return session.get("listener_id")


def login_required(view):
    """Pages like "My favorites" need a logged-in listener. Others go to Log in first."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if current_listener_id() is None:
            flash("Please log in first.", "info")
            # After a button (POST), come back to the page the button was on.
            if request.method == "POST":
                come_back = safe_next(request.form.get("next"), "/")
            else:
                come_back = here()
            return redirect(url_for("account.login", next=come_back))
        return view(*args, **kwargs)
    return wrapper


def admin_required(view):
    """The admin page needs the admin login (ADMIN_USERNAME and ADMIN_PASSWORD in .env)."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin.login", next=here()))
        return view(*args, **kwargs)
    return wrapper


# ---------------------------------------------------------------- CSRF protection
#
# CSRF ("cross-site request forgery"): another website could hide a form that posts
# to our website, using the visitor's login. So every form here carries a secret
# token that only our pages know. A POST without the right token is refused.

def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_urlsafe(32)
    return session["_csrf"]


def check_csrf():
    if request.method == "POST":
        sent = request.form.get("_csrf", "")
        if not sent or not secrets.compare_digest(sent, session.get("_csrf", "")):
            abort(400, "This form is too old or not from this website. Please try again.")


# ---------------------------------------------------------------- redirects

def here():
    """The current page's address, to come back to it after a button press."""
    if request.query_string:
        return f"{request.path}?{request.query_string.decode()}"
    return request.path


def safe_next(target, fallback="/"):
    """Only follow 'next' addresses on this website (never to another site)."""
    if target:
        parts = urlparse(target)
        if not parts.scheme and not parts.netloc and target.startswith("/") \
                and not target.startswith("//"):
            return target
    return fallback


def back(fallback="/"):
    """Redirect back to the page the form came from."""
    return redirect(safe_next(request.form.get("next"), fallback))
