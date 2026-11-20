#!/usr/bin/env bash
# Start the music_db website with one command (Mac or Linux):
#
#   ./run.sh           start the website (the first time, it sets everything up)
#   ./run.sh --fresh   build the database again from zero first (website changes are lost)
#
# The first time, it does steps 1 to 4 of the README for you:
#   - makes the Python folder (.venv) and installs the packages
#   - makes the settings file (.env) with a new random database password and secret key
#   - asks for your MySQL root password once, builds the database (scripts/build.sql)
#     if it is not there yet (or if it is an older version), and makes the website's
#     own MySQL user (music_app)
# After that, it only starts the website and opens it in your browser.

set -euo pipefail
cd "$(dirname "$0")"

PORT="${PORT:-5050}"
URL="http://127.0.0.1:$PORT"
PY=.venv/bin/python

case "${1:-}" in
    "")      FRESH=0 ;;
    --fresh) FRESH=1 ;;
    *)       echo "Usage: ./run.sh [--fresh]"; exit 2 ;;
esac

say()  { printf '\n\033[1;35m♪ %s\033[0m\n' "$*"; }
fail() { printf '\n\033[1;31m✗ %s\033[0m\n' "$*" >&2; exit 1; }
open_url() {
    if [ "${OPEN_BROWSER:-1}" = 1 ]; then
        open "$1" 2>/dev/null || xdg-open "$1" >/dev/null 2>&1 || true
    fi
}

# ---------------------------------------------------------------- already running?

if curl -s -o /dev/null "$URL"; then
    if [ "$FRESH" = 1 ]; then
        fail "The website is running. Stop it first (Ctrl+C in its window), then run ./run.sh --fresh"
    fi
    say "The website is already running: $URL"
    open_url "$URL"
    exit 0
fi

# ---------------------------------------------------------------- 1. Python packages

if [ ! -x "$PY" ]; then
    command -v python3 >/dev/null || fail "Python 3 is missing. Get it from https://www.python.org/downloads/"
    say "Making the Python folder (.venv). Only the first time."
    python3 -m venv .venv
fi
if ! "$PY" -c "import flask, mysql.connector, dotenv" 2>/dev/null; then
    say "Installing the Python packages. Only the first time."
    "$PY" -m pip install --quiet --disable-pip-version-check -r requirements.txt
fi

# ---------------------------------------------------------------- 2. Settings (.env)

[ -f .env ] || cp .env.example .env
chmod 600 .env

# Swap the example values in .env for new random ones. Values you changed stay.
FILLED=$("$PY" - <<'EOF'
import secrets

example = {
    "MYSQL_PASSWORD": ("change-me", lambda: secrets.token_hex(16)),
    "SECRET_KEY": ("paste-a-long-random-text-here", lambda: secrets.token_hex(32)),
    # an older .env.example had a placeholder here; now it is the demo password
    "ADMIN_PASSWORD": ("choose-an-admin-password", lambda: "music330"),
}
lines, filled = [], []
with open(".env") as f:
    for line in f:
        key, sep, value = line.rstrip("\n").partition("=")
        key = key.strip()
        if sep and key in example and value.strip() == example[key][0]:
            line = f"{key}={example[key][1]()}\n"
            filled.append(key)
        lines.append(line)
if filled:
    with open(".env", "w") as f:
        f.writelines(lines)
print(" ".join(filled))
EOF
)
if [ -n "$FILLED" ]; then
    say "Wrote new random values into .env: $FILLED"
fi

# One setting, read the same way the website reads it.
setting() {
    "$PY" -c 'import os, sys
from dotenv import load_dotenv
load_dotenv(".env")
print(os.environ.get(sys.argv[1]) or sys.argv[2])' "$1" "$2"
}

