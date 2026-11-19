-- reviews.sql: listeners review albums with 1 to 5 stars (the review table).


-- name: album_reviews
-- The reviews of one album, newest first, with the writer's username.
SELECT r.listener_id, l.username, r.stars, r.review_text, r.review_date
FROM review r
JOIN listener l ON l.listener_id = r.listener_id
WHERE r.album_id = %(album_id)s
ORDER BY r.review_date DESC, l.username;

-- name: star_counts
-- How many reviews gave each number of stars (for the little bar chart).
SELECT stars, COUNT(*) AS reviews
FROM review
WHERE album_id = %(album_id)s
GROUP BY stars;

-- name: my_review
-- My own review of this album, if I wrote one.
SELECT stars, review_text, review_date
FROM review
WHERE listener_id = %(listener_id)s AND album_id = %(album_id)s;

-- name: save_review
-- Write a review, or change mine. The key (listener_id, album_id) allows one review
-- per album, so a second one UPDATEs the first. CHECK refuses stars outside 1 to 5.
INSERT INTO review (listener_id, album_id, stars, review_text)
VALUES (%(listener_id)s, %(album_id)s, %(stars)s, %(review_text)s) AS new
ON DUPLICATE KEY UPDATE stars       = new.stars,
                        review_text = new.review_text,
                        review_date = CURRENT_DATE;

-- name: delete_review
-- Delete my review of this album.
DELETE FROM review
WHERE listener_id = %(listener_id)s AND album_id = %(album_id)s;
