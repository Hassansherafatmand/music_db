-- Migration 014 (the website, after Stage 4): an audit log, filled by triggers.
--
-- An audit log remembers who deleted what, and when. Real companies keep one, so
-- they can answer "where did this listener go?" later.
--
-- A trigger is SQL that MySQL runs by itself when something happens to a table.
-- Here: AFTER a row is DELETEd from listener, artist, album or song, the trigger
-- writes one row into audit_log. The website does not have to remember to do it.
--
-- audit_log has no foreign keys, on purpose: the row it talks about is gone.
-- It keeps a copy of a few values (like the username). That is allowed here:
-- a log is history, and history must not change when the original row is deleted.
--
-- Who did it: the website sets the variable @audit_actor (for example 'admin') just
-- before it deletes. If it is not set, USER() gives the MySQL user who is logged in.
--
-- Good to know: rows that are deleted by ON DELETE CASCADE do NOT start triggers in
-- MySQL. So deleting a listener writes 1 row here, not one row per favorite.

CREATE TABLE audit_log (
    audit_id   INT          NOT NULL AUTO_INCREMENT,
    action     VARCHAR(10)  NOT NULL,   -- what happened, like 'DELETE'
    table_name VARCHAR(30)  NOT NULL,   -- in which table
    row_id     INT          NOT NULL,   -- the id of the row
    details    VARCHAR(255) NOT NULL,   -- a copy of the important values
    done_by    VARCHAR(100) NOT NULL,   -- who did it
    done_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (audit_id)
);

-- Each trigger is one INSERT, so no BEGIN ... END (and no DELIMITER) is needed.
-- OLD is the row as it was, just before the DELETE.

CREATE TRIGGER trg_listener_deleted
AFTER DELETE ON listener
FOR EACH ROW
INSERT INTO audit_log (action, table_name, row_id, details, done_by)
VALUES ('DELETE', 'listener', OLD.listener_id,
        CONCAT('username: ', OLD.username, ', email: ', OLD.email,
               ', joined: ', OLD.joined_date),
        COALESCE(@audit_actor, USER()));

CREATE TRIGGER trg_artist_deleted
AFTER DELETE ON artist
FOR EACH ROW
INSERT INTO audit_log (action, table_name, row_id, details, done_by)
VALUES ('DELETE', 'artist', OLD.artist_id,
        CONCAT('artist: ', OLD.artist_name, ', state: ', COALESCE(OLD.origin_state, '-')),
        COALESCE(@audit_actor, USER()));

CREATE TRIGGER trg_album_deleted
AFTER DELETE ON album
FOR EACH ROW
INSERT INTO audit_log (action, table_name, row_id, details, done_by)
VALUES ('DELETE', 'album', OLD.album_id,
        CONCAT('album: ', COALESCE(OLD.album_name, 'Untitled'), ' (', OLD.release_year,
               '), artist_id: ', OLD.artist_id),
        COALESCE(@audit_actor, USER()));

CREATE TRIGGER trg_song_deleted
AFTER DELETE ON song
FOR EACH ROW
INSERT INTO audit_log (action, table_name, row_id, details, done_by)
VALUES ('DELETE', 'song', OLD.song_id,
        CONCAT('song: ', COALESCE(OLD.song_name, 'Untitled'), ', album_id: ', OLD.album_id,
               ', track ', OLD.track_number),
        COALESCE(@audit_actor, USER()));
