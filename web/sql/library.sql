-- library.sql: what belongs to a listener: favorites, plays, playlists, top songs.


-- ============================================================ Favorites (♥)

-- name: add_favorite
-- ♥ a song. The two-column key (listener_id, song_id) allows it only once.
INSERT INTO favorite (listener_id, song_id)
VALUES (%(listener_id)s, %(song_id)s);

-- name: remove_favorite
-- Take the ♥ away again.
DELETE FROM favorite
WHERE listener_id = %(listener_id)s AND song_id = %(song_id)s;

-- name: favorites_of_listener
-- My favorites page: every song I ♥, newest first, with album and artist.
SELECT s.song_id, s.song_name, s.duration_seconds, s.streams,
       a.album_id, a.album_name, ar.artist_id, ar.artist_name,
       f.added_date, 1 AS is_favorite
FROM favorite f
JOIN song s    ON s.song_id = f.song_id
JOIN album a   ON a.album_id = s.album_id
JOIN artist ar ON ar.artist_id = a.artist_id
WHERE f.listener_id = %(listener_id)s
ORDER BY f.added_date DESC, s.song_name;


-- ============================================================ Plays (▶)

-- name: record_play
-- Press Play: one new row in play. played_at gets the date and time by itself.
INSERT INTO play (listener_id, song_id)
VALUES (%(listener_id)s, %(song_id)s);

-- name: now_playing
-- The song in the "now playing" bar at the bottom of the page.
SELECT s.song_id, s.song_name, s.duration_seconds,
       a.album_id, a.album_name, ar.artist_id, ar.artist_name
FROM song s
JOIN album a   ON a.album_id = s.album_id
JOIN artist ar ON ar.artist_id = a.artist_id
WHERE s.song_id = %(song_id)s;


-- ============================================================ Playlists

-- name: playlists_of_listener
-- My playlists, with the number of songs, the total time, and the album ids of the
-- songs in order (for the 4-cover picture on each playlist card).
SELECT p.playlist_id, p.playlist_name, p.created_date,
       COUNT(ps.song_id) AS songs,
       COALESCE(SUM(s.duration_seconds), 0) AS seconds,
       GROUP_CONCAT(s.album_id ORDER BY ps.position SEPARATOR ',') AS album_ids
FROM playlist p
LEFT JOIN playlist_song ps ON ps.playlist_id = p.playlist_id
LEFT JOIN song s           ON s.song_id = ps.song_id
WHERE p.listener_id = %(listener_id)s
GROUP BY p.playlist_id, p.playlist_name, p.created_date
ORDER BY p.created_date DESC, p.playlist_id DESC;

-- name: playlist_names
-- My playlists' names only, for the "Add to playlist" menu next to each song.
SELECT playlist_id, playlist_name
FROM playlist
WHERE listener_id = %(listener_id)s
ORDER BY playlist_name;

-- name: create_playlist
-- A new playlist. UNIQUE (listener_id, playlist_name): no two with the same name.
INSERT INTO playlist (listener_id, playlist_name)
VALUES (%(listener_id)s, %(playlist_name)s);