# Can the website log in to MySQL and find the finished database?
# Prints "ok", or the MySQL error number.
check_db() {
    "$PY" - <<'EOF'
import os
from dotenv import load_dotenv
import mysql.connector

load_dotenv(".env")
try:
    conn = mysql.connector.connect(
        host=os.environ.get("MYSQL_HOST", "127.0.0.1"),
        port=int(os.environ.get("MYSQL_PORT", "3306")),
        user=os.environ.get("MYSQL_USER", "music_app"),
        password=os.environ.get("MYSQL_PASSWORD", ""),
        database=os.environ.get("MYSQL_DATABASE", "music_db"),
        connection_timeout=5,
    )
    cur = conn.cursor()
    # Things from the newest migrations: an older database doesn't have them yet.
    cur.execute("SELECT (SELECT password_hash FROM listener LIMIT 1),"
                "       (SELECT comment_id FROM review_comment LIMIT 1),"
                "       (SELECT album_id FROM public_album LIMIT 1)")
    cur.fetchall()
    conn.close()
    print("ok")
except mysql.connector.Error as err:
    print(err.errno)
EOF
}

mysql_is_off() { case "$1" in 2002|2003|2013) return 0 ;; *) return 1 ;; esac; }

# ---------------------------------------------------------------- 3. Is MySQL on?

STATUS=$(check_db)
if mysql_is_off "$STATUS"; then
    say "MySQL is not running."
    echo "  Start it: System Settings > MySQL > Start MySQL Server."
    if [ -d /Library/PreferencePanes/MySQL.prefPane ] && [ "${OPEN_BROWSER:-1}" = 1 ]; then
        open /Library/PreferencePanes/MySQL.prefPane || true
    fi
    echo "  Waiting for MySQL to start..."
    for _ in $(seq 1 90); do
        sleep 2
        STATUS=$(check_db)
        mysql_is_off "$STATUS" || break
    done
    if mysql_is_off "$STATUS"; then
        fail "MySQL is still not running. Start it, then run ./run.sh again."
    fi
fi

# ---------------------------------------------------------------- 4. Database and user

