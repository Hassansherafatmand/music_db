# music_db — Music Database Design

## Purpose

The purpose of `music_db` is to store information about music artists in the USA, their albums, songs, and genres.

This database is designed for practicing:

- **DDL** — `CREATE`, `ALTER`, `DROP`, constraints, primary keys, foreign keys
- **DML** — `INSERT`, `UPDATE`, `DELETE`
- **DQL** — `SELECT`, `WHERE`, `ORDER BY`, `GROUP BY`, `HAVING`, joins, subqueries, and window functions

---

## Important Terms

### Entity

An **entity** is a real-world thing that we want to store information about.

For this database, the main entities are:

- Artist
- Album
- Song
- Genre

When we implement an entity in SQL, it usually becomes a **table**.

Example:

```text
Entity: Artist
        ↓
Table: artists
```

### Table

A **table** is the SQL structure that stores data for an entity.

For example:

```text
artists
albums
songs
genres
```

### Schema

A **schema** describes the overall structure of the database.

It includes:

- Tables
- Columns
- Primary keys
- Foreign keys
- Relationships between tables

So:

```text
Entity = real-world concept
Table  = SQL implementation of that concept
Schema = overall database structure
```

---

# System Design

The current database contains four main entities:

```text
ARTIST
ALBUM
SONG
GENRE
```

The relationship **types are still one-to-many**, but the current practice data allows some parent rows to have zero children:

```text
ARTIST  1 -------- 0..many  ALBUM

ALBUM   1 -------- 0..many  SONG

GENRE   1 -------- 0..many  SONG
```

Read these in both directions:

```text
One artist can have zero, one, or many albums.
Each album belongs to exactly one artist.

One album can have zero, one, or many songs.
Each song belongs to exactly one album.

One genre can have zero, one, or many songs.
Each song belongs to exactly one genre.
```

---

## Design Rules

### Rule 1

One artist can have **zero, one, or many albums**.

```text
ARTIST
   1
   |
   | has
   |
  0..many
ALBUM
```

This lets us keep artists that currently have no album and practice `LEFT JOIN`.

### Rule 2

One album belongs to **exactly one artist**.

`album.artist_id` is `NOT NULL` and is a foreign key to `artist.artist_id`.

### Rule 3

One album can contain **zero, one, or many songs**.

```text
ALBUM
   1
   |
   | contains
   |
  0..many
SONG
```

This lets us keep albums that currently have no songs and practice `LEFT JOIN`.

### Rule 4

One song belongs to **exactly one album**.

Because `song.album_id` is `NOT NULL`, a song cannot exist in the current schema without an album.

### Rule 5

One song belongs to **exactly one genre**.

Because `song.genre_id` is `NOT NULL`, a song cannot exist in the current schema without a genre.

A genre, however, can have zero songs.

### Rule 6 — NULL values do not change relationships

Some descriptive columns are allowed to be `NULL`, such as:

```text
artist.origin_state
album.album_name
song.song_name
```

These `NULL` values are useful for SQL practice, but they do **not** change the table relationships.

The relationships are controlled by the foreign-key columns:

```text
album.artist_id
song.album_id
song.genre_id
```

---

# Schema Design

## 1. Artist

The `artist` table stores information about each artist.

```text
ARTIST
-------------------------
artist_id
artist_name
origin_state
debut_year
```

### Column meanings

- `artist_id` — unique identifier for the artist
- `artist_name` — name of the artist
- `origin_state` — U.S. state where the artist originated; may be `NULL`
- `debut_year` — year the artist began or debuted

### Primary Key

```text
artist_id
```

Example data:

```text
artist_id | artist_name | origin_state | debut_year
----------|-------------|--------------|-----------
1         | Metallica   | CA           | 1981
2         | Nirvana     | WA           | 1987
3         | Aerosmith   | MA           | 1970
```

---

## 2. Album

The `album` table stores albums.

```text
ALBUM
-------------------------
album_id
album_name
release_year
artist_id
```

### Column meanings

- `album_id` — unique identifier for the album
- `album_name` — album title; may be `NULL` in the practice data
- `release_year` — year the album was released
- `artist_id` — identifies which artist owns the album

### Primary Key

```text
album_id
```

### Foreign Key

```text
artist_id
```

The foreign key connects:

```text
album.artist_id
        ↓
artist.artist_id
```

Example:

```text
Artist:
artist_id = 1
artist_name = Metallica

Album:
album_id = 101
album_name = Master of Puppets
artist_id = 1
```

The value `1` connects the album to Metallica.

---

## 3. Song

The `song` table stores songs contained in albums.

```text
SONG
-------------------------
song_id
song_name
duration_seconds
track_number
streams
album_id
genre_id
```

### Column meanings

