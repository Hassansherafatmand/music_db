# music_db

A small music website where listeners browse artists, albums and songs, ♥ the songs they
love, build playlists in their own order, and review albums with 1 to 5 stars.

It has two parts: a **MySQL database** (13 tables, 4 views, 4 triggers), built in 4 stages
with migrations, and a **real website** made with Python and Flask that uses it.

My final project for CS330 (Databases) at Olympic College.

![The album page while a song is playing](docs/screenshots/album.jpg)

- **The database design:** [docs/design.md](docs/design.md) (tables, keys, relationships,
  views, triggers, indexes, and the 4 stages)
- **The website:** [docs/app.md](docs/app.md) (every page, the SQL it runs, and how it is
  kept safe)
- **A 10-minute tour:** [docs/demo.md](docs/demo.md) (what to click in a presentation)

## What the website can do

| For everyone | For logged-in listeners | For the admin |
|---|---|---|
| Browse songs, albums and artists, with filters and sorts | ♥ songs, and see "My favorites" | Add, edit and delete artists, albums and songs |
| Search (with `FULLTEXT` indexes) | Make playlists, put songs in order | Add, edit and delete listeners |
| Charts: top 3 per genre, plays per day | Press ▶ (saves a play) and see "My top songs" | Delete any review or comment |
| Listener profiles: everyone's taste is different | Write reviews, and comment on other reviews | Reports: questions answered with SQL |
| The Lab: SQL injection, indexes, two browsers | My account: change email or password, delete it | The audit log (written by triggers) |

Every page shows its own SQL: open **"Under the hood"** at the bottom of any page to see
the statements that built it, with their parameters.

There is no real sound. Pressing ▶ saves one row in the `play` table.

## Run it on your computer

You need **MySQL 8 or 9** and **Python 3.10 or newer**. Run every command from this folder.

**The quick way (Mac or Linux):** one command does steps 1 to 5 below for you:

```sh
./run.sh
```

