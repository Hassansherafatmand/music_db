-- catalog.sql: the pages everyone can see (home, songs, albums, artists, genres, search).
-- Each statement has a name. The website runs it by that name (see web/db.py).
-- %(name)s is a parameter: the value is sent separately, so it can't change the SQL.
--
-- Visitors only see finished albums: the public pages use the view public_album
-- (albums with 3 or more songs, migration 015) instead of the album table.


-- ============================================================ Home page

-- name: site_stats
-- How many artists, albums, songs, listeners and plays the website has.
SELECT (SELECT COUNT(*) FROM artist)                  AS artists,
       (SELECT COUNT(*) FROM public_album)            AS albums,
       (SELECT SUM(song_count) FROM public_album)     AS songs,
       (SELECT COUNT(*) FROM listener)                AS listeners,
       (SELECT COUNT(*) FROM play)                    AS plays,
       (SELECT COUNT(*) FROM review)                  AS reviews,
       (SELECT COUNT(*) FROM review_comment)          AS comments;

-- name: most_played_songs
-- The 10 songs with the most plays on our website (rows in play).
SELECT s.song_id, s.song_name, s.duration_seconds,
       a.album_id, a.album_name, ar.artist_id, ar.artist_name,
       COUNT(*) AS plays
FROM play p
JOIN song s         ON s.song_id = p.song_id
JOIN public_album a ON a.album_id = s.album_id
JOIN artist ar      ON ar.artist_id = a.artist_id
GROUP BY s.song_id, s.song_name, s.duration_seconds,
         a.album_id, a.album_name, ar.artist_id, ar.artist_name
ORDER BY plays DESC, s.song_id
LIMIT 10;

-- name: most_loved_songs
-- The 10 songs that the most listeners ♥ (the view song_popularity counts them).
SELECT s.song_id, s.song_name, s.duration_seconds,
       a.album_id, a.album_name, ar.artist_id, ar.artist_name,
       sp.love_count
FROM song_popularity sp
JOIN song s         ON s.song_id = sp.song_id
JOIN public_album a ON a.album_id = s.album_id
JOIN artist ar      ON ar.artist_id = a.artist_id
WHERE sp.love_count > 0
ORDER BY sp.love_count DESC, s.song_id
LIMIT 10;

