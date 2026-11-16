-- Nightly top-songs job (Stage 3).
--
-- Every night it finds what each listener played yesterday, most played first.
-- The email service (an outside service, imaginary) sends each listener their list.
-- We run it by hand:  mysql -u root -p music_db < scripts/nightly_top_songs.sql
--
-- The real job would use yesterday's date:  SET @day = CURDATE() - INTERVAL 1 DAY;
-- The practice data ends on 2026-11-09, so we use that day.
SET @day = DATE('2026-11-09');

SELECT l.username, l.email, s.song_name, COUNT(*) AS plays
FROM play p
JOIN listener l ON l.listener_id = p.listener_id
JOIN song s     ON s.song_id = p.song_id
WHERE p.played_at >= @day
  AND p.played_at <  @day + INTERVAL 1 DAY
GROUP BY l.listener_id, l.username, l.email, s.song_id, s.song_name
ORDER BY l.username, plays DESC;
