-- charts.sql: the Charts page. Window functions and CTEs (WITH).
--
-- A window function (like RANK() OVER (...)) looks at a group of rows but, unlike
-- GROUP BY, keeps every row. PARTITION BY says which rows belong together.
-- A CTE (WITH name AS (...)) is a query with a name, used by the query after it.
-- It makes a long query easier to read, step by step.


-- name: top_songs_per_genre
-- The 3 most played songs in each genre. Step 1 counts the plays of each song in
-- each genre. Step 2 numbers the songs inside each genre (PARTITION BY genre_id),
-- most plays first. RANK gives the same place to a tie, so a genre can show 4.
WITH genre_plays AS (
    SELECT sg.genre_id, s.song_id, s.song_name, s.album_id, COUNT(*) AS plays
    FROM play p
    JOIN song s        ON s.song_id = p.song_id
    JOIN song_genre sg ON sg.song_id = s.song_id
    GROUP BY sg.genre_id, s.song_id, s.song_name, s.album_id
),
ranked AS (
    SELECT gp.*,
           RANK() OVER (PARTITION BY gp.genre_id ORDER BY gp.plays DESC) AS place
    FROM genre_plays gp
)
SELECT g.genre_id, g.genre_name, r.place, r.song_id, r.song_name, r.album_id,
       a.album_name, ar.artist_name, r.plays
FROM ranked r
JOIN genre g        ON g.genre_id = r.genre_id
JOIN public_album a ON a.album_id = r.album_id
JOIN artist ar      ON ar.artist_id = a.artist_id
WHERE r.place <= 3
ORDER BY g.genre_name, r.place, r.song_name;

-- name: best_album_per_decade
-- The most loved album of each decade. ROW_NUMBER numbers the albums inside each
-- decade (1 = most loves), and the outer query keeps number 1.
WITH album_loves AS (
    SELECT a.album_id, a.album_name, a.release_year, a.artist_id,
           FLOOR(a.release_year / 10) * 10 AS decade,
           SUM(sp.love_count) AS loves
    FROM public_album a
    JOIN song s             ON s.album_id = a.album_id
    JOIN song_popularity sp ON sp.song_id = s.song_id
    GROUP BY a.album_id, a.album_name, a.release_year, a.artist_id
),
numbered AS (
    SELECT al.*,
           ROW_NUMBER() OVER (PARTITION BY al.decade ORDER BY al.loves DESC, al.album_id) AS place
    FROM album_loves al
)
SELECT n.decade, n.album_id, n.album_name, n.release_year, ar.artist_id, ar.artist_name, n.loves
FROM numbered n
JOIN artist ar ON ar.artist_id = n.artist_id
WHERE n.place = 1
ORDER BY n.decade;

-- name: plays_per_day
-- Plays on each of the last 30 days (up to the newest play). A recursive CTE makes
-- the list of days: it starts with one day and adds 1 day until the last one. So a
-- day with 0 plays still has a row (GROUP BY alone would skip it). The running total
-- adds up the plays day by day: SUM(...) OVER (ORDER BY day).
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
),
per_day AS (
    SELECT DATE(played_at) AS day, COUNT(*) AS plays
    FROM play
    WHERE played_at >= (SELECT last_day - INTERVAL 29 DAY FROM last_play)
    GROUP BY DATE(played_at)
)
SELECT d.day,
       COALESCE(pd.plays, 0) AS plays,
       SUM(COALESCE(pd.plays, 0)) OVER (ORDER BY d.day) AS running_total
FROM days d
LEFT JOIN per_day pd ON pd.day = d.day
ORDER BY d.day;

-- name: genre_share
-- Each genre's share of all plays, in percent. SUM(COUNT(*)) OVER () is the total
-- of all genres, so every row can divide by it.
SELECT g.genre_id, g.genre_name, COUNT(*) AS plays,
       ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS percent
FROM play p
JOIN song_genre sg ON sg.song_id = p.song_id
JOIN genre g       ON g.genre_id = sg.genre_id
GROUP BY g.genre_id, g.genre_name
ORDER BY plays DESC;
