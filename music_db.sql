-- DROP DATABASE IF EXISTS music_db;
-- CREATE DATABASE music_db;
-- USE music_db;



/*==========================================================
Artist Table
===========================================================*/
CREATE TABLE artist (
    artist_id INT NOT NULL,
    artist_name VARCHAR(100) NOT NULL,
    origin_state CHAR(2),
    debut_year YEAR NOT NULL,

    PRIMARY KEY (artist_id)
);

/*==========================================================
Album Table
===========================================================*/
CREATE TABLE album (
    album_id INT NOT NULL,
    album_name VARCHAR(100),
    release_year YEAR NOT NULL,
    artist_id INT NOT NULL,

    PRIMARY KEY (album_id),
    FOREIGN KEY (artist_id) REFERENCES artist(artist_id)
);

/*==========================================================
Genre Table
===========================================================*/
CREATE TABLE genre (
    genre_id INT NOT NULL,
    genre_name VARCHAR(50) NOT NULL,

    PRIMARY KEY (genre_id)
);

/*==========================================================
Song Table
===========================================================*/
CREATE TABLE song (
    song_id INT NOT NULL,
    song_name VARCHAR(100),
    duration_seconds INT NOT NULL,
    track_number INT NOT NULL,
    streams INT NOT NULL,
    album_id INT NOT NULL,
    genre_id INT NOT NULL,

    PRIMARY KEY (song_id),

    FOREIGN KEY (album_id) REFERENCES album(album_id),
    FOREIGN KEY (genre_id) REFERENCES genre(genre_id),

    UNIQUE (album_id, track_number)
);




