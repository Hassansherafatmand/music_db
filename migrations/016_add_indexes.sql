-- Migration 016 (the website, after Stage 4): indexes for the website's searches.
--
-- An index is like the index at the back of a book: MySQL can jump to the right rows
-- instead of reading the whole table. MySQL already has an index for every primary
-- key, every UNIQUE constraint and every foreign key. These are for the filters,
-- sorts and searches on the website. The Lab page (/lab/speed) shows the difference
-- with EXPLAIN.
--
-- An index costs a little: more disk space, and INSERT/UPDATE get a little slower,
-- because MySQL must update the index too. So we only add the ones we use.

-- Sort songs by name, and find names that START with some letters: LIKE 'sun%'.
-- (LIKE '%sun%' can't use it: the index is sorted by the first letters.)
CREATE INDEX idx_song_name ON song (song_name);

-- Filter artists by state (the Artists and Songs pages).
CREATE INDEX idx_artist_state ON artist (origin_state);

-- Filter albums by decade: release_year BETWEEN 1990 AND 1999.
CREATE INDEX idx_album_year ON album (release_year);

-- Plays in a time range (the Charts page: plays per day).
CREATE INDEX idx_play_played_at ON play (played_at);

-- FULLTEXT indexes are for searching words inside text: MATCH (...) AGAINST (...).
-- The search page uses them. They find whole words (and word beginnings with *),
-- in any position, and they sort the results by how well they match.
CREATE FULLTEXT INDEX ft_song_name   ON song (song_name);
CREATE FULLTEXT INDEX ft_album_name  ON album (album_name);
CREATE FULLTEXT INDEX ft_artist_name ON artist (artist_name);
