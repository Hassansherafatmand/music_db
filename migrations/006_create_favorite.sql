-- Migration 006 (Stage 2): create the favorite table.
-- One row for "this listener loves this song" (the ♥ button).
-- A junction table: listener and song are many-to-many.

CREATE TABLE favorite (
    listener_id INT  NOT NULL,
    song_id     INT  NOT NULL,
    added_date  DATE NOT NULL DEFAULT (CURRENT_DATE),  -- the day they pressed ♥

    -- Two-column key: a listener can love the same song only once.
    PRIMARY KEY (listener_id, song_id),

    -- If a listener deletes their account, their favorites are deleted too.
    CONSTRAINT fk_favorite_listener
        FOREIGN KEY (listener_id) REFERENCES listener (listener_id)
        ON DELETE CASCADE,

    -- A song that someone loves cannot be deleted.
    CONSTRAINT fk_favorite_song
        FOREIGN KEY (song_id) REFERENCES song (song_id)
);
