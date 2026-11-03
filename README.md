# music_db

A MySQL database about music: artists, their albums, songs and genres.

My final project for CS330 (Databases) at Olympic College. Work in progress.

## How it is built

The database grows in 4 stages. Each stage is a set of migrations: small
numbered SQL files that run in order. Each finished stage gets a git tag,
`stage-1` to `stage-4`.

## Files

- `music_db.sql`: the starting schema (4 tables)
- `music_db.md`: design notes
- `data/`: made-up practice data (CSV files), generated with AI
