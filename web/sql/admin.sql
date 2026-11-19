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


-- ============================================================ Dashboard

-- name: unfinished_albums
-- Albums with fewer than 3 songs: visitors can't see them yet (the view public_album).
-- LEFT JOIN keeps albums with 0 songs; HAVING filters after counting.
SELECT a.album_id, a.album_name, a.release_year, ar.artist_name, COUNT(s.song_id) AS songs
FROM album a
JOIN artist ar   ON ar.artist_id = a.artist_id
LEFT JOIN song s ON s.album_id = a.album_id
GROUP BY a.album_id, a.album_name, a.release_year, ar.artist_name
HAVING COUNT(s.song_id) < 3
ORDER BY a.album_id DESC;

-- name: audit_counts
-- How many rows the audit log has, and when the last one was written.
SELECT COUNT(*) AS entries, MAX(done_at) AS last_entry
FROM audit_log;


-- ============================================================ Listeners (CRUD)

-- name: browse_listeners
-- Every listener with their email and numbers, for the admin. Search with LIKE.
SELECT l.listener_id, l.username, l.email, l.joined_date,
       la.favorite_count, la.playlist_count, la.play_count, la.review_count, la.comment_count,
       COUNT(*) OVER () AS total_rows
FROM listener l
JOIN listener_activity la ON la.listener_id = l.listener_id
{where}
ORDER BY {order}
LIMIT %(limit)s OFFSET %(offset)s;

-- where: search
(l.username LIKE %(pattern)s OR l.email LIKE %(pattern)s)
-- sort: newest
l.listener_id DESC
-- sort: oldest
l.listener_id
-- sort: name
l.username
-- sort: active
la.play_count DESC, l.username

-- name: listener_for_admin
-- One listener, with their email and numbers.
SELECT l.listener_id, l.username, l.email, l.joined_date,
       l.password_hash IS NOT NULL AS has_password,
       la.favorite_count, la.playlist_count, la.play_count, la.review_count, la.comment_count
FROM listener l
JOIN listener_activity la ON la.listener_id = l.listener_id
WHERE l.listener_id = %(listener_id)s;

-- name: update_listener
-- Change a listener's username and email. UNIQUE refuses names that are taken.
UPDATE listener
SET username = %(username)s, email = %(email)s
WHERE listener_id = %(listener_id)s;

-- name: delete_review
-- Moderation: delete any review. ON DELETE CASCADE deletes its comments too.
DELETE FROM review
WHERE listener_id = %(listener_id)s AND album_id = %(album_id)s;

-- name: delete_comment
-- Moderation: delete any comment.
DELETE FROM review_comment
WHERE comment_id = %(comment_id)s;


-- ============================================================ Edit and delete music

-- name: update_artist
-- Change an artist.
UPDATE artist
SET artist_name = %(artist_name)s, origin_state = %(origin_state)s, debut_year = %(debut_year)s
WHERE artist_id = %(artist_id)s;

-- name: artist_uses
-- Before deleting an artist: how many albums point to them (fk_album_artist, RESTRICT).
SELECT COUNT(*) AS albums
FROM album
WHERE artist_id = %(artist_id)s;

-- name: delete_artist
-- Delete an artist. MySQL refuses if an album still points to them (RESTRICT).
DELETE FROM artist
WHERE artist_id = %(artist_id)s;

-- name: album_for_admin
-- One album, to edit it.
SELECT a.album_id, a.album_name, a.release_year, a.artist_id, ar.artist_name
FROM album a
JOIN artist ar ON ar.artist_id = a.artist_id
WHERE a.album_id = %(album_id)s;

-- name: update_album
-- Change an album. The foreign key needs an artist that exists.
UPDATE album
SET album_name = %(album_name)s, release_year = %(release_year)s, artist_id = %(artist_id)s
WHERE album_id = %(album_id)s;

-- name: album_uses
-- Before deleting an album: what points to it. Songs (fk_song_album) and reviews
-- (fk_review_album) both use RESTRICT, so MySQL refuses while there are any.
SELECT (SELECT COUNT(*) FROM song   WHERE album_id = %(album_id)s) AS songs,
       (SELECT COUNT(*) FROM review WHERE album_id = %(album_id)s) AS reviews;

-- name: delete_album
-- Delete an album. MySQL refuses if songs or reviews still point to it.
DELETE FROM album
WHERE album_id = %(album_id)s;

-- name: song_details_for_admin
-- One song, to edit it.
SELECT s.song_id, s.song_name, s.duration_seconds, s.track_number, s.streams,
       s.album_id, a.album_name, ar.artist_name
FROM song s
JOIN album a   ON a.album_id = s.album_id
JOIN artist ar ON ar.artist_id = a.artist_id
WHERE s.song_id = %(song_id)s;

-- name: update_song
-- Change a song. UNIQUE (album_id, track_number) still applies.
UPDATE song
SET song_name = %(song_name)s, duration_seconds = %(duration_seconds)s,
    track_number = %(track_number)s, album_id = %(album_id)s
WHERE song_id = %(song_id)s;

-- name: song_uses
-- Before deleting a song: what points to it. favorite, playlist_song and play use
-- RESTRICT (MySQL says no while there are rows). song_genre uses CASCADE (its rows
-- are deleted with the song).
SELECT (SELECT COUNT(*) FROM favorite      WHERE song_id = %(song_id)s) AS favorites,
       (SELECT COUNT(*) FROM playlist_song WHERE song_id = %(song_id)s) AS playlist_rows,
       (SELECT COUNT(*) FROM play          WHERE song_id = %(song_id)s) AS plays,
       (SELECT COUNT(*) FROM song_genre    WHERE song_id = %(song_id)s) AS genres;

-- name: delete_song
-- Delete a song. MySQL refuses if a favorite, playlist or play still points to it.
DELETE FROM song
WHERE song_id = %(song_id)s;


-- ============================================================ The audit log

-- name: audit_log
-- The newest 200 rows of the audit log (written by the triggers of migration 014).
SELECT audit_id, action, table_name, row_id, details, done_by, done_at
FROM audit_log
ORDER BY done_at DESC, audit_id DESC
LIMIT 200;
