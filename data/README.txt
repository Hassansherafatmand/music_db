music_db advanced synthetic SQL practice dataset

Import order:
1. artist.csv
2. album.csv
3. genre.csv
4. song.csv

Row counts:
- artist.csv: 50 artists
- album.csv: 184 albums
- genre.csv: 15 genres
- song.csv: 956 songs

Relationships:
- artist 1 -> many album through album.artist_id
- album 1 -> many song through song.album_id
- genre 1 -> many song through song.genre_id

Practice design:
- album rows are intentionally scattered; the same artist_id is not grouped together.
- song rows are intentionally scattered; the same album_id is not grouped together.
- artists have different album counts, including artists with zero albums.
- albums have different song counts, including albums with zero songs.
- genre 15 intentionally has zero songs for LEFT JOIN / NOT EXISTS practice.
- states, years, song names, album names, genres, and stream counts repeat in useful ways.
- stream counts include zero, repeated values, low values, and very high values.
- IDs and all foreign-key references are internally consistent.

This dataset is intended to support a full SQL course, including:
- DDL: CREATE, ALTER, DROP, constraints, keys, indexes, views
- DML: INSERT, UPDATE, DELETE, transactions
- DQL: SELECT, WHERE, ORDER BY, DISTINCT, GROUP BY, HAVING
- JOINs: INNER, LEFT, RIGHT, self-style comparisons, multi-table joins
- advanced querying: subqueries, correlated subqueries, CTEs, window functions, CASE, set operations

Notes:
- All names and data are synthetic.
- Do not assume CSV row order has meaning. Use ORDER BY when order matters.
