-- Migration 010 (Stage 4): the pivot. One song can now have MANY genres.
--
-- Before: each song has one genre, in the column song.genre_id.
-- After:  the junction table song_genre, one row for each song-and-genre pair.
-- "Rock, Pop" in one cell would break 1NF, so the genres get their own table.
--
-- 3 steps, so no data is lost.

-- Step 1: make the new junction table.
CREATE TABLE song_genre (
    song_id  INT NOT NULL,
    genre_id INT NOT NULL,

    -- Two-column key: a song gets the same genre only once.
    PRIMARY KEY (song_id, genre_id),

    -- If a song is deleted, its genre rows are deleted too.
    CONSTRAINT fk_song_genre_song
        FOREIGN KEY (song_id) REFERENCES song (song_id)
        ON DELETE CASCADE,

    -- A genre that songs still use cannot be deleted.
    CONSTRAINT fk_song_genre_genre
        FOREIGN KEY (genre_id) REFERENCES genre (genre_id)
);

-- Step 2: move the data. Every song keeps the genre it had.
INSERT INTO song_genre (song_id, genre_id)
SELECT song_id, genre_id
FROM song;

-- Step 3: remove the old column. First its foreign key (by its name), then the column.
ALTER TABLE song DROP FOREIGN KEY fk_song_genre;
ALTER TABLE song DROP COLUMN genre_id;
