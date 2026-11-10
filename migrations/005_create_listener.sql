-- Migration 005 (Stage 2): create the listener table.
-- One row for each person who uses the website.

CREATE TABLE listener (
    listener_id INT          NOT NULL AUTO_INCREMENT,
    username    VARCHAR(30)  NOT NULL,
    email       VARCHAR(100) NOT NULL,
    joined_date DATE         NOT NULL DEFAULT (CURRENT_DATE),  -- the day they signed up

    PRIMARY KEY (listener_id),

    -- No two listeners with the same username or the same email.
    CONSTRAINT uq_listener_username UNIQUE (username),
    CONSTRAINT uq_listener_email    UNIQUE (email)
);