setup() {
    local mysql_bin tmp cnf root_pw esc built old_infile try
    mysql_bin=$(command -v mysql || echo /usr/local/mysql/bin/mysql)
    [ -x "$mysql_bin" ] || fail "I can't find the mysql program. Is MySQL installed?"

    # The root password goes in a private temporary file (only you can read it),
    # so you type it once. The file is deleted at the end.
    tmp=$(mktemp -d)
    trap "rm -rf '$tmp'" EXIT
    cnf="$tmp/root.cnf"

    say "Setup: I need your MySQL root password (the one you chose when you installed MySQL)."
    echo "  Nothing shows while you type. That's normal. Then press Enter."
    for try in 1 2 3; do
        read -r -s -p "  MySQL root password: " root_pw || true
        echo
        esc=${root_pw//\\/\\\\}    # in the file, \ is written \\ and " is written \"
        esc=${esc//\"/\\\"}
        {
            echo "[client]"
            echo "user=root"
            printf 'password="%s"\n' "$esc"
            echo "host=$(setting MYSQL_HOST 127.0.0.1)"
            echo "port=$(setting MYSQL_PORT 3306)"
        } > "$cnf"
        if "$mysql_bin" --defaults-extra-file="$cnf" -e "SELECT 1" >/dev/null 2>"$tmp/err"; then
            break
        fi
        echo "  That didn't work: $(grep -o 'ERROR.*' "$tmp/err" | head -1)"
        if [ "$try" = 3 ]; then
            fail "That's 3 tries. Run ./run.sh again when you have the root password."
        fi
    done
    root_pw= esc=

    # Is the newest version of the database there? (6 = yes: the newest table, view,
    # trigger, index and column all exist.)
    built=$("$mysql_bin" --defaults-extra-file="$cnf" -N -B -e "
        SELECT (SELECT COUNT(*) FROM information_schema.tables
                WHERE table_schema = 'music_db'
                  AND table_name IN ('review_comment', 'audit_log', 'public_album'))
             + (SELECT COUNT(*) FROM information_schema.triggers
                WHERE trigger_schema = 'music_db' AND trigger_name = 'trg_listener_deleted')
             + (SELECT COUNT(*) FROM information_schema.statistics
                WHERE table_schema = 'music_db' AND index_name = 'ft_artist_name' LIMIT 1)
             + (SELECT COUNT(*) FROM information_schema.columns
                WHERE table_schema = 'music_db' AND table_name = 'listener'
                  AND column_name = 'password_hash')")

    if [ "$built" != 0 ] && [ "$built" != 6 ] && [ "$FRESH" = 0 ]; then
        say "Your music_db database is an older version, so it gets built again."
    fi
    if [ "$FRESH" = 1 ] || [ "$built" != 6 ]; then
        say "Building the database from zero (scripts/build.sql). This takes a few seconds..."
        # The import scripts read CSV files (LOAD DATA LOCAL INFILE), so this is
        # turned on just for the build, then set back.
        old_infile=$("$mysql_bin" --defaults-extra-file="$cnf" -N -B -e "SELECT @@GLOBAL.local_infile")
        "$mysql_bin" --defaults-extra-file="$cnf" -e "SET GLOBAL local_infile = 1"
        if ! "$mysql_bin" --defaults-extra-file="$cnf" --local-infile=1 --commands < scripts/build.sql; then
            "$mysql_bin" --defaults-extra-file="$cnf" -e "SET GLOBAL local_infile = $old_infile"
            fail "Building the database failed (see the error above)."
        fi
        "$mysql_bin" --defaults-extra-file="$cnf" -e "SET GLOBAL local_infile = $old_infile"
        echo "  Done: 13 tables, 4 views and 4 triggers, with the demo data."
    fi

    say "Making the website's MySQL user (music_app). It can't drop tables."
    "$PY" - <<'EOF' | "$mysql_bin" --defaults-extra-file="$cnf"
import os, re, sys
from dotenv import load_dotenv

load_dotenv(".env")
user = os.environ.get("MYSQL_USER", "music_app")
db = os.environ.get("MYSQL_DATABASE", "music_db")
if user == "root" or not re.fullmatch(r"\w+", user) or not re.fullmatch(r"\w+", db):
    sys.exit("MYSQL_USER in .env must be a new user like music_app (not root).")
password = os.environ.get("MYSQL_PASSWORD", "").replace("\\", "\\\\").replace("'", "''")
hosts = ["127.0.0.1", "localhost"]
accounts = ", ".join(f"'{user}'@'{host}'" for host in hosts)
print(f"DROP USER IF EXISTS {accounts};")
for host in hosts:
    print(f"CREATE USER '{user}'@'{host}' IDENTIFIED BY '{password}';")
print(f"GRANT SELECT, INSERT, UPDATE, DELETE ON `{db}`.* TO {accounts};")
EOF

    rm -rf "$tmp"
    trap - EXIT
}

if [ "$STATUS" != ok ] || [ "$FRESH" = 1 ]; then
    setup
    STATUS=$(check_db)
    [ "$STATUS" = ok ] || fail "The website still can't use MySQL (MySQL error $STATUS)."
fi

# ---------------------------------------------------------------- 5. Start

say "Starting music_db: $URL"
echo "  Log in as a practice listener: sunny_cactus40, password music330"
ADMIN_USER=$(setting ADMIN_USERNAME admin)
ADMIN_PW=$(setting ADMIN_PASSWORD "")
if [ -n "$ADMIN_PW" ]; then
    echo "  Admin page: $URL/admin (username: $ADMIN_USER, password: $ADMIN_PW, from .env)"
fi
echo "  To stop the website, press Ctrl+C."
echo

# Open the browser as soon as the website answers.
( for _ in $(seq 1 40); do
      if curl -s -o /dev/null "$URL"; then open_url "$URL"; break; fi
      sleep 0.5
  done ) &

exec "$PY" -m flask --app web run --port "$PORT"
