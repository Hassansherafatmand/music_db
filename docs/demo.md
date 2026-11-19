# music_db: a 10-minute tour

A plan for showing the project: what to click, and what to say. Start the website with
`./run.sh` first (see the [README](../README.md)).

Every page has **"Under the hood"** at the bottom: open it to show the SQL that page just
ran, with its parameters.

---

## 1. The three parts (1 minute)

Open **Lab** (`/lab`). The picture shows the three parts: the **browser**, the **web
server** (Python + Flask) and the **database** (MySQL). The browser never talks to MySQL.
The web server runs the SQL from `web/sql/*.sql` and sends back the page.

## 2. The music, with filters (2 minutes)

1. Open **Songs**. Choose **Genre: Pop**, then **Sort by: Most played**.
2. Open "Under the hood": the `WHERE` got a piece for the genre, and `ORDER BY` changed.
   The genre is a parameter (`genre = 2`), sent separately from the SQL.
3. Choose **Length: Medium**: the SQL now has `BETWEEN 180 AND 300`.
4. Open **Albums**, choose **Stars: 4★ or more**. This one uses `HAVING`, because it
   filters on `AVG(stars)`, which only exists after `GROUP BY`.
5. Open **Charts**: window functions (`RANK() OVER (PARTITION BY genre_id ...)`) and a
   recursive CTE that makes 30 days in a row.

## 3. Every listener is different (1 minute)

1. Open **Listeners**. Each card shows a "top genre". It is not saved anywhere: a window
   function finds it from the listener's ♥.
2. Open one profile: their taste in percent, their favorites, reviews and comments.

## 4. Two browsers at the same time (2 minutes)

1. In **Chrome**, log in as `sunny_cactus40` (password `music330`) and open
   **Lab → Two browsers**.
2. In **Safari** (or a private window), log in as `brave_falcon3` and open the same page.
   The two "session names" are different: two logins, one server, one database.
3. In Chrome, press ♥ on the song on that page. Refresh Safari: the numbers went up.
4. In Safari, open **My favorites**: these are brave_falcon3's songs, not sunny's. Each
   SQL uses `WHERE listener_id = <who is logged in>`.
5. While logged in as sunny, open **brave_falcon3's profile**: "You both love N songs" uses
   `INTERSECT`.

## 5. Writing data (1 minute)

On an album page: ♥ a song (`INSERT`), press ▶ (`INSERT` into `play`), post a review
(`INSERT ... ON DUPLICATE KEY UPDATE`), and reply to someone's review (a comment: its
foreign key points to the review's **two-column** key).

## 6. Security (1 minute)

Open **Lab → Security** and press **The classic attack** (`' OR '1'='1' --`). The left side
shows how a careless website would glue it into the SQL (every listener would match).
The right side shows music_db: the text is a parameter, so MySQL finds **0 rows**.

## 7. CASCADE, RESTRICT and the trigger (2 minutes)

1. Open the admin page (`/admin`, the password is `ADMIN_PASSWORD` in `.env`).
2. **Listeners → Manage** on anyone: the page lists what `ON DELETE CASCADE` will delete
   (favorites, playlists, plays, reviews, and the comments under those reviews). Press
   **Delete**.
3. Open **Audit log**: a new row. Nobody wrote it from Python: the trigger
   `trg_listener_deleted` did it, `AFTER DELETE`.
4. Open any album, press ✎ on a song, then **Try to delete**. MySQL says no: listeners still
   ♥ it (`RESTRICT`). The music and the listeners' history are protected.
5. Open **Reports**: six questions answered with SQL (`LEFT JOIN ... IS NULL`, `NOT EXISTS`,
   a correlated subquery, `CASE`, `EXCEPT`, `GROUP BY HOUR()`).

## 8. Speed (optional)

**Lab → Speed**: the same question with and without an index. `EXPLAIN` shows `range`
(reads a part of an index) or `ALL` (reads the whole table), and how many rows MySQL reads.

---

After the demo, `./run.sh --fresh` builds the database again from zero, so the next demo
starts clean.
