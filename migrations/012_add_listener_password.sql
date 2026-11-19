-- Migration 012 (the website): listeners need a password to log in.
--
-- The website never saves the real password, only a hash: a scrambled version that
-- cannot be turned back into the password. To log in, the website scrambles what the
-- listener types the same way and compares the two hashes.
--
-- NULL means "this listener has no password yet", so they cannot log in. Everyone who
-- signs up on the website gets a hash. The practice listeners get one from
-- scripts/demo_passwords.sql.
--
-- 3NF: the hash depends only on listener_id (the key), so it belongs in listener.

ALTER TABLE listener
    ADD COLUMN password_hash VARCHAR(255) NULL AFTER email;
