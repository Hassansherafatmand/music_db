-- showcase.sql: the review feature, from start to end.
-- It shows that the database works. Exam question 2 uses this file together with
-- migrations/011_create_review.sql (the table with the primary key and foreign keys).
-- It ends with a DELETE, so it can run again and again.

-- 1. INSERT (changes data): listener 3 gives album 101 four stars.
INSERT INTO review (listener_id, album_id, stars, review_text)
VALUES (3, 101, 4, 'Great guitar sound');

-- 2. JOIN of 4 tables, with WHERE: every 5-star review, with names instead of ids.
SELECT l.username, a.album_name, ar.artist_name, r.stars
FROM review r
JOIN listener l ON l.listener_id = r.listener_id
JOIN album a    ON a.album_id = r.album_id
JOIN artist ar  ON ar.artist_id = a.artist_id
WHERE r.stars = 5;

-- 3. GROUP BY with COUNT and AVG: the average stars of each artist.
SELECT ar.artist_name, COUNT(*) AS reviews, ROUND(AVG(r.stars), 1) AS avg_stars
FROM review r
JOIN album a   ON a.album_id = r.album_id
JOIN artist ar ON ar.artist_id = a.artist_id
GROUP BY ar.artist_id, ar.artist_name
ORDER BY avg_stars DESC;

-- 4. DELETE with WHERE (changes data): listener 3 removes the review.
DELETE FROM review
WHERE listener_id = 3 AND album_id = 101;
