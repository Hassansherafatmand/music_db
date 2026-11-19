-- test_constraints.sql: every statement here MUST FAIL.
-- Each one breaks a constraint, so the database refuses it and saves nothing.
-- Run it with --force, so MySQL keeps going after each error:
--   mysql --force -u root -p music_db < queries/test_constraints.sql

-- PRIMARY KEY (two columns): a listener loves the same song a second time.
INSERT INTO favorite (listener_id, song_id)
SELECT listener_id, song_id FROM favorite LIMIT 1;

-- UNIQUE: a second genre called 'Rock'.
INSERT INTO genre (genre_name) VALUES ('Rock');

-- UNIQUE: a new listener with a username that is already taken.
INSERT INTO listener (username, email)
SELECT username, 'someone.new@example.com' FROM listener LIMIT 1;

-- NOT NULL: an artist with no name.
INSERT INTO artist (artist_name, debut_year) VALUES (NULL, 2000);

-- FOREIGN KEY: a favorite for a song that does not exist.
INSERT INTO favorite (listener_id, song_id) VALUES (1, 999999);

-- FOREIGN KEY: deleting an artist who still has albums.
DELETE FROM artist WHERE artist_id = (SELECT artist_id FROM album LIMIT 1);

-- CHECK: a review with 6 stars.
INSERT INTO review (listener_id, album_id, stars) VALUES (3, 101, 6);
