# music_db: design

> A small music website where listeners browse artists, albums and songs, and save
> their own favorite songs and playlists.

This document explains the whole system: the website, the parts around the database,
the tables, and how the database grows in 4 stages.

---

## 1. The system

The **website is imaginary**: it is designed and drawn, but not built. Everything that
touches the database is **real** and lives in this repo.

| Part | Real or imaginary | What it does with the data |
|---|---|---|
| Listener website | imaginary | browse, search, sign up, press ♥ |
| API server | imaginary | gets requests from the website and runs the SQL |
| MySQL database `music_db` | **real** | stores everything |
| One SQL file for each website action | **real** | the exact query the API server would run |
| Import script | **real** | loads the CSV files in `data/` into the tables |

- The API server sits between the website and the database. A browser must never talk
  to MySQL directly, because then everyone could see the database password.
- There is no real sound. Playing music is not part of the system.

```text
Listener website* --sign up, ♥, search, browse--> API server* --runs SQL--> MySQL music_db
                                                                                 ^
                                              Import script --loads CSV data-----'

* = imaginary
```

---

## 2. The stages

The database grows in 4 stages. Each stage is a set of migrations (small numbered SQL
files, run in order), and each finished stage gets a git tag.

| Stage | New tables | Tables in total | Status |
|---|---|---|---|
| 1 | `artist`, `album`, `song`, `genre` | 4 | **built** (git tag `stage-1`, see [stage-1.md](stage-1.md)) |
| 2 | `listener`, `favorite` | 6 | planned |
| 3 | `playlist`, `playlist_song`, `play` | 9 | planned |
| 4 | `song_genre`, `review` | 11 | planned |

In Stage 4, `song_genre` replaces the column `song.genre_id`, so that one song can have
more than one genre.

---

## 3. ER diagram (Stages 1 to 3)

```mermaid
erDiagram
    ARTIST ||--o{ ALBUM : "has"
    ALBUM ||--o{ SONG : "contains"
    GENRE ||--o{ SONG : "describes"
    LISTENER ||--o{ FAVORITE : "saves"
    SONG ||--o{ FAVORITE : "is saved in"
    LISTENER ||--o{ PLAYLIST : "owns"
    PLAYLIST ||--o{ PLAYLIST_SONG : "holds"
    SONG ||--o{ PLAYLIST_SONG : "is in"
    LISTENER ||--o{ PLAY : "presses Play"
    SONG ||--o{ PLAY : "is played"

    ARTIST {
        int artist_id PK
        varchar artist_name
        char origin_state
        year debut_year
    }
    ALBUM {
        int album_id PK
        varchar album_name
        year release_year
        int artist_id FK
    }
    GENRE {
        int genre_id PK
        varchar genre_name
    }
    SONG {
        int song_id PK
        varchar song_name
        int duration_seconds
        int track_number
        bigint streams
        int album_id FK
        int genre_id FK
    }
    LISTENER {
        int listener_id PK
        varchar username
        varchar email
        date joined_date
    }
    FAVORITE {
        int listener_id PK, FK
        int song_id PK, FK
        date added_date
    }
    PLAYLIST {
        int playlist_id PK
        int listener_id FK
        varchar playlist_name
        date created_date
    }
    PLAYLIST_SONG {
        int playlist_id PK, FK
        int song_id PK, FK
        int position
        date added_date
    }
    PLAY {
        int play_id PK
        int listener_id FK
        int song_id FK
        datetime played_at
    }
```

---

## 4. The tables

### Stage 1: the music catalog

**`artist`**: one row for each artist.

| Column | Key | Notes |
|---|---|---|
| `artist_id` | PK | |
| `artist_name` | | required |
| `origin_state` | | US state, 2 letters, like `WA`. Can be empty. |
| `debut_year` | | the year the artist started |

**`album`**: one row for each album.

| Column | Key | Notes |
|---|---|---|
| `album_id` | PK | |
| `album_name` | | can be empty |
| `release_year` | | the year the album came out |
| `artist_id` | FK → `artist` | required |

**`genre`**: one row for each genre, like Rock or Pop.

| Column | Key | Notes |
|---|---|---|
| `genre_id` | PK | |
| `genre_name` | | required, unique |

**`song`**: one row for each song.

| Column | Key | Notes |
|---|---|---|
| `song_id` | PK | |
| `song_name` | | can be empty |
| `duration_seconds` | | how long the song is |
| `track_number` | | the place of the song on its album |
| `streams` | | streams on **other** music services, from the CSV (`BIGINT`) |
| `album_id` | FK → `album` | required |
| `genre_id` | FK → `genre` | required |

Extra rule: `UNIQUE (album_id, track_number)`. One album cannot have two "track 1"s.

Every `_id` primary key is `AUTO_INCREMENT`: a new row gets the next number by itself.