-- name: playlist_of_owner
-- One playlist, only if it belongs to me (other people's playlists are private).
SELECT playlist_id, playlist_name, created_date
FROM playlist
WHERE playlist_id = %(playlist_id)s AND listener_id = %(listener_id)s;

-- name: playlist_tracks
-- The songs in one playlist, in order (position).
SELECT ps.position, ps.added_date,
       s.song_id, s.song_name, s.duration_seconds, s.streams,
       a.album_id, a.album_name, ar.artist_id, ar.artist_name,
       MAX(f.listener_id IS NOT NULL) AS is_favorite
FROM playlist_song ps
JOIN song s    ON s.song_id = ps.song_id
JOIN album a   ON a.album_id = s.album_id
JOIN artist ar ON ar.artist_id = a.artist_id
LEFT JOIN favorite f ON f.song_id = s.song_id AND f.listener_id = %(listener_id)s
WHERE ps.playlist_id = %(playlist_id)s
GROUP BY ps.position, ps.added_date, s.song_id, s.song_name, s.duration_seconds,
         s.streams, a.album_id, a.album_name, ar.artist_id, ar.artist_name
ORDER BY ps.position;

-- name: next_position
-- The place after the last song (1 for an empty playlist).
SELECT COALESCE(MAX(position), 0) + 1 AS next_position
FROM playlist_song
WHERE playlist_id = %(playlist_id)s;

-- name: add_to_playlist
-- Put a song at the end of a playlist. The two-column key allows each song once.
INSERT INTO playlist_song (playlist_id, song_id, position)
VALUES (%(playlist_id)s, %(song_id)s, %(position)s);

-- name: position_of_song
-- Where a song is in a playlist.
SELECT position
FROM playlist_song
WHERE playlist_id = %(playlist_id)s AND song_id = %(song_id)s;

-- name: song_at_position
-- Which song is at a place in a playlist.
SELECT song_id, position
FROM playlist_song
WHERE playlist_id = %(playlist_id)s AND position = %(position)s;

-- name: set_position
-- Move one song to a place. (Moving up/down swaps two songs, in a transaction.)
UPDATE playlist_song
SET position = %(position)s
WHERE playlist_id = %(playlist_id)s AND song_id = %(song_id)s;

-- name: remove_from_playlist
-- Take a song out of a playlist.
DELETE FROM playlist_song
WHERE playlist_id = %(playlist_id)s AND song_id = %(song_id)s;

-- name: close_gap
-- After a song is removed, the songs after it move up one place (no gap: 1, 2, 3...).
-- ORDER BY position: move the lowest first, so two songs never share a place.
UPDATE playlist_song
SET position = position - 1
WHERE playlist_id = %(playlist_id)s AND position > %(position)s
ORDER BY position;

-- name: rename_playlist
-- Give a playlist a new name (only my own).
UPDATE playlist
SET playlist_name = %(playlist_name)s
WHERE playlist_id = %(playlist_id)s AND listener_id = %(listener_id)s;

-- name: delete_playlist
-- Delete a playlist (only my own). ON DELETE CASCADE removes its playlist_song rows.
DELETE FROM playlist
WHERE playlist_id = %(playlist_id)s AND listener_id = %(listener_id)s;


-- ============================================================ My top songs
-- (This page replaces the nightly email: the same kind of query, shown on the website.)

-- name: my_stats
-- My numbers: plays, different songs, minutes listened, first and last play.
SELECT COUNT(*) AS plays,
       COUNT(DISTINCT p.song_id) AS different_songs,
       COALESCE(SUM(s.duration_seconds), 0) AS seconds,
       MIN(p.played_at) AS first_play,
       MAX(p.played_at) AS last_play
FROM play p
JOIN song s ON s.song_id = p.song_id
WHERE p.listener_id = %(listener_id)s;

-- name: my_top_songs
-- My 10 most played songs.
SELECT s.song_id, s.song_name, s.duration_seconds,
       a.album_id, a.album_name, ar.artist_id, ar.artist_name,
       COUNT(*) AS plays
FROM play p
JOIN song s    ON s.song_id = p.song_id
JOIN album a   ON a.album_id = s.album_id
JOIN artist ar ON ar.artist_id = a.artist_id
WHERE p.listener_id = %(listener_id)s
GROUP BY s.song_id, s.song_name, s.duration_seconds,
         a.album_id, a.album_name, ar.artist_id, ar.artist_name
ORDER BY plays DESC, MAX(p.played_at) DESC
LIMIT 10;

-- name: my_top_genres
-- The genres I play most (a song with 2 genres counts for both).
SELECT g.genre_id, g.genre_name, COUNT(*) AS plays
FROM play p
JOIN song_genre sg ON sg.song_id = p.song_id
JOIN genre g       ON g.genre_id = sg.genre_id
WHERE p.listener_id = %(listener_id)s
GROUP BY g.genre_id, g.genre_name
ORDER BY plays DESC
LIMIT 5;

-- name: my_plays_by_weekday
-- How many plays on each day of the week (DAYOFWEEK: 1 = Sunday ... 7 = Saturday).
SELECT DAYOFWEEK(played_at) AS weekday, COUNT(*) AS plays
FROM play
WHERE listener_id = %(listener_id)s
GROUP BY DAYOFWEEK(played_at)
ORDER BY weekday;

-- name: my_latest_day
-- My last listening day: what the nightly job (scripts/nightly_top_songs.sql) finds
-- for one day. The subquery finds the day, the outer query counts each song's plays.
SELECT s.song_id, s.song_name, a.album_id, ar.artist_name,
       DATE(MAX(p.played_at)) AS day, COUNT(*) AS plays
FROM play p
JOIN song s    ON s.song_id = p.song_id
JOIN album a   ON a.album_id = s.album_id
JOIN artist ar ON ar.artist_id = a.artist_id
WHERE p.listener_id = %(listener_id)s
  AND DATE(p.played_at) = (SELECT MAX(DATE(p2.played_at))
                           FROM play p2
                           WHERE p2.listener_id = %(listener_id)s)
GROUP BY s.song_id, s.song_name, a.album_id, ar.artist_name
ORDER BY plays DESC, s.song_name;

-- name: my_recent_plays
-- My last 8 plays.
SELECT p.played_at, s.song_id, s.song_name, a.album_id, a.album_name, ar.artist_name
FROM play p
JOIN song s    ON s.song_id = p.song_id
JOIN album a   ON a.album_id = s.album_id
JOIN artist ar ON ar.artist_id = a.artist_id
WHERE p.listener_id = %(listener_id)s
ORDER BY p.played_at DESC, p.play_id DESC
LIMIT 8;
