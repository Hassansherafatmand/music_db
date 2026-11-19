-- catalog.sql: the pages everyone can see (home, artists, albums, genres, search).
-- Each statement has a name. The website runs it by that name (see web/db.py).
-- %(name)s is a parameter: the value is sent separately, so it can't change the SQL.


-- ============================================================ Home page

-- name: site_stats
-- How many artists, albums, songs, listeners and plays the website has.
SELECT (SELECT COUNT(*) FROM artist)   AS artists,
       (SELECT COUNT(*) FROM album)    AS albums,
       (SELECT COUNT(*) FROM song)     AS songs,
       (SELECT COUNT(*) FROM listener) AS listeners,
       (SELECT COUNT(*) FROM play)     AS plays;

-- name: most_played_songs
-- The 10 songs with the most plays on our website (rows in play).
SELECT s.song_id, s.song_name, s.duration_seconds,
       a.album_id, a.album_name, ar.artist_id, ar.artist_name,
       COUNT(*) AS plays
FROM play p
JOIN song s    ON s.song_id = p.song_id
JOIN album a   ON a.album_id = s.album_id
JOIN artist ar ON ar.artist_id = a.artist_id
GROUP BY s.song_id, s.song_name, s.duration_seconds,
         a.album_id, a.album_name, ar.artist_id, ar.artist_name
ORDER BY plays DESC, s.song_id
LIMIT 10;

-- name: newest_albums
-- The 6 newest albums, with their artist.
SELECT a.album_id, a.album_name, a.release_year, ar.artist_id, ar.artist_name
FROM album a
JOIN artist ar ON ar.artist_id = a.artist_id
ORDER BY a.release_year DESC, a.album_id DESC
LIMIT 6;

-- name: top_rated_albums
-- Albums with the best average stars (only albums with 2 or more reviews).
SELECT a.album_id, a.album_name, ar.artist_id, ar.artist_name,
       ROUND(AVG(r.stars), 1) AS avg_stars, COUNT(*) AS reviews
FROM review r
JOIN album a   ON a.album_id = r.album_id
JOIN artist ar ON ar.artist_id = a.artist_id
GROUP BY a.album_id, a.album_name, ar.artist_id, ar.artist_name
HAVING COUNT(*) >= 2
ORDER BY avg_stars DESC, reviews DESC
LIMIT 6;

-- name: genres_with_counts
-- Every genre and how many songs have it (LEFT JOIN keeps genres with 0 songs).
SELECT g.genre_id, g.genre_name, COUNT(sg.song_id) AS songs
FROM genre g
LEFT JOIN song_genre sg ON sg.genre_id = g.genre_id
GROUP BY g.genre_id, g.genre_name
ORDER BY g.genre_name;


-- ============================================================ Artists

-- name: all_artists
-- Every artist, with their number of albums and their total streams.
SELECT ar.artist_id, ar.artist_name, ar.origin_state, ar.debut_year,
       COUNT(DISTINCT a.album_id) AS albums,
       COALESCE(SUM(s.streams), 0) AS streams
FROM artist ar
LEFT JOIN album a ON a.artist_id = ar.artist_id
LEFT JOIN song s  ON s.album_id = a.album_id
GROUP BY ar.artist_id, ar.artist_name, ar.origin_state, ar.debut_year
ORDER BY ar.artist_name;

-- name: artist_by_id
-- One artist.
SELECT artist_id, artist_name, origin_state, debut_year
FROM artist
WHERE artist_id = %(artist_id)s;

-- name: albums_by_artist
-- One artist's albums, newest first, with how many songs each has.
SELECT a.album_id, a.album_name, a.release_year, COUNT(s.song_id) AS songs
FROM album a
LEFT JOIN song s ON s.album_id = a.album_id
WHERE a.artist_id = %(artist_id)s
GROUP BY a.album_id, a.album_name, a.release_year
ORDER BY a.release_year DESC, a.album_id;

-- name: popular_songs_by_artist
-- One artist's 5 songs with the most streams (on other music services).
SELECT s.song_id, s.song_name, s.duration_seconds, s.streams,
       a.album_id, a.album_name,
       GROUP_CONCAT(CONCAT(g.genre_id, ':', g.genre_name)
                    ORDER BY g.genre_name SEPARATOR '|') AS genres,
       MAX(f.listener_id IS NOT NULL) AS is_favorite
