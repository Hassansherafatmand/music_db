-- reports.sql: the admin's Reports page. Each report answers one question with SQL.
-- COUNT(*) OVER () counts all the answers, even when the page shows only 25.


-- name: unreviewed_albums
-- Which albums has nobody reviewed yet? LEFT JOIN keeps every album; an album with
-- no review gets NULL in the review columns, and WHERE ... IS NULL keeps only those.
SELECT a.album_id, a.album_name, a.release_year, ar.artist_name,
       COUNT(*) OVER () AS total_rows
FROM public_album a
JOIN artist ar     ON ar.artist_id = a.artist_id
LEFT JOIN review r ON r.album_id = a.album_id
WHERE r.album_id IS NULL
ORDER BY a.release_year DESC, a.album_id
LIMIT 25;

-- name: loved_never_played
-- Which songs did a listener ♥ but never play? NOT EXISTS is true when the subquery
-- finds no row: no play of this song by this listener.
SELECT l.username, s.song_id, s.song_name, f.added_date,
       COUNT(*) OVER () AS total_rows
FROM favorite f
JOIN listener l ON l.listener_id = f.listener_id
JOIN song s     ON s.song_id = f.song_id
WHERE NOT EXISTS (
    SELECT 1
    FROM play p
    WHERE p.listener_id = f.listener_id AND p.song_id = f.song_id
)
ORDER BY f.added_date DESC, l.username
LIMIT 25;

-- name: album_hits
-- Which songs are the "hits" of their album: more than twice the album's average
-- streams? The subquery is correlated: it runs again for each song, with that
-- song's album_id (s.album_id from the outer query).
SELECT s.song_id, s.song_name, a.album_id, a.album_name, s.streams,
       (SELECT ROUND(AVG(s2.streams)) FROM song s2 WHERE s2.album_id = s.album_id) AS album_average,
       COUNT(*) OVER () AS total_rows
FROM song s
JOIN album a ON a.album_id = s.album_id
WHERE s.streams > 2 * (SELECT AVG(s2.streams) FROM song s2 WHERE s2.album_id = s.album_id)
ORDER BY s.streams DESC
LIMIT 25;

-- name: length_groups
-- Are short or long songs more popular? CASE puts each song in a group, then
-- GROUP BY counts each group.
SELECT CASE
           WHEN duration_seconds < 180  THEN 'Short (under 3 min)'
           WHEN duration_seconds <= 300 THEN 'Medium (3 to 5 min)'
           ELSE 'Long (over 5 min)'
       END AS length_group,
       COUNT(*) AS songs,
       ROUND(AVG(streams)) AS avg_streams,
       COUNT(*) OVER () AS total_rows
FROM song
GROUP BY length_group
ORDER BY MIN(duration_seconds);

-- name: reviewers_who_never_comment
-- Who writes reviews but never comments? EXCEPT takes the first list (reviewers)
-- and removes everybody in the second list (commenters). A set operation.
SELECT l.listener_id, l.username,
       COUNT(*) OVER () AS total_rows
FROM listener l
WHERE l.listener_id IN (
    SELECT listener_id FROM review
    EXCEPT
    SELECT listener_id FROM review_comment
)
ORDER BY l.username
LIMIT 25;

-- name: busiest_hours
-- When do people listen? HOUR() takes the hour out of played_at (0 to 23).
SELECT HOUR(played_at) AS hour, COUNT(*) AS plays,
       COUNT(*) OVER () AS total_rows
FROM play
GROUP BY HOUR(played_at)
ORDER BY hour;