- `song_id` — unique identifier for the song
- `song_name` — song title; may be `NULL` in the practice data
- `duration_seconds` — song duration in seconds
- `track_number` — position of the song on the album
- `streams` — number of streams
- `album_id` — identifies the album containing the song
- `genre_id` — identifies the song's genre

### Primary Key

```text
song_id
```

### Foreign Keys

```text
album_id
genre_id
```

Connections:

```text
song.album_id
      ↓
album.album_id
```

and:

```text
song.genre_id
      ↓
genre.genre_id
```

Example data:

```text
song_id | song_name          | duration_seconds | track_number | streams   | album_id | genre_id
--------|--------------------|------------------|--------------|-----------|----------|---------
1001    | Battery            | 312              | 1            | 250000000 | 101      | 1
1002    | Master of Puppets  | 515              | 2            | 500000000 | 101      | 1
1003    | Disposable Heroes  | 496              | 5            | 150000000 | 101      | 1
```

The `streams` column is useful for practicing aggregate queries such as:

```sql
SUM(streams)
AVG(streams)
MAX(streams)
MIN(streams)
```

---

## 4. Genre

The `genre` table stores music genres.

```text
GENRE
-------------------------
genre_id
genre_name
```

### Column meanings

- `genre_id` — unique identifier for the genre
- `genre_name` — name of the genre

### Primary Key

```text
genre_id
```

Example data:

```text
genre_id | genre_name
---------|-----------
1        | Metal
2        | Rock
3        | Grunge
4        | Pop
5        | Hip-Hop
```

---

# Overall Database Design

```text
ARTIST
-------------------------
artist_id       PK
artist_name
origin_state    NULL allowed
debut_year

        1
        |
        | has
        |
      0..many

ALBUM
-------------------------
album_id        PK
album_name      NULL allowed
release_year
artist_id       FK, NOT NULL

        1
        |
        | contains
        |
      0..many

SONG
-------------------------
song_id         PK
song_name       NULL allowed
duration_seconds
track_number
streams
album_id        FK, NOT NULL
genre_id        FK, NOT NULL

      0..many
        |
        | belong to
        |
        1

GENRE
-------------------------
genre_id        PK
genre_name
```

### Cardinality summary

| Relationship | Parent side | Child side |
|---|---|---|
| Artist → Album | An artist can have `0..many` albums | Each album has exactly `1` artist |
| Album → Song | An album can have `0..many` songs | Each song has exactly `1` album |
| Genre → Song | A genre can have `0..many` songs | Each song has exactly `1` genre |

Important:

```text
Some albums have no songs.
This does NOT mean some songs have no album.
```

The foreign keys are still required, so every album has an artist and every song has an album and genre.

---

# Why This Database Is Good for Practice

This schema gives practice with simple and advanced SQL.

## DDL Practice

Examples:

```sql
CREATE DATABASE music_db;
CREATE TABLE ...
ALTER TABLE ...
DROP TABLE ...
```

You can also practice:

```text
PRIMARY KEY
FOREIGN KEY
NOT NULL
UNIQUE
DEFAULT
```

## DML Practice

You can practice:

```sql
INSERT INTO ...
UPDATE ...
DELETE FROM ...
```

## DQL Practice

You can practice basic queries:

```sql
SELECT *
FROM artist;
```

Filtering:

```sql
SELECT *
FROM song
WHERE streams > 100000000;
```

Sorting:

```sql
SELECT *
FROM song
ORDER BY streams DESC;
```

Aggregation:

```sql
SELECT album_id, AVG(streams)
FROM song
GROUP BY album_id;
```

Filtering grouped results:

```sql
SELECT album_id, AVG(streams) AS avg_streams
FROM song
GROUP BY album_id
HAVING avg_streams > 100000000;
```

This database can also be used to practice:

```text
INNER JOIN
LEFT JOIN
RIGHT JOIN
multi-table JOIN
GROUP BY
HAVING
IS NULL
IS NOT NULL
COALESCE
Subqueries
Correlated subqueries
CTEs
CASE
Window Functions
OVER (PARTITION BY ...)
```

The practice data intentionally includes:

```text
artists with no albums
albums with no songs
a genre with no songs
NULL origin_state values
NULL album_name values
NULL song_name values
different album counts per artist
different song counts per album and genre
```

Example questions for later practice:

```text
Which artist has the most total streams?

What is the average number of streams for each album?

Which albums have an average stream count greater than 100 million?

What is the most streamed song for each artist?

How many albums does each artist have?

How many songs are in each genre?
```

---

# Current Study Step

The schema design is complete enough for query practice.

The current focus is:

```text
1. INNER JOIN
2. LEFT JOIN
3. RIGHT JOIN
4. GROUP BY + HAVING with joins
5. Subqueries
6. CTEs
7. Window functions
```

The important relationship idea to remember is:

```text
Parent can have zero children.
Child foreign keys are still required.
```
