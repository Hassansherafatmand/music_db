-- Migration 008 (Stage 3): create the playlist_song table.
-- One row for "this song is in this playlist, at this place".
-- A junction table with extra data: playlist and song are many-to-many.

CREATE TABLE playlist_song (
    playlist_id INT  NOT NULL,
    song_id     INT  NOT NULL,
    position    INT  NOT NULL,                        -- the order: 1, 2, 3...
    added_date  DATE NOT NULL DEFAULT (CURRENT_DATE),

    -- Two-column key: a song is in a playlist only once.
    PRIMARY KEY (playlist_id, song_id),

    -- Two songs cannot have the same place in one playlist.
    CONSTRAINT uq_playlist_song_position UNIQUE (playlist_id, position),
    CONSTRAINT chk_playlist_song_position CHECK (position >= 1),

    -- If a playlist is deleted, its rows here are deleted too.
    CONSTRAINT fk_playlist_song_playlist
        FOREIGN KEY (playlist_id) REFERENCES playlist (playlist_id)
        ON DELETE CASCADE,

    -- A song that is in a playlist cannot be deleted.
    CONSTRAINT fk_playlist_song_song
        FOREIGN KEY (song_id) REFERENCES song (song_id)
);
