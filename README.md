# music_db

A small music website where listeners browse artists, albums and songs, and save their
own favorite songs and playlists. The website is imaginary; the MySQL database and its
SQL files are real.

My final project for CS330 (Databases) at Olympic College. Work in progress.

**Full design:** [docs/design.md](docs/design.md) (the system, tables, keys,
relationships and stages).

## How it is built

The database grows in 4 stages. Each stage is a set of migrations: small
numbered SQL files that run in order. Each finished stage gets a git tag,
`stage-1` to `stage-4`.

## Build the database

From this folder, with MySQL 9:

```sh
mysql --local-infile=1 --commands -u root -p < scripts/build.sql
```

This deletes the old `music_db` database, runs every migration in order, and loads the
practice data. If MySQL says "Loading local data is disabled", run
`SET GLOBAL local_infile = 1;` once as root.

## Files

- `docs/design.md`: the full design
- `docs/stage-1.md`: the Stage 1 diagrams
- `migrations/`: the migrations (small numbered SQL files)
- `scripts/`: the import script and the build script
- `data/`: made-up practice data (CSV files), generated with AI
