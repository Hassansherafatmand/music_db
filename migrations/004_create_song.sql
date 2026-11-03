-- Migration 004 (Stage 1): create the song table.
-- One row for each song. Each song is on exactly one album and has one genre.

CREATE TABLE song (
    song_id          INT          NOT NULL AUTO_INCREMENT,
    song_name        VARCHAR(100),           -- can be empty (NULL)
    duration_seconds INT          NOT NULL,  -- how long the song is
    track_number     INT          NOT NULL,  -- the place of the song on its album
    streams          BIGINT       NOT NULL,  -- streams on other music services (BIGINT: INT stops at about 2.1 billion)
    album_id         INT          NOT NULL,
    genre_id         INT          NOT NULL,

    PRIMARY KEY (song_id),

    -- One album cannot have two songs with the same track number.
    CONSTRAINT uq_song_album_track UNIQUE (album_id, track_number),

    -- A song must point to an album and a genre that exist.
    CONSTRAINT fk_song_album
        FOREIGN KEY (album_id) REFERENCES album (album_id),
    CONSTRAINT fk_song_genre
        FOREIGN KEY (genre_id) REFERENCES genre (genre_id)
);
