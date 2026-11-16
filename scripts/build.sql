-- Build the whole database from zero, stage by stage.
--
-- WARNING: this deletes the old music_db database first.
--
-- Run it from the repo folder (the paths below start there):
--   mysql --local-infile=1 --commands -u root -p < scripts/build.sql
--
-- --local-infile=1 lets the import scripts read the CSV files.
-- --commands lets this file use SOURCE (MySQL 9 turns it off by default).
-- If MySQL says "Loading local data is disabled", run this once as root:
--   SET GLOBAL local_infile = 1;
--
-- Why stage by stage (each stage's tables, then that stage's data)?
-- Like in real life, the data is already there when a later migration changes a
-- table. A migration that moves data (like the Stage 4 pivot) needs this.

DROP DATABASE IF EXISTS music_db;
CREATE DATABASE music_db;
USE music_db;

-- Stage 1: the music catalog
SOURCE migrations/001_create_artist.sql;
SOURCE migrations/002_create_album.sql;
SOURCE migrations/003_create_genre.sql;
SOURCE migrations/004_create_song.sql;
SOURCE scripts/import_stage_1.sql;

-- Stage 2: listeners and favorites
SOURCE migrations/005_create_listener.sql;
SOURCE migrations/006_create_favorite.sql;
SOURCE scripts/import_stage_2.sql;

-- Stage 3: playlists and plays
SOURCE migrations/007_create_playlist.sql;
SOURCE migrations/008_create_playlist_song.sql;
SOURCE migrations/009_create_play.sql;
SOURCE scripts/import_stage_3.sql;