### Stage 2: listeners and favorites

**`listener`**: one row for each person who uses the website.

| Column | Key | Notes |
|---|---|---|
| `listener_id` | PK | |
| `username` | | unique |
| `email` | | unique |
| `joined_date` | | the day they signed up |

**`favorite`**: one row for "this listener loves this song".

| Column | Key | Notes |
|---|---|---|
| `listener_id` | PK, FK → `listener` | |
| `song_id` | PK, FK → `song` | |
| `added_date` | | the day they pressed ♥ |

### Stage 3: playlists and plays

**`playlist`**: one row for each playlist.

| Column | Key | Notes |
|---|---|---|
| `playlist_id` | PK | |
| `listener_id` | FK → `listener` | required (the owner) |
| `playlist_name` | | required |
| `created_date` | | the day it was made |

Extra rule: `UNIQUE (listener_id, playlist_name)`. One listener cannot have two
playlists with the same name.

**`playlist_song`**: one row for "this song is in this playlist, at this place".

| Column | Key | Notes |
|---|---|---|
| `playlist_id` | PK, FK → `playlist` | |
| `song_id` | PK, FK → `song` | |
| `position` | | the order: 1, 2, 3… |
| `added_date` | | the day the song was added |

Extra rule: `UNIQUE (playlist_id, position)`. Two songs cannot have the same place in
one playlist.

**`play`**: one row each time a listener presses Play.

| Column | Key | Notes |
|---|---|---|
| `play_id` | PK | |
| `listener_id` | FK → `listener` | required |
| `song_id` | FK → `song` | required |
| `played_at` | | the date and time |

---

## 5. Relationships

| Relationship | In words |
|---|---|
| `artist` 1 — 0..many `album` | One artist has zero or more albums. Each album has exactly one artist. |
| `album` 1 — 0..many `song` | One album has zero or more songs. Each song is on exactly one album. |
| `genre` 1 — 0..many `song` | One genre has zero or more songs. Each song has exactly one genre. |
| `listener` 1 — 0..many `favorite` | One listener has zero or more favorites. Each favorite belongs to exactly one listener. |
| `song` 1 — 0..many `favorite` | One song is loved zero or more times. Each favorite is for exactly one song. |
| `listener` 1 — 0..many `playlist` | One listener has zero or more playlists. Each playlist has exactly one owner. |
| `playlist` 1 — 0..many `playlist_song` | One playlist holds zero or more songs. |
| `song` 1 — 0..many `playlist_song` | One song is in zero or more playlists. |
| `listener` 1 — 0..many `play` | One listener has zero or more plays. |
| `song` 1 — 0..many `play` | One song is played zero or more times. |

Many-to-many relationships:

- `listener` and `song`, through `favorite` (loved once)
- `playlist` and `song`, through `playlist_song`
- `listener` and `song`, through `play` (played many times)

A parent can have no children (some artists have no albums yet). But a child always
needs its parent, because every foreign key is required (`NOT NULL`).

---

## 6. Why it is built like this

The database is in **3NF**. The important choices:

- **`song` has no `artist_id`.** The artist depends on the album, not on the song. A
  copy in `song` could say "artist A" while the album says "artist B". To find a song's
  artist, join `song` → `album` → `artist`.
- **`genre_name` lives only in `genre`.** In `song`, it would depend on `genre_id`,
  which is not the key.
- **`favorite` has a two-column key** (`listener_id`, `song_id`). A listener cannot love
  the same song twice. Its only other column, `added_date`, depends on the whole key
  (2NF). A column like `username` would not belong here, because it depends only on
  `listener_id`.
- **`favorite` and `play` look alike, but their keys are different.** You love a song
  only once, so `favorite` uses the two-column key. You can play a song many times, so
  `play` needs its own `play_id`.
- **`playlist` does not save its owner's `username`.** It would depend on
  `listener_id`, which is not the key (3NF).
- **`playlist` has no "number of songs" column.** We count the rows in
  `playlist_song` instead. We don't save what we can calculate.
- **`streams` is not a copy of `play`.** `song.streams` is the count from **other**
  music services (from the CSV). `play` is the plays on **our** website. These are two
  different facts.
- **`streams` is a `BIGINT`.** An `INT` stops at about 2.1 billion, and one song already
  has 1,847,621,533 streams.
- **Constraints have names** (like `fk_song_genre`). Error messages show the name, and a
  later migration can remove a constraint by its name.

---

## 7. Files

| File | What it is |
|---|---|
| `docs/design.md` | this document |
| `docs/stage-1.md` | the Stage 1 diagrams |
| `migrations/` | the migrations: small numbered SQL files, run in order |
| `scripts/import_data.sql` | loads the CSV files into the tables |
| `scripts/build.sql` | builds the whole database from zero |
| `data/` | made-up practice data (CSV files), generated with AI |
