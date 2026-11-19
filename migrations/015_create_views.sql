-- Migration 015 (the website, after Stage 4): views.
--
-- A view is a saved SELECT with a name. You use it like a table, but it stores no
-- data: MySQL runs its SELECT every time. So a view never gets out of date, and it
-- fits our rule "don't save what you can calculate" (no copy of the numbers).
--
-- The website uses these views in many pages, so the same calculation is written once.


-- How each album is rated: the number of reviews and the average stars.
-- (Only albums with at least one review have a row.)
CREATE VIEW album_rating AS
SELECT album_id,
       COUNT(*)              AS review_count,
       ROUND(AVG(stars), 1)  AS avg_stars
FROM review
GROUP BY album_id;


-- How popular each song is on our website: how many listeners ♥ it, and how many
-- times it was played. Every song has a row (also songs with 0).
CREATE VIEW song_popularity AS
SELECT s.song_id,
       (SELECT COUNT(*) FROM favorite f WHERE f.song_id = s.song_id) AS love_count,
       (SELECT COUNT(*) FROM play p     WHERE p.song_id = s.song_id) AS play_count
FROM song s;


-- How much each listener did. Every listener has a row.
CREATE VIEW listener_activity AS
SELECT l.listener_id,
       (SELECT COUNT(*) FROM favorite f       WHERE f.listener_id = l.listener_id) AS favorite_count,
       (SELECT COUNT(*) FROM playlist p       WHERE p.listener_id = l.listener_id) AS playlist_count,
       (SELECT COUNT(*) FROM play p           WHERE p.listener_id = l.listener_id) AS play_count,
       (SELECT COUNT(*) FROM review r         WHERE r.listener_id = l.listener_id) AS review_count,
       (SELECT COUNT(*) FROM review_comment c WHERE c.listener_id = l.listener_id) AS comment_count
FROM listener l;


-- The albums that visitors can see: albums with 3 or more songs.
-- An album with fewer songs is not finished yet (the admin is still adding its songs),
-- so the public pages use this view instead of the album table.
CREATE VIEW public_album AS
SELECT a.album_id, a.album_name, a.release_year, a.artist_id,
       COUNT(s.song_id) AS song_count
FROM album a
JOIN song s ON s.album_id = a.album_id
GROUP BY a.album_id, a.album_name, a.release_year, a.artist_id
HAVING COUNT(s.song_id) >= 3;
