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
