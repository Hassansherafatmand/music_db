-- Migration 009 (Stage 3): create the play table.
-- One row each time a listener presses Play (there is no real sound).
-- A history table: the same listener can play the same song many times,
-- so it needs its own key (play_id), not a two-column key.

CREATE TABLE play (
    play_id     INT      NOT NULL AUTO_INCREMENT,
    listener_id INT      NOT NULL,
    song_id     INT      NOT NULL,
    played_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,  -- the date and time

    PRIMARY KEY (play_id),

    -- If a listener deletes their account, their plays are deleted too.
    CONSTRAINT fk_play_listener
        FOREIGN KEY (listener_id) REFERENCES listener (listener_id)
        ON DELETE CASCADE,

    -- A song that was played cannot be deleted.
    CONSTRAINT fk_play_song
        FOREIGN KEY (song_id) REFERENCES song (song_id)
);
