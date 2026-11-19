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


-- ============================================================ Comments under reviews

-- name: album_comments
-- All comments under the reviews of one album, oldest first (a conversation).
-- The website puts each comment under its review (reviewer_id + album_id).
SELECT c.comment_id, c.reviewer_id, c.listener_id, l.username, c.comment_text, c.commented_at
FROM review_comment c
JOIN listener l ON l.listener_id = c.listener_id
WHERE c.album_id = %(album_id)s
ORDER BY c.commented_at, c.comment_id;

-- name: add_comment
-- Answer a review. The two-column foreign key (reviewer_id, album_id) needs a
-- review that exists. CHECK refuses a comment with no words.
INSERT INTO review_comment (reviewer_id, album_id, listener_id, comment_text)
VALUES (%(reviewer_id)s, %(album_id)s, %(listener_id)s, %(comment_text)s);

-- name: comment_by_id
-- One comment (to find its album, and its writer).
SELECT comment_id, reviewer_id, album_id, listener_id
FROM review_comment
WHERE comment_id = %(comment_id)s;

-- name: delete_my_comment
-- Delete my own comment (the listener_id check: only my own).
DELETE FROM review_comment
WHERE comment_id = %(comment_id)s AND listener_id = %(listener_id)s;
