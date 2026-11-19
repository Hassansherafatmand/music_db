-- admin.sql: the admin page adds music and sets a song's genres.


-- name: artist_choices
-- Every artist, for the "artist" menu when adding an album.
SELECT artist_id, artist_name
FROM artist
ORDER BY artist_name;

-- name: album_choices
-- Every album with its artist, for the "album" menu when adding a song.
SELECT a.album_id, a.album_name, a.release_year, ar.artist_name
FROM album a
JOIN artist ar ON ar.artist_id = a.artist_id
ORDER BY ar.artist_name, a.release_year, a.album_id;

-- name: genre_choices
-- Every genre, for the genre check boxes.
SELECT genre_id, genre_name
FROM genre
ORDER BY genre_name;

-- name: newest_songs
-- The 8 songs added last (the biggest song_id), to see what was just added.
SELECT s.song_id, s.song_name, s.track_number, a.album_id, a.album_name, ar.artist_name
FROM song s
JOIN album a   ON a.album_id = s.album_id
JOIN artist ar ON ar.artist_id = a.artist_id
ORDER BY s.song_id DESC
LIMIT 8;

-- name: add_artist
-- A new artist.
INSERT INTO artist (artist_name, origin_state, debut_year)
VALUES (%(artist_name)s, %(origin_state)s, %(debut_year)s);

-- name: add_album
-- A new album. The foreign key needs an artist that exists.
INSERT INTO album (album_name, release_year, artist_id)
VALUES (%(album_name)s, %(release_year)s, %(artist_id)s);

-- name: add_song
-- A new song. UNIQUE (album_id, track_number): one album can't have two "track 1"s.
INSERT INTO song (song_name, duration_seconds, track_number, streams, album_id)
VALUES (%(song_name)s, %(duration_seconds)s, %(track_number)s, 0, %(album_id)s);

-- name: song_for_admin
-- One song with its album and artist, for the "set genres" page.
SELECT s.song_id, s.song_name, s.track_number, a.album_id, a.album_name, ar.artist_name
FROM song s
JOIN album a   ON a.album_id = s.album_id
JOIN artist ar ON ar.artist_id = a.artist_id
WHERE s.song_id = %(song_id)s;

-- name: genres_of_song
-- The genre ids a song has now.
SELECT genre_id
FROM song_genre
WHERE song_id = %(song_id)s;

-- name: clear_song_genres
-- Remove all of a song's genres (before saving the new ones, in one transaction).
DELETE FROM song_genre
WHERE song_id = %(song_id)s;

-- name: add_song_genre
-- Give a song one genre: one row in the junction table song_genre.
INSERT INTO song_genre (song_id, genre_id)
VALUES (%(song_id)s, %(genre_id)s);
