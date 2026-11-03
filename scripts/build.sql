-- Build the whole database from zero:
-- run every migration in order, then load the practice data.
--
-- WARNING: this deletes the old music_db database first.
--
-- Run it from the repo folder (the paths below start there):
--   mysql --local-infile=1 --commands -u root -p < scripts/build.sql
--
-- --local-infile=1 lets the import script read the CSV files.
-- --commands lets this file use SOURCE (MySQL 9 turns it off by default).
--
-- If MySQL says "Loading local data is disabled", run this once as root:
--   SET GLOBAL local_infile = 1;

DROP DATABASE IF EXISTS music_db;
CREATE DATABASE music_db;
USE music_db;

-- Stage 1: the music catalog
SOURCE migrations/001_create_artist.sql;
SOURCE migrations/002_create_album.sql;
SOURCE migrations/003_create_genre.sql;
SOURCE migrations/004_create_song.sql;

-- Data
SOURCE scripts/import_data.sql;
