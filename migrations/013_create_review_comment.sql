-- Migration 013 (the website, after Stage 4): comments under reviews.
--
-- A review is a "post" about an album. Other listeners can answer it with comments.
-- One review can have many comments, and one listener can write many comments, so the
-- comments get their own table (a list of comments inside the review row would break 1NF).
--
-- The review table's primary key has two columns (listener_id, album_id). So the
-- foreign key that points to a review has two columns too: reviewer_id + album_id.

CREATE TABLE review_comment (
    comment_id   INT          NOT NULL AUTO_INCREMENT,
    reviewer_id  INT          NOT NULL,   -- the review: the listener who wrote it ...
    album_id     INT          NOT NULL,   -- ... and the album it is about
    listener_id  INT          NOT NULL,   -- who wrote this comment
    comment_text VARCHAR(500) NOT NULL,
    commented_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (comment_id),
    -- A comment needs words. Only spaces is not a comment.
    CONSTRAINT chk_comment_text CHECK (CHAR_LENGTH(TRIM(comment_text)) >= 1),
    -- The comment belongs to one review (a two-column foreign key).
    -- If the review is deleted, its comments are deleted too.
    CONSTRAINT fk_comment_review
        FOREIGN KEY (reviewer_id, album_id) REFERENCES review (listener_id, album_id)
        ON DELETE CASCADE,
    -- If the writer deletes their account, their comments are deleted too.
    CONSTRAINT fk_comment_listener
        FOREIGN KEY (listener_id) REFERENCES listener (listener_id)
        ON DELETE CASCADE
);
