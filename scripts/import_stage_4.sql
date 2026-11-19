-- Import script, Stage 4: load the extra genres and the reviews.
--
-- This runs AFTER migration 010 (the pivot). The pivot already copied each song's
-- first genre into song_genre. This file adds a second (or third) genre to some songs.
-- An empty review_text in the CSV becomes NULL (NULLIF), not an empty text ''.

LOAD DATA LOCAL INFILE 'data/song_genre_extra.csv'
INTO TABLE song_genre
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(song_id, genre_id);

LOAD DATA LOCAL INFILE 'data/review.csv'
INTO TABLE review
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(listener_id, album_id, stars, @review_text, review_date)
SET review_text = NULLIF(@review_text, '');
