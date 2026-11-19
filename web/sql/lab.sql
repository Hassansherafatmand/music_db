-- lab.sql: the Lab pages, which show how the website and the database work.


-- ============================================================ Security

-- name: safe_login_lookup
-- How the login really finds a listener: the username is a parameter. Whatever is
-- typed, MySQL compares it as plain text with the username column.
SELECT listener_id, username
FROM listener
WHERE username = %(username)s;

-- name: demo_hash
-- What the database keeps instead of a password: only the hash.
SELECT username, password_hash
FROM listener
WHERE username = %(username)s;

-- name: my_grants
-- What the website's MySQL user is allowed to do.
SHOW GRANTS FOR CURRENT_USER();


-- ============================================================ Speed (indexes)

-- name: names_starting
-- Song names that START with some letters. The index idx_song_name can be used,
-- because it is sorted by the first letters (like a phone book).
SELECT song_id, song_name
FROM song
WHERE song_name LIKE %(starts)s;

-- name: names_containing
-- Song names that CONTAIN some letters anywhere. A % at the start means the index
-- can't help: MySQL must read every song.
SELECT song_id, song_name
FROM song
WHERE song_name LIKE %(contains)s;

-- name: names_fulltext
-- The same search with the FULLTEXT index: it finds words in any position.
SELECT song_id, song_name
FROM song
WHERE MATCH (song_name) AGAINST (%(words)s IN BOOLEAN MODE);

-- name: plays_range
-- The plays of one day, as a range on played_at: the index idx_play_played_at is used.
SELECT COUNT(*) AS plays
FROM play
WHERE played_at >= %(day)s AND played_at < %(day)s + INTERVAL 1 DAY;

-- name: plays_function
-- The same day, but with a function around the column: DATE(played_at). MySQL must
-- run DATE() for every row first, so it can't use the index.
SELECT COUNT(*) AS plays
FROM play
WHERE DATE(played_at) = %(day)s;

-- name: plays_no_index
-- The range again, but we tell MySQL to ignore the index (IGNORE INDEX), to compare.
SELECT COUNT(*) AS plays
FROM play IGNORE INDEX (idx_play_played_at)
WHERE played_at >= %(day)s AND played_at < %(day)s + INTERVAL 1 DAY;


-- ============================================================ Two browsers

-- name: live_numbers
-- The numbers right now, straight from the database (every browser sees the same).
SELECT (SELECT COUNT(*) FROM favorite) AS favorites,
       (SELECT COUNT(*) FROM play)     AS plays,
       (SELECT COUNT(*) FROM review_comment) AS comments,
       NOW() AS server_time;
