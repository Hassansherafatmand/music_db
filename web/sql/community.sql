-- community.sql: the listeners (the Listeners page and each listener's profile).
-- Emails are private: these statements never show them.


-- ============================================================ The Listeners page

-- name: browse_listeners
-- Every listener with their numbers (the view listener_activity) and their top
-- genre. The CTE counts each listener's ♥ in each genre; ROW_NUMBER() numbers the
-- genres of each listener (PARTITION BY listener_id), and place 1 is their top genre.
WITH genre_love AS (
    SELECT f.listener_id, sg.genre_id, COUNT(*) AS loves,
           ROW_NUMBER() OVER (PARTITION BY f.listener_id
                              ORDER BY COUNT(*) DESC, sg.genre_id) AS place
    FROM favorite f
    JOIN song_genre sg ON sg.song_id = f.song_id
    GROUP BY f.listener_id, sg.genre_id
)
SELECT l.listener_id, l.username, l.joined_date,
       la.favorite_count, la.play_count, la.review_count, la.comment_count,
       g.genre_id AS top_genre_id, g.genre_name AS top_genre,
       COUNT(*) OVER () AS total_rows
FROM listener l
JOIN listener_activity la ON la.listener_id = l.listener_id
LEFT JOIN genre_love gl   ON gl.listener_id = l.listener_id AND gl.place = 1
LEFT JOIN genre g         ON g.genre_id = gl.genre_id
{where}
ORDER BY {order}
LIMIT %(limit)s OFFSET %(offset)s;

-- where: joined
YEAR(l.joined_date) = %(joined)s
-- where: genre
gl.genre_id = %(genre)s
-- sort: favorites
la.favorite_count DESC, l.username
-- sort: reviews
la.review_count DESC, l.username
-- sort: plays
la.play_count DESC, l.username
-- sort: comments
la.comment_count DESC, l.username
-- sort: newest
l.joined_date DESC, l.listener_id DESC
-- sort: name
l.username

-- name: joined_year_choices
-- The years in which listeners joined, for the "Joined" filter.
SELECT DISTINCT YEAR(joined_date) AS joined_year
FROM listener
ORDER BY joined_year DESC;


-- ============================================================ One listener's profile

-- name: profile
-- One listener, with their numbers (no email: it is private).
SELECT l.listener_id, l.username, l.joined_date,
       la.favorite_count, la.playlist_count, la.play_count, la.review_count, la.comment_count
FROM listener l
JOIN listener_activity la ON la.listener_id = l.listener_id
WHERE l.username = %(username)s;

-- name: top_genres
-- A listener's taste: the genres of the songs they ♥, in percent.
-- SUM(COUNT(*)) OVER () is the total of all their genres (a window function).
SELECT g.genre_id, g.genre_name, COUNT(*) AS loves,
       ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 0) AS percent
FROM favorite f
JOIN song_genre sg ON sg.song_id = f.song_id
JOIN genre g       ON g.genre_id = sg.genre_id
WHERE f.listener_id = %(listener_id)s
GROUP BY g.genre_id, g.genre_name
ORDER BY loves DESC, g.genre_name
LIMIT 5;

-- name: favorites
-- The 15 songs this listener loved last, with "♥ by me" for the visitor.
SELECT s.song_id, s.song_name, s.duration_seconds, s.streams,
       a.album_id, a.album_name, ar.artist_id, ar.artist_name, f.added_date,
       EXISTS (SELECT 1 FROM favorite mine
               WHERE mine.song_id = s.song_id AND mine.listener_id = %(me)s) AS is_favorite
FROM favorite f
JOIN song s    ON s.song_id = f.song_id
JOIN album a   ON a.album_id = s.album_id
JOIN artist ar ON ar.artist_id = a.artist_id
WHERE f.listener_id = %(listener_id)s
ORDER BY f.added_date DESC, s.song_id
LIMIT 15;

-- name: reviews
-- The reviews this listener wrote, newest first, with how many comments each got.
SELECT r.album_id, a.album_name, ar.artist_name, r.stars, r.review_text, r.review_date,
       (SELECT COUNT(*) FROM review_comment c
        WHERE c.reviewer_id = r.listener_id AND c.album_id = r.album_id) AS comment_count
FROM review r
JOIN album a   ON a.album_id = r.album_id
JOIN artist ar ON ar.artist_id = a.artist_id
WHERE r.listener_id = %(listener_id)s
ORDER BY r.review_date DESC, r.album_id;

-- name: comments
-- The 10 comments this listener wrote last, and whose review they answered.
SELECT c.comment_id, c.comment_text, c.commented_at, c.album_id, a.album_name,
       rl.username AS reviewer
FROM review_comment c
JOIN album a     ON a.album_id = c.album_id
JOIN listener rl ON rl.listener_id = c.reviewer_id
WHERE c.listener_id = %(listener_id)s
ORDER BY c.commented_at DESC, c.comment_id DESC
LIMIT 10;

-- name: last_30_days
-- How many songs this listener played on each of the last 30 days (up to the newest
-- play on the website). The recursive CTE makes all 30 days, so days without plays
-- show 0 (the LEFT JOIN keeps them, and COUNT(p.play_id) counts no rows as 0).
WITH RECURSIVE last_play AS (
    SELECT DATE(MAX(played_at)) AS last_day
    FROM play
),
days AS (
    SELECT last_day - INTERVAL 29 DAY AS day, last_day
    FROM last_play
    UNION ALL
    SELECT day + INTERVAL 1 DAY, last_day
    FROM days
    WHERE day < last_day
)
SELECT d.day, COUNT(p.play_id) AS plays
FROM days d
LEFT JOIN play p ON p.listener_id = %(listener_id)s
                AND p.played_at >= d.day AND p.played_at < d.day + INTERVAL 1 DAY
GROUP BY d.day
ORDER BY d.day;

-- name: songs_we_both_love
-- The songs that the visitor AND this listener both ♥. INTERSECT keeps only the
-- song ids that are in both lists (a set operation, like in math).
SELECT s.song_id, s.song_name, a.album_id, a.album_name, ar.artist_id, ar.artist_name
FROM song s
JOIN album a   ON a.album_id = s.album_id
JOIN artist ar ON ar.artist_id = a.artist_id
WHERE s.song_id IN (
    SELECT song_id FROM favorite WHERE listener_id = %(me)s
    INTERSECT
    SELECT song_id FROM favorite WHERE listener_id = %(listener_id)s
)
ORDER BY s.song_name, s.song_id;