FROM song s
JOIN album a ON a.album_id = s.album_id
LEFT JOIN song_genre sg ON sg.song_id = s.song_id
LEFT JOIN genre g       ON g.genre_id = sg.genre_id
LEFT JOIN favorite f    ON f.song_id = s.song_id AND f.listener_id = %(listener_id)s
WHERE a.artist_id = %(artist_id)s
GROUP BY s.song_id, s.song_name, s.duration_seconds, s.streams, a.album_id, a.album_name
ORDER BY s.streams DESC
LIMIT 5;


-- ============================================================ Albums

-- name: album_by_id
-- One album, with its artist and its review numbers.
SELECT a.album_id, a.album_name, a.release_year,
       ar.artist_id, ar.artist_name,
       (SELECT COUNT(*) FROM review r WHERE r.album_id = a.album_id) AS reviews,
       (SELECT ROUND(AVG(r.stars), 1) FROM review r WHERE r.album_id = a.album_id) AS avg_stars
FROM album a
JOIN artist ar ON ar.artist_id = a.artist_id
WHERE a.album_id = %(album_id)s;

-- name: album_tracks
-- The songs on one album, in track order, with their genres (song_genre) and a
-- "loved by me" flag (favorite). Genres come packed as '3:Pop|7:Rock'.
SELECT s.song_id, s.song_name, s.track_number, s.duration_seconds, s.streams,
       GROUP_CONCAT(CONCAT(g.genre_id, ':', g.genre_name)
                    ORDER BY g.genre_name SEPARATOR '|') AS genres,
       MAX(f.listener_id IS NOT NULL) AS is_favorite
FROM song s
LEFT JOIN song_genre sg ON sg.song_id = s.song_id
LEFT JOIN genre g       ON g.genre_id = sg.genre_id
LEFT JOIN favorite f    ON f.song_id = s.song_id AND f.listener_id = %(listener_id)s
WHERE s.album_id = %(album_id)s
GROUP BY s.song_id, s.song_name, s.track_number, s.duration_seconds, s.streams
ORDER BY s.track_number;


-- ============================================================ Genres

-- name: genre_by_id
-- One genre.
SELECT genre_id, genre_name
FROM genre
WHERE genre_id = %(genre_id)s;

-- name: songs_in_genre
-- The 100 songs with the most streams in one genre (through song_genre, Stage 4).
SELECT s.song_id, s.song_name, s.duration_seconds, s.streams,
       a.album_id, a.album_name, ar.artist_id, ar.artist_name,
       MAX(f.listener_id IS NOT NULL) AS is_favorite
FROM song_genre sg
JOIN song s    ON s.song_id = sg.song_id
JOIN album a   ON a.album_id = s.album_id
JOIN artist ar ON ar.artist_id = a.artist_id
LEFT JOIN favorite f ON f.song_id = s.song_id AND f.listener_id = %(listener_id)s
WHERE sg.genre_id = %(genre_id)s
GROUP BY s.song_id, s.song_name, s.duration_seconds, s.streams,
         a.album_id, a.album_name, ar.artist_id, ar.artist_name
ORDER BY s.streams DESC
LIMIT 100;


-- ============================================================ Search

-- name: search_songs
-- Songs whose name contains the search words (LIKE '%words%').
SELECT s.song_id, s.song_name, s.duration_seconds, s.streams,
       a.album_id, a.album_name, ar.artist_id, ar.artist_name,
       MAX(f.listener_id IS NOT NULL) AS is_favorite
FROM song s
JOIN album a   ON a.album_id = s.album_id
JOIN artist ar ON ar.artist_id = a.artist_id
LEFT JOIN favorite f ON f.song_id = s.song_id AND f.listener_id = %(listener_id)s
WHERE s.song_name LIKE %(pattern)s
GROUP BY s.song_id, s.song_name, s.duration_seconds, s.streams,
         a.album_id, a.album_name, ar.artist_id, ar.artist_name
ORDER BY s.streams DESC
LIMIT 50;

-- name: search_artists
-- Artists whose name contains the search words.
SELECT artist_id, artist_name, origin_state, debut_year
FROM artist
WHERE artist_name LIKE %(pattern)s
ORDER BY artist_name
LIMIT 12;

-- name: search_albums
-- Albums whose name contains the search words, with their artist.
SELECT a.album_id, a.album_name, a.release_year, ar.artist_id, ar.artist_name
FROM album a
JOIN artist ar ON ar.artist_id = a.artist_id
WHERE a.album_name LIKE %(pattern)s
ORDER BY a.release_year DESC
LIMIT 12;
