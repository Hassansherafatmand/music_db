-- Migration 001 (Stage 1): create the artist table.
-- One row for each artist.

CREATE TABLE artist (
    artist_id    INT          NOT NULL AUTO_INCREMENT,
    artist_name  VARCHAR(100) NOT NULL,
    origin_state CHAR(2),                 -- US state, like 'WA'. Can be empty (NULL).
    debut_year   YEAR         NOT NULL,   -- the year the artist started

    PRIMARY KEY (artist_id)
);