-- name: most_loved_albums
-- The 6 albums whose songs have the most ♥ together (SUM of each song's loves).
SELECT a.album_id, a.album_name, a.release_year, ar.artist_id, ar.artist_name,
       SUM(sp.love_count) AS loves
FROM public_album a
JOIN artist ar          ON ar.artist_id = a.artist_id
JOIN song s             ON s.album_id = a.album_id
JOIN song_popularity sp ON sp.song_id = s.song_id
GROUP BY a.album_id, a.album_name, a.release_year, ar.artist_id, ar.artist_name
ORDER BY loves DESC, a.album_id
LIMIT 6;

-- name: newest_albums
-- The 6 newest albums, with their artist.
SELECT a.album_id, a.album_name, a.release_year, ar.artist_id, ar.artist_name
FROM public_album a
JOIN artist ar ON ar.artist_id = a.artist_id
ORDER BY a.release_year DESC, a.album_id DESC
LIMIT 6;

-- name: top_rated_albums
-- Albums with the best average stars, with 3 or more reviews (the view album_rating).
SELECT a.album_id, a.album_name, ar.artist_id, ar.artist_name,
       rt.avg_stars, rt.review_count AS reviews
FROM album_rating rt
JOIN public_album a ON a.album_id = rt.album_id
JOIN artist ar      ON ar.artist_id = a.artist_id
WHERE rt.review_count >= 3
ORDER BY rt.avg_stars DESC, rt.review_count DESC
LIMIT 6;

-- name: whats_new
-- The "What's new" feed: the newest things listeners did. Four different tables are
-- stacked into one list with UNION ALL (each part must have the same columns). Each
-- part keeps only its 5 newest rows (ORDER BY ... LIMIT inside the brackets), so the
-- feed is a mix. It is calculated, not stored: there is no "feed" table.
SELECT kind, happened_at, listener_id, username, item_id, item_name, album_id, stars
FROM (
    (SELECT 'loved' AS kind, f.added_date AS happened_at, l.listener_id, l.username,
            s.song_id AS item_id, s.song_name AS item_name, s.album_id, NULL AS stars
     FROM favorite f
     JOIN listener l ON l.listener_id = f.listener_id
     JOIN song s     ON s.song_id = f.song_id
     ORDER BY f.added_date DESC, f.song_id DESC
     LIMIT 5)
    UNION ALL
    (SELECT 'reviewed', r.review_date, l.listener_id, l.username,
            a.album_id, a.album_name, a.album_id, r.stars
     FROM review r
     JOIN listener l ON l.listener_id = r.listener_id
     JOIN album a    ON a.album_id = r.album_id
     ORDER BY r.review_date DESC
     LIMIT 5)
    UNION ALL
    (SELECT 'commented', c.commented_at, l.listener_id, l.username,
            a.album_id, a.album_name, a.album_id, NULL
     FROM review_comment c
     JOIN listener l ON l.listener_id = c.listener_id
     JOIN album a    ON a.album_id = c.album_id
     ORDER BY c.commented_at DESC
     LIMIT 5)
    UNION ALL
    (SELECT 'joined', l.joined_date, l.listener_id, l.username, NULL, NULL, NULL, NULL
     FROM listener l
     ORDER BY l.joined_date DESC
     LIMIT 3)
) AS feed
ORDER BY happened_at DESC, kind
LIMIT 12;

-- name: genres_with_counts
-- Every genre and how many songs have it (LEFT JOIN keeps genres with 0 songs).
SELECT g.genre_id, g.genre_name, COUNT(sg.song_id) AS songs
FROM genre g
LEFT JOIN song_genre sg ON sg.genre_id = g.genre_id
GROUP BY g.genre_id, g.genre_name
ORDER BY g.genre_name;


-- ============================================================ Choices for the filters

-- name: genre_choices
-- Every genre, for the "Genre" filter.
SELECT genre_id, genre_name
FROM genre
ORDER BY genre_name;

-- name: state_choices
-- The states that artists come from (DISTINCT: each state once).
SELECT DISTINCT origin_state
FROM artist
WHERE origin_state IS NOT NULL
ORDER BY origin_state;

-- name: decade_choices
-- The decades that have albums: 1984 -> 1980 (FLOOR rounds down).
SELECT DISTINCT FLOOR(release_year / 10) * 10 AS decade
FROM public_album
ORDER BY decade;

-- name: artist_choices
-- Every artist, for the "Artist" filter.
SELECT artist_id, artist_name
FROM artist
ORDER BY artist_name;


-- ============================================================ Songs (a list with filters)

-- name: browse_songs
-- All songs, with the filters and the sort the visitor chose. The ♥ and ▶ numbers
-- are counted with COUNT(*) in subqueries. COUNT(*) OVER () counts all the rows that
-- match (before LIMIT), so the page knows how many pages there are.
SELECT s.song_id, s.song_name, s.duration_seconds, s.streams,
       a.album_id, a.album_name, a.release_year,
       ar.artist_id, ar.artist_name, ar.origin_state,
       (SELECT COUNT(*) FROM favorite f WHERE f.song_id = s.song_id) AS love_count,
       (SELECT COUNT(*) FROM play p     WHERE p.song_id = s.song_id) AS play_count,
       (SELECT GROUP_CONCAT(CONCAT(g.genre_id, ':', g.genre_name)
                            ORDER BY g.genre_name SEPARATOR '|')
        FROM song_genre sg JOIN genre g ON g.genre_id = sg.genre_id
        WHERE sg.song_id = s.song_id) AS genres,
       EXISTS (SELECT 1 FROM favorite f
               WHERE f.song_id = s.song_id AND f.listener_id = %(listener_id)s) AS is_favorite,
       COUNT(*) OVER () AS total_rows
FROM song s
JOIN public_album a ON a.album_id = s.album_id
JOIN artist ar      ON ar.artist_id = a.artist_id
{where}
ORDER BY {order}
LIMIT %(limit)s OFFSET %(offset)s;

-- where: genre
EXISTS (SELECT 1 FROM song_genre sg WHERE sg.song_id = s.song_id AND sg.genre_id = %(genre)s)
-- where: artist
ar.artist_id = %(artist)s
-- where: state
ar.origin_state = %(state)s
-- where: decade
a.release_year BETWEEN %(decade)s AND %(decade)s + 9
-- where: short
s.duration_seconds < 180
-- where: medium
s.duration_seconds BETWEEN 180 AND 300
-- where: long
s.duration_seconds > 300
-- sort: loved
love_count DESC, s.song_id
-- sort: played
play_count DESC, s.song_id
-- sort: streams
s.streams DESC, s.song_id
-- sort: newest
a.release_year DESC, a.album_id DESC, s.track_number
-- sort: name
s.song_name IS NULL, s.song_name, s.song_id
-- sort: length
s.duration_seconds DESC, s.song_id


-- ============================================================ Albums (a list with filters)

-- name: browse_albums
-- All albums with their review numbers. LEFT JOIN keeps albums with no reviews
-- (then AVG is NULL). GROUP BY makes one row per album, and HAVING can filter on
-- the AVG, like "4 stars or more" (WHERE can't, because it runs before GROUP BY).
SELECT a.album_id, a.album_name, a.release_year, a.song_count,
       ar.artist_id, ar.artist_name,
       COUNT(r.listener_id)  AS review_count,
       ROUND(AVG(r.stars), 1) AS avg_stars,
       (SELECT COUNT(*) FROM favorite f JOIN song s ON s.song_id = f.song_id
        WHERE s.album_id = a.album_id) AS love_count,
       COUNT(*) OVER () AS total_rows
FROM public_album a
JOIN artist ar     ON ar.artist_id = a.artist_id
LEFT JOIN review r ON r.album_id = a.album_id
{where}
GROUP BY a.album_id, a.album_name, a.release_year, a.song_count, ar.artist_id, ar.artist_name
{having}
ORDER BY {order}
LIMIT %(limit)s OFFSET %(offset)s;

-- where: genre
EXISTS (SELECT 1 FROM song s JOIN song_genre sg ON sg.song_id = s.song_id
        WHERE s.album_id = a.album_id AND sg.genre_id = %(genre)s)
-- where: decade
a.release_year BETWEEN %(decade)s AND %(decade)s + 9
-- where: state
ar.origin_state = %(state)s
-- having: stars
AVG(r.stars) >= %(stars)s
-- sort: rated
avg_stars IS NULL, avg_stars DESC, review_count DESC
-- sort: reviews
review_count DESC, a.album_id
-- sort: loved
love_count DESC, a.album_id
-- sort: newest
a.release_year DESC, a.album_id DESC
-- sort: name
a.album_name IS NULL, a.album_name, a.album_id


-- ============================================================ Artists (a list with filters)

-- name: browse_artists
-- Every artist with their numbers. Each number is counted first, in its own subquery
-- in FROM (a "derived table", grouped by artist), and then joined to the artist.
-- Counting before joining keeps the numbers right: joining artist -> song -> favorite
-- first would repeat each song once per fan, and SUM(streams) would be too big.
-- COUNT(DISTINCT ...) counts each fan only once, even if they love many songs.
SELECT ar.artist_id, ar.artist_name, ar.origin_state, ar.debut_year,
       COALESCE(music.album_count, 0) AS album_count,
       COALESCE(music.streams, 0)     AS streams,
       COALESCE(fans.fan_count, 0)    AS fan_count,
       COUNT(*) OVER () AS total_rows
FROM artist ar
LEFT JOIN (SELECT a.artist_id, COUNT(DISTINCT a.album_id) AS album_count,
                  SUM(s.streams) AS streams
           FROM public_album a
           JOIN song s ON s.album_id = a.album_id
           GROUP BY a.artist_id) AS music ON music.artist_id = ar.artist_id
LEFT JOIN (SELECT a.artist_id, COUNT(DISTINCT f.listener_id) AS fan_count
           FROM favorite f
           JOIN song s  ON s.song_id = f.song_id
           JOIN album a ON a.album_id = s.album_id
           GROUP BY a.artist_id) AS fans ON fans.artist_id = ar.artist_id
{where}
ORDER BY {order}
LIMIT %(limit)s OFFSET %(offset)s;

-- where: state
ar.origin_state = %(state)s
-- where: decade
ar.debut_year BETWEEN %(decade)s AND %(decade)s + 9
-- sort: name
ar.artist_name, ar.artist_id
-- sort: state
ar.origin_state IS NULL, ar.origin_state, ar.artist_name
-- sort: albums
album_count DESC, ar.artist_name
-- sort: fans
fan_count DESC, ar.artist_name
-- sort: streams
streams DESC, ar.artist_name
-- sort: debut
ar.debut_year, ar.artist_name


-- ============================================================ One artist

-- name: artist_by_id
-- One artist.
SELECT artist_id, artist_name, origin_state, debut_year
FROM artist
WHERE artist_id = %(artist_id)s;

-- name: albums_by_artist
-- One artist's albums, newest first, with how many songs each has. Visitors see
-- albums with 3 or more songs (min_songs = 3); the admin sees all (min_songs = 0).
SELECT a.album_id, a.album_name, a.release_year, COUNT(s.song_id) AS songs
FROM album a
LEFT JOIN song s ON s.album_id = a.album_id
WHERE a.artist_id = %(artist_id)s
GROUP BY a.album_id, a.album_name, a.release_year
HAVING COUNT(s.song_id) >= %(min_songs)s
ORDER BY a.release_year DESC, a.album_id;

-- name: popular_songs_by_artist
-- One artist's 5 songs with the most streams (on other music services).
SELECT s.song_id, s.song_name, s.duration_seconds, s.streams,
       a.album_id, a.album_name,
       GROUP_CONCAT(CONCAT(g.genre_id, ':', g.genre_name)
                    ORDER BY g.genre_name SEPARATOR '|') AS genres,
       MAX(f.listener_id IS NOT NULL) AS is_favorite
FROM song s
JOIN public_album a ON a.album_id = s.album_id
LEFT JOIN song_genre sg ON sg.song_id = s.song_id
LEFT JOIN genre g       ON g.genre_id = sg.genre_id
LEFT JOIN favorite f    ON f.song_id = s.song_id AND f.listener_id = %(listener_id)s
WHERE a.artist_id = %(artist_id)s
GROUP BY s.song_id, s.song_name, s.duration_seconds, s.streams, a.album_id, a.album_name
ORDER BY s.streams DESC
LIMIT 5;


-- ============================================================ One album

-- name: album_by_id
-- One album, with its artist, its number of songs, and its rating (the view album_rating).
SELECT a.album_id, a.album_name, a.release_year,
       ar.artist_id, ar.artist_name,
       COALESCE(rt.review_count, 0) AS reviews,
       rt.avg_stars,
       (SELECT COUNT(*) FROM song s WHERE s.album_id = a.album_id) AS song_count
FROM album a
JOIN artist ar            ON ar.artist_id = a.artist_id
LEFT JOIN album_rating rt ON rt.album_id = a.album_id
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

-- name: album_lovers
-- The listeners who ♥ songs on this album, and how many of its songs each one loves.
SELECT l.listener_id, l.username, COUNT(*) AS loved_songs
FROM favorite f
JOIN song s     ON s.song_id = f.song_id
JOIN listener l ON l.listener_id = f.listener_id
WHERE s.album_id = %(album_id)s
GROUP BY l.listener_id, l.username
ORDER BY loved_songs DESC, l.username;


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
JOIN song s         ON s.song_id = sg.song_id
JOIN public_album a ON a.album_id = s.album_id
JOIN artist ar      ON ar.artist_id = a.artist_id
LEFT JOIN favorite f ON f.song_id = s.song_id AND f.listener_id = %(listener_id)s
WHERE sg.genre_id = %(genre_id)s
GROUP BY s.song_id, s.song_name, s.duration_seconds, s.streams,
         a.album_id, a.album_name, ar.artist_id, ar.artist_name
ORDER BY s.streams DESC
LIMIT 100;


-- ============================================================ Search
-- The search uses the FULLTEXT indexes (migration 016): MATCH ... AGAINST finds
-- words in any position and gives each row a score (how well it matches).
-- words looks like '+golden* +train*': every word must be there (+), and * means
-- "starts with". If no word can be used (too short, or too common, like "the"),
-- the website uses the LIKE statements below instead.

-- name: search_songs
-- Songs whose name has all the search words (FULLTEXT), best match first.
SELECT s.song_id, s.song_name, s.duration_seconds, s.streams,
       a.album_id, a.album_name, ar.artist_id, ar.artist_name,
       EXISTS (SELECT 1 FROM favorite f
               WHERE f.song_id = s.song_id AND f.listener_id = %(listener_id)s) AS is_favorite,
       MATCH (s.song_name) AGAINST (%(words)s IN BOOLEAN MODE) AS score
FROM song s
JOIN public_album a ON a.album_id = s.album_id
JOIN artist ar      ON ar.artist_id = a.artist_id
WHERE MATCH (s.song_name) AGAINST (%(words)s IN BOOLEAN MODE)
ORDER BY score DESC, s.streams DESC
LIMIT 50;

-- name: search_artists
-- Artists whose name has all the search words (FULLTEXT).
SELECT artist_id, artist_name, origin_state, debut_year
FROM artist
WHERE MATCH (artist_name) AGAINST (%(words)s IN BOOLEAN MODE)
ORDER BY MATCH (artist_name) AGAINST (%(words)s IN BOOLEAN MODE) DESC, artist_name
LIMIT 12;

-- name: search_albums
-- Albums whose name has all the search words (FULLTEXT), with their artist.
SELECT a.album_id, a.album_name, a.release_year, ar.artist_id, ar.artist_name
FROM public_album a
JOIN album al  ON al.album_id = a.album_id
JOIN artist ar ON ar.artist_id = a.artist_id
WHERE MATCH (al.album_name) AGAINST (%(words)s IN BOOLEAN MODE)
ORDER BY MATCH (al.album_name) AGAINST (%(words)s IN BOOLEAN MODE) DESC, a.release_year DESC
LIMIT 12;

-- name: search_songs_like
-- Songs whose name contains the search text (LIKE '%text%'). Used for short words.
SELECT s.song_id, s.song_name, s.duration_seconds, s.streams,
       a.album_id, a.album_name, ar.artist_id, ar.artist_name,
       EXISTS (SELECT 1 FROM favorite f
               WHERE f.song_id = s.song_id AND f.listener_id = %(listener_id)s) AS is_favorite
FROM song s
JOIN public_album a ON a.album_id = s.album_id
JOIN artist ar      ON ar.artist_id = a.artist_id
WHERE s.song_name LIKE %(pattern)s
ORDER BY s.streams DESC
LIMIT 50;

-- name: search_artists_like
-- Artists whose name contains the search text.
SELECT artist_id, artist_name, origin_state, debut_year
FROM artist
WHERE artist_name LIKE %(pattern)s
ORDER BY artist_name
LIMIT 12;

-- name: search_albums_like
-- Albums whose name contains the search text, with their artist.
SELECT a.album_id, a.album_name, a.release_year, ar.artist_id, ar.artist_name
FROM public_album a
JOIN artist ar ON ar.artist_id = a.artist_id
WHERE a.album_name LIKE %(pattern)s
ORDER BY a.release_year DESC
LIMIT 12;
