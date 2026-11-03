-- Migration 003 (Stage 1): create the genre table.
-- One row for each genre, like Rock or Pop.

CREATE TABLE genre (
    genre_id   INT         NOT NULL AUTO_INCREMENT,
    genre_name VARCHAR(50) NOT NULL,

    PRIMARY KEY (genre_id),

    -- No two genres with the same name.
    CONSTRAINT uq_genre_name UNIQUE (genre_name)
);
