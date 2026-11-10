-- Import script, Stage 1: load the music catalog from data/*.csv into the tables.
--
-- Order matters: parents first (artist, genre), then children (album, song).
-- So every foreign key already has its parent row when the child row arrives.
--
-- The CSV files use Windows line ends ('\r\n') and a header line (IGNORE 1 LINES).
-- An empty cell in the CSV becomes NULL (NULLIF), not an empty text ''.

LOAD DATA LOCAL INFILE 'data/artist.csv'
INTO TABLE artist
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(artist_id, artist_name, @origin_state, debut_year)
SET origin_state = NULLIF(@origin_state, '');

LOAD DATA LOCAL INFILE 'data/genre.csv'
INTO TABLE genre
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(genre_id, genre_name);

LOAD DATA LOCAL INFILE 'data/album.csv'
INTO TABLE album
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(album_id, @album_name, release_year, artist_id)
SET album_name = NULLIF(@album_name, '');

LOAD DATA LOCAL INFILE 'data/song.csv'
INTO TABLE song
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(song_id, @song_name, duration_seconds, track_number, streams, album_id, genre_id)
SET song_name = NULLIF(@song_name, '');
