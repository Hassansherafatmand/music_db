-- Migration 007 (Stage 3): create the playlist table.
-- One row for each playlist. Each playlist has exactly one owner (a listener).

CREATE TABLE playlist (
    playlist_id   INT         NOT NULL AUTO_INCREMENT,
    listener_id   INT         NOT NULL,                        -- the owner
    playlist_name VARCHAR(50) NOT NULL,
    created_date  DATE        NOT NULL DEFAULT (CURRENT_DATE),

    PRIMARY KEY (playlist_id),

    -- One listener cannot have two playlists with the same name.
    CONSTRAINT uq_playlist_owner_name UNIQUE (listener_id, playlist_name),

    -- If a listener deletes their account, their playlists are deleted too.
    CONSTRAINT fk_playlist_listener
        FOREIGN KEY (listener_id) REFERENCES listener (listener_id)
        ON DELETE CASCADE
);
