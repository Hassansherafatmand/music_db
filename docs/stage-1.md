# Stage 1 (Week 7): the music catalog

**What changed and why:** the database starts with the music itself: artists, their
albums, the songs on each album, and genres. An import script loads the practice data,
and the (imaginary) listener website can browse and search it.

## Database (4 tables)

```mermaid
erDiagram
    ARTIST ||--o{ ALBUM : "has"
    ALBUM ||--o{ SONG : "contains"
    GENRE ||--o{ SONG : "describes"

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
```

## The system around the database

```mermaid
flowchart LR
    W["Listener website<br/>(imaginary)"] -- "search, browse" --> A["API server<br/>(imaginary)"]
    A -- "runs SELECT" --> DB[("MySQL<br/>music_db")]
    I["Import script<br/>scripts/import_data.sql"] -- "loads CSV data" --> DB
```

## Files in this stage

| File | What it does |
|---|---|
| `migrations/001_create_artist.sql` | creates `artist` |
| `migrations/002_create_album.sql` | creates `album` (FK → `artist`) |
| `migrations/003_create_genre.sql` | creates `genre` (`genre_name` is unique) |
| `migrations/004_create_song.sql` | creates `song` (FK → `album`, FK → `genre`) |
| `scripts/import_data.sql` | loads `data/*.csv` into the 4 tables |
| `scripts/build.sql` | builds everything from zero, in order |
