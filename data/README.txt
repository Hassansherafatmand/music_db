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

Stage 2 (listeners), import after the files above:
5. listener.csv: 40 listeners (made-up usernames, emails at example.com)
6. favorite.csv: 248 favorites (listener_id + song_id); 5 listeners have none

Stage 3 (playlists and plays), import after the files above:
7. playlist.csv: 43 playlists; 20 listeners have none, 1 playlist is empty,
   and 11 playlist names are used by more than one listener
8. playlist_song.csv: 319 rows (playlist_id + song_id + position); 1 to 15 songs
   per playlist
9. play.csv: 2,456 plays from 2026-10-01 to 2026-11-09 (112 on 2026-11-09);
   5 listeners have none, and the same listener can play a song many times

Relationships:
- artist 1 -> many album through album.artist_id
- album 1 -> many song through song.album_id
- genre 1 -> many song through song.genre_id
- listener 1 -> many favorite, playlist and play through listener_id
- playlist 1 -> many playlist_song through playlist_song.playlist_id
- song 1 -> many favorite, playlist_song and play through song_id

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
