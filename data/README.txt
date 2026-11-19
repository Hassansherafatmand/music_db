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

Stage 4 (more genres per song, and reviews), import after migration 010:
10. song_genre_extra.csv: 180 extra genres (song_id + genre_id) for 141 songs;
    39 songs get two extra. Migration 010 already copied every song's first genre
    into song_genre, so these are second and third genres.
11. review.csv: 90 reviews (listener_id + album_id, 1 to 5 stars) of 77 albums;
    15 have no text (empty -> NULL), and 7 listeners have none

The content pack (for the website), import after migrations 012 to 016:
scripts/import_content.sql loads data/content/*.csv. scripts/make_content.py made these
files from the files above (a fixed random seed, so it makes the same files every time).
The files above are NOT changed, so Stages 1 to 4 stay as they are.
12. content/album.csv: 12 albums for the 5 artists who had none (one plays Classical)
13. content/song.csv: 243 songs: 156 fill up the albums that had 0 or 2 songs (now every
    album has 3 to 10), and 87 are on the new albums
14. content/song_genre.csv: 273 rows: the new songs' genres, plus 12 old songs that get
    Classical as a second genre (now 37 songs are Classical)
15. content/listener.csv: 80 listeners (ids 41 to 120). Each one has a "taste": 1 to 3
    favorite genres. The taste is not in any file: it shows in what they love and play.
16. content/favorite.csv: 1,757 favorites, mostly from each listener's genres
17. content/playlist.csv and playlist_song.csv: 90 playlists with 862 songs
18. content/play.csv: 5,836 plays up to 2026-11-18 (the old listeners keep listening
    after 2026-11-09, too)
19. content/review.csv: 334 reviews with real-sounding text (37 stars only); review and
    comment texts are in "quotes", because they can have commas. (3, 101) stays free for
    queries/showcase.sql.
20. content/review_comment.csv: 432 comments under the reviews (sometimes the reviewer
    answers back)

Totals after the content pack: 50 artists, 196 albums, 1,199 songs, 15 genres,
120 listeners, 2,005 favorites, 133 playlists, 8,292 plays, 424 reviews, 432 comments.

Passwords (for the website):
- listener.csv and content/listener.csv have no passwords. scripts/demo_passwords.sql
  (after the content pack) gives every practice listener the same demo password: music330

Relationships:
- artist 1 -> many album through album.artist_id
- album 1 -> many song through song.album_id
- genre 1 -> many song through song.genre_id (Stages 1-3; Stage 4 moves this into
  song_genre, so song and genre become many-to-many)
- listener 1 -> many favorite, playlist, play and review through listener_id
- playlist 1 -> many playlist_song through playlist_song.playlist_id
- song 1 -> many favorite, playlist_song, play and song_genre through song_id
- album 1 -> many review through review.album_id
- review 1 -> many review_comment through (reviewer_id, album_id), a two-column key
- listener 1 -> many review_comment through review_comment.listener_id

Practice design (the files above; the content pack fills the gaps for the website):
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
