-- Demo passwords for the practice listeners (run after migration 012 and the content pack).
--
-- The practice listeners come from data/listener.csv (40, Stage 2) and
-- data/content/listener.csv (80 more), which have no passwords. This gives all of them
-- the same demo password, so you can log in as any of them:
--
--     password: music330
--
-- The long text below is the hash of "music330" (made by the website's own
-- generate_password_hash), not the password itself. It is practice data only:
-- a real website would never give everyone the same password.

UPDATE listener
SET password_hash = 'scrypt:32768:8:1$eWkYgGuvmoRsWtNg$1cc3ba899d99ae5344d86c405ef3801fa28e023b88bae72bacb3c70dd18726847dfb8999256fb9d1fd13b967691041a85d17e1cd27c760a2c1bf50eed4e65cf9'
WHERE password_hash IS NULL;
