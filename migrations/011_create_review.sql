-- Migration 011 (Stage 4): create the review table.
-- One row for "this listener gives this album 1 to 5 stars".

CREATE TABLE review (
    listener_id INT          NOT NULL,
    album_id    INT          NOT NULL,
    stars       TINYINT      NOT NULL,
    review_text VARCHAR(500),                                  -- optional
    review_date DATE         NOT NULL DEFAULT (CURRENT_DATE),

    -- Two-column key: one review per listener per album.
    PRIMARY KEY (listener_id, album_id),

    -- The database refuses 0 stars or 6 stars.
    CONSTRAINT chk_review_stars CHECK (stars BETWEEN 1 AND 5),

    -- If a listener deletes their account, their reviews are deleted too.
    CONSTRAINT fk_review_listener
        FOREIGN KEY (listener_id) REFERENCES listener (listener_id)
        ON DELETE CASCADE,

    -- An album with reviews cannot be deleted.
    CONSTRAINT fk_review_album
        FOREIGN KEY (album_id) REFERENCES album (album_id)
);