The first time, it asks for your MySQL root password once. Then it builds the database (if
it isn't there yet, or if it is an older version), makes the `music_app` user and a `.env`
file with new random passwords, starts the website and opens it in your browser. After
that, `./run.sh` only starts the website. `./run.sh --fresh` builds the database again from
zero.

**Or step by step** (also on Windows):

**1. Build the database.** This deletes the old `music_db` database, then builds it stage
by stage, with the practice data:

```sh
mysql --local-infile=1 --commands -u root -p < scripts/build.sql
```

If MySQL says "Loading local data is disabled", run `SET GLOBAL local_infile = 1;` once as
root.

**2. Make a MySQL user for the website.** It can read and change data, but it can't drop
tables. Log in with `mysql -u root -p` and run (choose your own password):

```sql
CREATE USER 'music_app'@'127.0.0.1' IDENTIFIED BY 'choose-a-password';
GRANT SELECT, INSERT, UPDATE, DELETE ON music_db.* TO 'music_app'@'127.0.0.1';
```

**3. Install the Python packages** in a private folder (`.venv`):

```sh
python3 -m venv .venv
source .venv/bin/activate        # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**4. Write your settings.** Copy the example file, then open `.env` and fill it in: the
password from step 2, a secret key, and an admin password. `.env` is never uploaded to
GitHub.

```sh
cp .env.example .env
python3 -c "import secrets; print(secrets.token_hex(32))"   # makes a secret key
```

**5. Start the website**, then open http://127.0.0.1:5050 in your browser:

```sh
flask --app web run --port 5050
```

(Port 5050, because macOS already uses port 5000 for AirPlay.)

**Try it:** log in as any practice listener, for example `sunny_cactus40`, with the
password `music330`. The admin page is at http://127.0.0.1:5050/admin and uses the
`ADMIN_PASSWORD` from your `.env` file.

## Screenshots

| | |
|---|---|
| ![Home page](docs/screenshots/home.jpg) | ![Songs with filters](docs/screenshots/songs.jpg) |
| **Home:** most played, most loved, and the newest albums | **Songs:** filters and a sort; each one changes the SQL |
| ![Listeners](docs/screenshots/listeners.jpg) | ![A profile](docs/screenshots/profile.jpg) |
| **Listeners:** each one's top genre, found with a window function | **A profile:** taste, last 30 days (a recursive CTE), “you both love” (`INTERSECT`) |
| ![Reviews and comments](docs/screenshots/comments.jpg) | ![Charts](docs/screenshots/charts.jpg) |
| **Reviews and comments:** a comment points to its review with a two-column foreign key | **Charts:** `RANK() OVER (PARTITION BY ...)` and a running total |
| ![A playlist](docs/screenshots/playlist.jpg) | ![Add to playlist](docs/screenshots/add-to-playlist.jpg) |
| **A playlist:** move songs up and down, or remove them | **Add to playlist:** a transaction that locks the playlist (`FOR UPDATE`) |
| ![My top songs](docs/screenshots/top-songs.jpg) | ![Delete my account](docs/screenshots/account-delete.jpg) |
| **My top songs:** counted from the `play` table with `GROUP BY` | **My account:** what `ON DELETE CASCADE` removes with an account |
| ![The admin page](docs/screenshots/admin.jpg) | ![Delete a listener](docs/screenshots/admin-cascade.jpg) |
| **The admin page:** CRUD, reports and the audit log | **Admin, delete a listener:** the cascade, before it happens |
| ![RESTRICT says no](docs/screenshots/admin-restrict.jpg) | ![The audit log](docs/screenshots/audit.jpg) |
| **Admin, delete a song:** MySQL says no (`RESTRICT`) | **The audit log:** written by a trigger, `AFTER DELETE` |
| ![Reports](docs/screenshots/reports.jpg) | ![Lab: security](docs/screenshots/lab-security.jpg) |
| **Reports:** `NOT EXISTS`, `EXCEPT`, `CASE`, a correlated subquery | **Lab, security:** why SQL injection fails here |
| ![Lab: speed](docs/screenshots/lab-speed.jpg) | ![Under the hood](docs/screenshots/under-the-hood.jpg) |
| **Lab, speed:** indexes, and what `EXPLAIN` says | **Under the hood:** the SQL behind every page |
| ![Log in](docs/screenshots/login.jpg) | |
| **Log in:** passwords are saved only as a hash | |

<p>
  <img src="docs/screenshots/phone-home.jpg" alt="The home page on a phone" width="240">
  <img src="docs/screenshots/phone-songs.jpg" alt="The songs list on a phone" width="240">
  <img src="docs/screenshots/phone-album.jpg" alt="An album on a phone" width="240">
</p>

## How it is built

The database grows in 4 stages. Each stage is a set of migrations: small numbered SQL
files that run in order. Each finished stage has a git tag, `stage-1` to `stage-4`.

After Stage 4 came the website, and with it migrations 012 to 016: a `password_hash`
column, comments under reviews (`review_comment`), an audit log with triggers
(`audit_log`), 4 views and the indexes for searching. Then the **content pack**
(`data/content/`) adds more made-up data, so the website looks like a real one: every
album has at least 3 songs, there are 120 listeners with different tastes, and hundreds of
reviews and comments.

## Files

- `docs/design.md`: the database design. `docs/app.md`: the website. `docs/demo.md`: a tour.
- `docs/stage-1.md` to `docs/stage-4.md`: the diagrams for each stage
- `migrations/`: the migrations (small numbered SQL files)
- `scripts/`: one import script per stage and one for the content pack, the build script,
  the demo passwords, the content generator (`make_content.py`), and the nightly
  top-songs job
- `queries/`: the review feature from start to end (`showcase.sql`), and statements that
  must fail, to test the constraints (`test_constraints.sql`)
- `web/`: the website. Python in `web/*.py`, every SQL statement in `web/sql/*.sql`, the
  pages in `web/templates/`, and the design in `web/static/`
- `data/`: made-up practice data (CSV files), generated with AI; `data/content/` is the
  content pack
- `run.sh`: sets everything up and starts the website with one command
- `requirements.txt`: the Python packages. `.env.example`: the settings to copy.
