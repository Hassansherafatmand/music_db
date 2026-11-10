-- Import script, Stage 2: load the listeners and their favorite songs.
--
-- Parents first: listener before favorite. (The songs are loaded in Stage 1.)
-- The CSV files use Windows line ends ('\r\n') and a header line (IGNORE 1 LINES).

LOAD DATA LOCAL INFILE 'data/listener.csv'
INTO TABLE listener
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(listener_id, username, email, joined_date);

LOAD DATA LOCAL INFILE 'data/favorite.csv'
INTO TABLE favorite
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(listener_id, song_id, added_date);
