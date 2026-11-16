-- Import script, Stage 3: load the playlists, their songs, and the plays.
--
-- Parents first: playlist before playlist_song.
-- The CSV files use Windows line ends ('\r\n') and a header line (IGNORE 1 LINES).

LOAD DATA LOCAL INFILE 'data/playlist.csv'
INTO TABLE playlist
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(playlist_id, listener_id, playlist_name, created_date);

LOAD DATA LOCAL INFILE 'data/playlist_song.csv'
INTO TABLE playlist_song
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(playlist_id, song_id, position, added_date);

LOAD DATA LOCAL INFILE 'data/play.csv'
INTO TABLE play
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(play_id, listener_id, song_id, played_at);
