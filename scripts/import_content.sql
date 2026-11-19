-- Import script, the website: load the content pack (data/content/*.csv).
--
-- This runs after migrations 013 to 016. It adds more made-up data, so the website
-- looks like a real one: every album gets at least 3 songs, 80 more listeners, and
-- more favorites, plays, playlists, reviews and comments. scripts/make_content.py
-- made the files (data/README.txt says what is in them).
--
-- The order matters, because of the foreign keys: parents first (album before song,
-- listener before favorite, review before review_comment).
-- Review and comment texts can have commas, so they are inside "quotes" in the CSV
-- (OPTIONALLY ENCLOSED BY '"').

LOAD DATA LOCAL INFILE 'data/content/album.csv'
INTO TABLE album
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(album_id, album_name, release_year, artist_id);

LOAD DATA LOCAL INFILE 'data/content/song.csv'
INTO TABLE song
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(song_id, song_name, duration_seconds, track_number, streams, album_id);

LOAD DATA LOCAL INFILE 'data/content/song_genre.csv'
INTO TABLE song_genre
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(song_id, genre_id);

LOAD DATA LOCAL INFILE 'data/content/listener.csv'
INTO TABLE listener
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(listener_id, username, email, joined_date);

LOAD DATA LOCAL INFILE 'data/content/favorite.csv'
INTO TABLE favorite
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(listener_id, song_id, added_date);

LOAD DATA LOCAL INFILE 'data/content/playlist.csv'
INTO TABLE playlist
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(playlist_id, listener_id, playlist_name, created_date);

LOAD DATA LOCAL INFILE 'data/content/playlist_song.csv'
INTO TABLE playlist_song
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(playlist_id, song_id, position, added_date);

LOAD DATA LOCAL INFILE 'data/content/play.csv'
INTO TABLE play
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(play_id, listener_id, song_id, played_at);

LOAD DATA LOCAL INFILE 'data/content/review.csv'
INTO TABLE review
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(listener_id, album_id, stars, @review_text, review_date)
SET review_text = NULLIF(@review_text, '');

LOAD DATA LOCAL INFILE 'data/content/review_comment.csv'
INTO TABLE review_comment
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(comment_id, reviewer_id, album_id, listener_id, comment_text, commented_at);
