"""Helpers for the list pages (Songs, Albums, Artists, Listeners): read the visitor's
filters from the address safely, and work out the page numbers.

Everything in the address (?genre=3&sort=loved&page=2) comes from the visitor, so it
is checked here first: numbers must be numbers, and a choice must be in a fixed list.
Anything else is ignored, as if the visitor did not choose it.
"""

import re

from flask import request

from . import db


def number(name, allowed=None):
    """A whole number from the address, like ?genre=3. None if missing or not allowed."""
    raw = request.args.get(name, "").strip()
    if not re.fullmatch(r"\d{1,9}", raw):
        return None
    value = int(raw)
    if allowed is not None and value not in allowed:
        return None
    return value


def choice(name, allowed):
    """A word from the address that must be one of the allowed words, or None."""
    value = request.args.get(name, "").strip()
    return value if value in allowed else None


def sort_choice(statement, labels, default):
    """The sort the visitor chose (?sort=...), only if the statement has that piece.

    labels: {"loved": "Most loved", ...}, in the order shown in the menu."""
    allowed = [key for key in labels if key in db.pieces(statement, "sort")]
    chosen = request.args.get("sort", "")
    return (chosen if chosen in allowed else default), [(key, labels[key]) for key in allowed]


class Pages:
    """Page numbers for a list: "Page 2 of 20", and which numbers to show."""

    def __init__(self, total, per_page):
        self.total = total
        self.per_page = per_page
        self.count = max(1, -(-total // per_page))  # rounded up
        asked = number("page") or 1
        self.page = min(max(asked, 1), self.count)
        self.first_row = (self.page - 1) * per_page + 1 if total else 0
        self.last_row = min(self.page * per_page, total)

    @property
    def numbers(self):
        """Like [1, None, 4, 5, 6, None, 20]: None is shown as '…'."""
        near = {1, self.count, self.page - 1, self.page, self.page + 1}
        shown, last = [], 0
        for n in sorted(p for p in near if 1 <= p <= self.count):
            if n - last > 1:
                shown.append(None)
            shown.append(n)
            last = n
        return shown


def menu(name, label, all_label, options, current):
    """One filter menu for the page: options is a list of (value, text)."""
    return {"name": name, "label": label, "all": all_label, "options": list(options),
            "current": current}


def page_number():
    """The page the visitor asked for (1 if none). The list is cut with LIMIT/OFFSET."""
    return max(number("page") or 1, 1)
