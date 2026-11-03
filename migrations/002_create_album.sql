-- Migration 002 (Stage 1): create the album table.
-- One row for each album. Each album belongs to exactly one artist.

CREATE TABLE album (
    album_id     INT          NOT NULL AUTO_INCREMENT,
    album_name   VARCHAR(100),            -- can be empty (NULL)
    release_year YEAR         NOT NULL,
    artist_id    INT          NOT NULL,   -- the artist who made the album

    PRIMARY KEY (album_id),

    -- An album must point to an artist that exists.
    -- An artist that still has albums cannot be deleted.
    CONSTRAINT fk_album_artist
        FOREIGN KEY (artist_id) REFERENCES artist (artist_id)
);
