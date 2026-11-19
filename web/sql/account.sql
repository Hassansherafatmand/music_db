-- account.sql: sign up and log in (the listener table).


-- name: listener_by_username
-- Find a listener to log in. The website checks the password against the hash.
SELECT listener_id, username, password_hash
FROM listener
WHERE username = %(username)s;

-- name: create_listener
-- Sign up: a new listener. joined_date gets today by itself (DEFAULT).
-- UNIQUE on username and email refuses a name or email that is already taken.
INSERT INTO listener (username, email, password_hash)
VALUES (%(username)s, %(email)s, %(password_hash)s);


-- ============================================================ My account

-- name: my_account
-- My own account page: my email (only I can see it) and my numbers.
SELECT l.listener_id, l.username, l.email, l.joined_date,
       la.favorite_count, la.playlist_count, la.play_count, la.review_count, la.comment_count
FROM listener l
JOIN listener_activity la ON la.listener_id = l.listener_id
WHERE l.listener_id = %(listener_id)s;

-- name: my_password_hash
-- My password's hash, to check the password I typed (before a change or a delete).
SELECT password_hash
FROM listener
WHERE listener_id = %(listener_id)s;

-- name: update_email
-- Change my email. UNIQUE (email) refuses an email that another account has.
UPDATE listener
SET email = %(email)s
WHERE listener_id = %(listener_id)s;

-- name: update_password
-- Save a new password (only its hash, never the password itself).
UPDATE listener
SET password_hash = %(password_hash)s
WHERE listener_id = %(listener_id)s;

-- name: what_goes_too
-- Before deleting a listener: what ON DELETE CASCADE will delete with them.
-- Their reviews take the comments that OTHER people wrote under them too
-- (listener -> review -> review_comment: a chain of cascades).
SELECT la.favorite_count, la.playlist_count, la.play_count, la.review_count, la.comment_count,
       (SELECT COUNT(*) FROM playlist_song ps
        JOIN playlist p ON p.playlist_id = ps.playlist_id
        WHERE p.listener_id = %(listener_id)s) AS playlist_song_count,
       (SELECT COUNT(*) FROM review_comment c
        WHERE c.reviewer_id = %(listener_id)s
          AND c.listener_id <> %(listener_id)s) AS replies_count
FROM listener_activity la
WHERE la.listener_id = %(listener_id)s;

-- name: set_audit_actor
-- Tell the audit trigger (migration 014) who is deleting. @audit_actor is a
-- session variable: it lives only in this connection.
SET @audit_actor = %(actor)s;

-- name: delete_listener
-- Delete a listener. ON DELETE CASCADE deletes their favorites, playlists (and
-- playlist_song rows), plays, reviews (and the comments under them) and comments.
-- Then the trigger trg_listener_deleted writes one row into audit_log.
DELETE FROM listener
WHERE listener_id = %(listener_id)s;
