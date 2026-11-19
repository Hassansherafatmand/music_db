"""Make the content pack: more made-up data, so the website looks like a real one.

    python3 scripts/make_content.py

It reads the practice data in data/*.csv (Stages 1 to 4) and writes new CSV files to
data/content/. scripts/import_content.sql loads them, after migrations 013 to 016.
The old CSV files are not changed: Stages 1 to 4 stay exactly as they are in git.

What it adds:
  - songs, so every album has at least 3 songs (an album with no songs is not an album)
  - albums for the 5 artists who had none, and songs for Classical (it had none)
  - 80 more listeners. Each one gets a "taste" (1 to 3 favorite genres), so their
    favorites, plays, playlists and reviews are different from everybody else's.
    The taste is NOT saved in the database: the website works it out from the
    favorites ("Top genres"), because data that can be calculated is not stored.
  - more favorites, plays (up to 2026-11-18), playlists, reviews with real-sounding
    text, and comments under the reviews

A fixed random seed means it makes the same files every time.
"""

import csv
import random
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = DATA / "content"

random.seed(2026)

LAST_DAY = date(2026, 11, 18)          # the newest data is from this day
PLAYS_FROM = date(2026, 10, 1)         # the play table starts here (Stage 3)
SHOWCASE_REVIEW = (3, 101)             # queries/showcase.sql inserts this review: keep it free


# ---------------------------------------------------------------- read the old data

def read(name):
    with open(DATA / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write(name, header, rows):
    OUT.mkdir(exist_ok=True)
    with open(OUT / name, "w", newline="", encoding="utf-8") as f:
        out = csv.writer(f, lineterminator="\r\n")  # CRLF, like the other CSV files
        out.writerow(header)
        out.writerows(rows)
    print(f"  data/content/{name}: {len(rows):,} rows")


artists = read("artist.csv")
albums = read("album.csv")
genres = {int(g["genre_id"]): g["genre_name"] for g in read("genre.csv")}
songs = read("song.csv")
listeners = read("listener.csv")
old_favorites = read("favorite.csv")
old_playlists = read("playlist.csv")
old_plays = read("play.csv")
old_reviews = read("review.csv")

song_genres = defaultdict(set)  # song_id -> {genre_id}
for s in songs:
    song_genres[int(s["song_id"])].add(int(s["genre_id"]))
for row in read("song_genre_extra.csv"):
    song_genres[int(row["song_id"])].add(int(row["genre_id"]))

album_of_song = {int(s["song_id"]): int(s["album_id"]) for s in songs}
song_name = {int(s["song_id"]): s["song_name"] for s in songs}
artist_of_album = {int(a["album_id"]): int(a["artist_id"]) for a in albums}
tracks = defaultdict(list)  # album_id -> [track numbers]
for s in songs:
    tracks[int(s["album_id"])].append(int(s["track_number"]))

next_song_id = max(int(s["song_id"]) for s in songs) + 1
next_album_id = max(int(a["album_id"]) for a in albums) + 1
FIRST_NEW_SONG = next_song_id
album_year = {int(a["album_id"]): int(a["release_year"]) for a in albums}


# ---------------------------------------------------------------- word banks

FIRST = ["Golden", "Southern", "Midnight", "Cold", "Quiet", "Empty", "Silver", "Velvet",
         "Paper", "Electric", "Neon", "Amber", "Crimson", "Lonely", "Wild", "Northern",
         "Summer", "Winter", "Broken", "Hidden", "Lucky", "Burning", "Gentle", "Restless"]
SECOND = ["Train", "Light", "Shadow", "Highway", "Bridge", "Valley", "Sky", "Bloom",
          "Thunder", "Current", "Memory", "Dream", "Fire", "Harbor", "River", "Rain",
          "Lights", "Heart", "Road", "Signal", "Garden", "Ocean", "Morning", "Echo"]
PHRASES = ["Long Way Home", "Last Call", "City at Dawn", "Back to You", "Stay a While",
           "Before the Storm", "Slow Dancing", "One More Night", "Out of Time",
           "Home Again", "Under the Stars", "All the Way Down", "Paper Planes"]
CLASSICAL = ["Nocturne in Blue", "Prelude for Rain", "Adagio for Strings", "Winter Sonata",
             "Etude No. 3", "Serenade", "Morning Overture", "Elegy", "Waltz of the Harbor",
             "Moonlight Variations", "Andante", "Rhapsody in Gray", "Pastorale",
             "Requiem for a River", "Fugue in Silver", "Lullaby", "Interlude",
             "Symphony of Lights", "Allegro", "Berceuse", "Romance", "Toccata"]
ALBUM_A = ["Velvet", "Quiet", "Paper", "Electric", "Winter", "Amber", "Crimson", "Indigo",
           "Golden", "Modern", "June", "Fading", "Distant", "Northern", "Wild"]
ALBUM_B = ["Seasons", "Signals", "Rooms", "Fields", "Letters", "Rivers", "Horizons",
           "Stories", "Memory", "Nights", "Roads", "Gardens", "Echoes", "Hours"]
CLASSICAL_ALBUMS = ["Nocturnes for a Quiet City", "Strings in Winter", "The Harbor Suite",
                    "Sonatas at Dusk"]

ADJECTIVES = ["silver", "frozen", "velvet", "happy", "sunny", "golden", "midnight", "brave",
              "cosmic", "lucky", "quiet", "wild", "misty", "electric", "crimson", "amber",
              "neon", "lunar", "rusty", "sleepy"]
ANIMALS = ["raven", "rocket", "harbor", "river", "echo", "cactus", "fox", "lantern",
           "meadow", "falcon", "tiger", "comet", "maple", "otter", "panda", "willow",
           "phoenix", "sparrow", "canyon", "koala"]
NAMES = ["sarah", "tom", "maya", "leo", "nina", "omar", "lena", "jay", "ava", "noah",
         "mia", "eli", "zoe", "sam", "ivy", "kai", "ruby", "max", "luna", "ben", "aria",
         "finn", "sofia", "hugo", "nora", "dev", "emma", "theo", "lily", "marco"]
NAME_ENDS = ["loops", "beats", "vinyl", "tunes", "on_repeat", "sounds", "listens",
             "music", "waves", "records", "plays", "notes"]

PLAYLIST_NAMES = ["Chill", "Cooking", "Focus", "Gym", "Late Night", "Old Favorites",
                  "Party", "Rainy Day", "Road Trip", "Running", "Study Time",
                  "Sunday Morning", "Sad Songs", "Summer 2026", "Deep Work",
                  "Morning Coffee", "Night Drive", "Throwbacks", "Weekend", "Dinner"]

# How popular each genre is as a taste (bigger number = more listeners like it).
TASTE_WEIGHT = {1: 10, 2: 12, 3: 9, 4: 5, 5: 6, 6: 4, 7: 4, 8: 3, 9: 7, 10: 4,
                11: 6, 12: 6, 13: 3, 14: 4, 15: 3}

OPENERS = {
    5: ["An instant classic.", "I can't stop playing this one.", "Front to back, no skips.",
        "Easily one of the best albums I heard this year.", "Pure magic from start to finish.",
        "This album found me at the right time.", "Wow. Just wow.",
        "Ten out of ten, would listen again."],
    4: ["Really solid album.", "Very good, with one or two weak spots.",
        "Better than I expected.", "A grower: it gets better every time.",
        "Strong songs and a great mood.", "Almost perfect."],
    3: ["It's okay.", "A mixed bag.", "Some good moments, some forgettable ones.",
        "Not bad, not amazing.", "Fine as background music.", "I wanted to like it more."],
    2: ["Not really for me.", "Disappointing after their last album.", "Too repetitive.",
        "A few nice ideas, but it drags.", "The production feels flat."],
    1: ["Couldn't finish it.", "Sorry, this one is a miss.", "Not my thing at all.",
        "I really tried, but no."],
}
GOOD_MIDDLES = ["'{song}' is the highlight for me.", "The opener '{song}' hooked me right away.",
                "'{song}' has been on repeat all week.", "Don't skip '{song}'.",
                "'{song}' gives me chills every time."]
BAD_MIDDLES = ["'{song}' is the only song I came back to.", "Even '{song}' couldn't save it.",
               "I skip '{song}' every time.", "'{song}' is fine, the rest is forgettable."]
FLAVOR = {
    "Rock": ["The guitars are huge.", "Loud in the best way."],
    "Pop": ["Catchy choruses everywhere.", "Every chorus gets stuck in my head."],
    "Hip-Hop": ["The beats hit hard.", "Sharp lyrics and a great flow."],
    "Country": ["Great storytelling.", "Feels like a long drive through small towns."],
    "R&B": ["Smooth vocals all the way.", "So smooth."],
    "Metal": ["Heavy and fast, just how I like it.", "The drums are insane."],
    "Jazz": ["The saxophone solos are beautiful.", "Feels like a small club at 2 a.m."],
    "Blues": ["Raw and honest.", "That guitar tone is pure blues."],
    "Electronic": ["The synths are gorgeous.", "Perfect for late-night drives."],
    "Folk": ["Simple and warm, like a campfire.", "Just a voice and a guitar, and it works."],
    "Alternative": ["Weird in a good way.", "Not like anything else I listen to."],
    "Indie": ["Feels very personal.", "Small, honest songs."],
    "Punk": ["Short, fast and angry.", "Pure energy."],
    "Soul": ["That voice!", "Warm and full of feeling."],
    "Classical": ["The strings are breathtaking.", "Great for studying.",
                  "Calm and beautiful."],
}
CLOSERS = ["Perfect for a rainy day.", "Great for the gym.", "Can't wait for the next one.",
           "Recommended!", "Give it a few listens.", "My new road trip album.",
           "Worth it for the last song alone.", "Headphones on, lights off."]
LOW_CLOSERS = ["Maybe their next one.", "Not for me, but maybe for you.",
               "I'll stick to their older stuff."]

AGREE = ["Totally agree!", "Same here, '{song}' is so good.", "100%. No skips.",
         "This review made me listen to it. Not disappointed.", "Underrated album for sure.",
         "Thanks for the tip, I added it to my playlist.", "Saw them live, even better!",
         "Yes! '{song}' is my favorite too."]
DISAGREE = ["Hard disagree, I think this is their best album.",
            "I had the same feeling at first. Give it another try.",
            "Interesting take! I like it more than you.",
            "Really? '{song}' is a masterpiece.", "Fair point about the second half."]
QUESTIONS = ["{reviewer}, what's your favorite song on it?",
             "Have you heard their older albums?", "Is it better than their last one?"]
REPLIES = ["Glad you liked it!", "Thanks! '{song}' for sure.",
           "Fair enough, it's not for everyone.", "Yes, give it a try!"]


# ---------------------------------------------------------------- small helpers

def random_day(start, end):
    if end <= start:
        return end
    return start + timedelta(days=random.randint(0, (end - start).days))


def random_time(day):
    # More listening in the evening, a little at night.
    hour = random.choices(range(24), weights=[2, 1, 1, 1, 1, 1, 2, 4, 6, 5, 4, 5,
                                              6, 5, 5, 6, 7, 8, 9, 10, 10, 8, 6, 4])[0]
    return datetime(day.year, day.month, day.day, hour,
                    random.randint(0, 59), random.randint(0, 59))


def as_date(text):
    return date.fromisoformat(text[:10])


def song_title(genre_id):
    if genre_id == 15:
        return random.choice(CLASSICAL)
    if random.random() < 0.15:
        return random.choice(PHRASES)
    return f"{random.choice(FIRST)} {random.choice(SECOND)}"


def streams():
    # Most songs have a few million streams, a few have very many, some have none.
    # (A number that is too big is drawn again, so no two songs end up on the same limit.)
    if random.random() < 0.04:
        return 0
    while True:
        value = random.lognormvariate(18.6, 1.6)
        if value < 1_850_000_000:
            return int(value)


def username_taken(name, taken):
    return name in taken or not (3 <= len(name) <= 30)


# ---------------------------------------------------------------- 1. songs and albums

new_albums, new_songs, new_song_genres = [], [], []


def add_song(album_id, track, genre_id, extra_genre=None):
    global next_song_id
    song_id = next_song_id
    next_song_id += 1
    name = song_title(genre_id)
    seconds = random.randint(150, 330) if genre_id != 15 else random.randint(180, 600)
    new_songs.append([song_id, name, seconds, track, streams(), album_id])
    new_song_genres.append([song_id, genre_id])
    song_genres[song_id] = {genre_id}
    if extra_genre and extra_genre != genre_id:
        new_song_genres.append([song_id, extra_genre])
        song_genres[song_id].add(extra_genre)
    album_of_song[song_id] = album_id
    song_name[song_id] = name
    tracks[album_id].append(track)
    return song_id


def main_genre_of_artist(artist_id):
    counts = Counter()
    for song_id, album_id in album_of_song.items():
        if artist_of_album.get(album_id) == artist_id:
            counts.update(song_genres[song_id])
    return counts.most_common(1)[0][0] if counts else None


# 1a. Every album gets at least 3 songs (most get 5 to 9).
for a in albums:
    album_id = int(a["album_id"])
    have = len(tracks[album_id])
    if have >= 3:
        continue
    counts = Counter(g for s, al in album_of_song.items() if al == album_id
                     for g in song_genres[s])
    genre_id = (counts.most_common(1)[0][0] if counts
                else main_genre_of_artist(int(a["artist_id"])) or random.choice(list(genres)))
    target = random.randint(5, 9)
    for track in range(max(tracks[album_id], default=0) + 1, target + 1):
        add_song(album_id, track, genre_id,
                 extra_genre=random.choice(list(genres)) if random.random() < 0.15 else None)

# 1b. The 5 artists with no albums get 2 or 3 albums each.
#     The first one plays Classical (no songs had that genre before).
artists_with_albums = {int(a["artist_id"]) for a in albums}
lonely = [a for a in artists if int(a["artist_id"]) not in artists_with_albums]
for i, artist in enumerate(lonely):
    artist_id = int(artist["artist_id"])
    debut = int(artist["debut_year"])
    genre_id = 15 if i == 0 else random.choice([g for g in genres if g != 15])
    names = list(CLASSICAL_ALBUMS) if genre_id == 15 else []
    for n in range(random.randint(2, 3)):
        album_id = next_album_id
        next_album_id += 1
        if names:
            name = names.pop(0)
        else:
            name = f"{random.choice(ALBUM_A)} {random.choice(ALBUM_B)}"
        year = random.randint(min(debut + 1, 2026), 2026)
        new_albums.append([album_id, name, year, artist_id])
        artist_of_album[album_id] = artist_id
        album_year[album_id] = year
        for track in range(1, random.randint(5, 10) + 1):
            extra = 7 if genre_id == 15 and random.random() < 0.2 else None  # a little Jazz
            add_song(album_id, track, genre_id, extra_genre=extra)

# 1c. A few Classical pieces as a second genre on other songs ("crossover").
for song_id in random.sample(sorted(s for s in song_genres if s < FIRST_NEW_SONG), 12):
    if 15 not in song_genres[song_id]:
        new_song_genres.append([song_id, 15])
        song_genres[song_id].add(15)

songs_by_genre = defaultdict(list)
for song_id, gs in song_genres.items():
    for g in gs:
        songs_by_genre[g].append(song_id)
all_song_ids = sorted(song_genres)
songs_of_album = defaultdict(list)
for song_id, album_id in album_of_song.items():
    songs_of_album[album_id].append(song_id)
all_album_ids = sorted(songs_of_album)


# ---------------------------------------------------------------- 2. listeners with a taste

taken = {l["username"] for l in listeners}
new_listeners = []
taste = {}  # listener_id -> [genre ids]   (only used here, never saved)
genre_ids = list(TASTE_WEIGHT)
for listener_id in range(41, 121):
    while True:
        if random.random() < 0.55:
            base = random.choice(NAMES)
            style = random.random()
            if style < 0.4:
                name = f"{base}_{random.choice(NAME_ENDS)}"
            elif style < 0.7:
                name = f"{base}{random.randint(1, 99)}"
            else:
                name = f"{base}_{random.choice('abcdefghjklmnprstw')}"
        else:
            name = f"{random.choice(ADJECTIVES)}_{random.choice(ANIMALS)}{random.randint(1, 99)}"
        if not username_taken(name, taken):
            break
    taken.add(name)
    joined = random_day(date(2024, 1, 1), date(2026, 11, 12))
    new_listeners.append([listener_id, name, f"{name}@example.com", joined.isoformat()])
    count = random.choices([1, 2, 3], weights=[3, 5, 2])[0]
    picks = []
    while len(picks) < count:
        g = random.choices(genre_ids, weights=[TASTE_WEIGHT[x] for x in genre_ids])[0]
        if g not in picks:
            picks.append(g)
    taste[listener_id] = picks

joined_of = {int(l["listener_id"]): as_date(l["joined_date"]) for l in listeners}
joined_of.update({row[0]: date.fromisoformat(row[3]) for row in new_listeners})

# The old listeners' taste: their top genres in the favorites they already have.
for l in listeners:
    listener_id = int(l["listener_id"])
    counts = Counter(g for f in old_favorites if int(f["listener_id"]) == listener_id
                     for g in song_genres[int(f["song_id"])])
    taste[listener_id] = [g for g, _ in counts.most_common(2)] or random.sample(genre_ids, 2)


def taste_song(listener_id, share=0.8):
    """A song this listener would like: mostly from their genres, sometimes anything."""
    if random.random() < share:
        return random.choice(songs_by_genre[random.choice(taste[listener_id])])
    return random.choice(all_song_ids)


# ---------------------------------------------------------------- 3. favorites

new_favorites = []
favorites_of = defaultdict(set)
for f in old_favorites:
    favorites_of[int(f["listener_id"])].add(int(f["song_id"]))
for listener_id, *_ in new_listeners:
    joined = joined_of[listener_id]
    how_many = random.randint(0, 6) if joined > date(2026, 11, 1) else random.randint(8, 34)
    while len(favorites_of[listener_id]) < how_many:
        song_id = taste_song(listener_id)
        if song_id in favorites_of[listener_id]:
            continue
        favorites_of[listener_id].add(song_id)
        released = date(album_year[album_of_song[song_id]], 1, 1)  # not before the album exists
        new_favorites.append([listener_id, song_id,
                              random_day(max(joined, released), LAST_DAY).isoformat()])


# ---------------------------------------------------------------- 4. plays

new_plays = []
next_play_id = max(int(p["play_id"]) for p in old_plays) + 1


def add_plays(listener_id, start, how_many):
    global next_play_id
    favorites = sorted(favorites_of[listener_id])
    for _ in range(how_many):
        roll = random.random()
        if favorites and roll < 0.5:
            song_id = random.choice(favorites)          # people play their favorites a lot
        else:
            song_id = taste_song(listener_id, share=0.75)
        played = random_time(random_day(start, LAST_DAY))
        new_plays.append([next_play_id, listener_id, song_id, played])
        next_play_id += 1


for listener_id, *_ in new_listeners:
    start = max(joined_of[listener_id], PLAYS_FROM)
    days = (LAST_DAY - start).days + 1
    if random.random() < 0.08:
        continue  # a few listeners never press Play
    add_plays(listener_id, start, random.randint(days // 2, days * 3))

# The old listeners keep listening after 2026-11-09 (where the Stage 3 plays stop).
old_players = {int(p["listener_id"]) for p in old_plays}
for listener_id in sorted(old_players):
    add_plays(listener_id, date(2026, 11, 10), random.randint(4, 30))

new_plays.sort(key=lambda row: row[3])  # play_id in time order, like real data
first_play_id = max(int(p["play_id"]) for p in old_plays) + 1
for i, row in enumerate(new_plays):
    row[0] = first_play_id + i
    row[3] = row[3].strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------- 5. playlists

new_playlists, new_playlist_songs = [], []
next_playlist_id = max(int(p["playlist_id"]) for p in old_playlists) + 1
for listener_id, *_ in new_listeners:
    joined = joined_of[listener_id]
    names = random.sample(PLAYLIST_NAMES, random.choices([0, 1, 2, 3], weights=[3, 4, 3, 2])[0])
    for name in names:
        created = random_day(joined, LAST_DAY)
        new_playlists.append([next_playlist_id, listener_id, name, created.isoformat()])
        chosen = []
        for _ in range(random.randint(4, 15)):
            song_id = taste_song(listener_id, share=0.85)
            if song_id not in chosen:
                chosen.append(song_id)
        for position, song_id in enumerate(chosen, start=1):
            new_playlist_songs.append([next_playlist_id, song_id, position,
                                       random_day(created, LAST_DAY).isoformat()])
        next_playlist_id += 1


# ---------------------------------------------------------------- 6. reviews

def review_text(album_id, stars, listener_id):
    if random.random() < 0.12:
        return ""  # stars only (NULL in the database)
    song_ids = [s for s in songs_of_album[album_id] if song_name[s]]
    song = song_name[random.choice(song_ids)] if song_ids else "the first song"
    parts = [random.choice(OPENERS[stars])]
    if random.random() < 0.6:
        pool = GOOD_MIDDLES if stars >= 4 else BAD_MIDDLES
        parts.append(random.choice(pool).format(song=song))
    album_genres = Counter(g for s in songs_of_album[album_id] for g in song_genres[s])
    if album_genres and random.random() < 0.5 and stars >= 3:
        parts.append(random.choice(FLAVOR[genres[album_genres.most_common(1)[0][0]]]))
    if random.random() < 0.4:
        parts.append(random.choice(CLOSERS if stars >= 3 else LOW_CLOSERS))
    return " ".join(parts)[:500]


reviewed = {(int(r["listener_id"]), int(r["album_id"])) for r in old_reviews}
new_reviews = []


def add_review(listener_id, album_id):
    key = (listener_id, album_id)
    if key in reviewed or key == SHOWCASE_REVIEW:
        return
    reviewed.add(key)
    album_genres = {g for s in songs_of_album[album_id] for g in song_genres[s]}
    likes_it = bool(album_genres & set(taste[listener_id]))
    weights = [1, 2, 4, 8, 7] if likes_it else [3, 4, 5, 3, 1]
    stars = random.choices([1, 2, 3, 4, 5], weights=weights)[0]
    released = date(album_year[album_id], 1, 1)  # nobody reviews an album before it exists
    day = random_day(max(joined_of[listener_id], released, date(2024, 6, 1)), LAST_DAY)
    new_reviews.append([listener_id, album_id, stars,
                        review_text(album_id, stars, listener_id), day.isoformat()])


for listener_id, *_ in new_listeners:
    for _ in range(random.choices(range(10), weights=[4, 5, 6, 6, 5, 4, 3, 2, 1, 1])[0]):
        song_id = taste_song(listener_id, share=0.85)
        add_review(listener_id, album_of_song[song_id])
for l in listeners:  # a few more reviews from the old listeners too
    listener_id = int(l["listener_id"])
    for _ in range(random.randint(0, 3)):
        add_review(listener_id, album_of_song[taste_song(listener_id)])


# ---------------------------------------------------------------- 7. comments under reviews

usernames = {int(l["listener_id"]): l["username"] for l in listeners}
usernames.update({row[0]: row[1] for row in new_listeners})
all_reviews = [(int(r["listener_id"]), int(r["album_id"]), int(r["stars"]), as_date(r["review_date"]))
               for r in old_reviews]
all_reviews += [(r[0], r[1], r[2], date.fromisoformat(r[4])) for r in new_reviews]
all_listener_ids = sorted(usernames)

new_comments = []
for reviewer_id, album_id, stars, review_day in sorted(all_reviews):
    how_many = random.choices([0, 1, 2, 3, 4], weights=[5, 5, 3, 2, 1])[0]
    when = datetime(review_day.year, review_day.month, review_day.day, 12)
    talked = False
    song_ids = [s for s in songs_of_album[album_id] if song_name[s]]
    for _ in range(how_many):
        song = song_name[random.choice(song_ids)] if song_ids else "the first song"
        if talked and random.random() < 0.3:
            author, text = reviewer_id, random.choice(REPLIES)  # the reviewer answers
        else:
            author = random.choice(all_listener_ids)
            if author == reviewer_id or joined_of[author] > review_day:
                continue
            album_genres = {g for s in songs_of_album[album_id] for g in song_genres[s]}
            agrees = (stars >= 4) == bool(album_genres & set(taste[author]))
            pool = AGREE if agrees else DISAGREE
            if random.random() < 0.15:
                pool = QUESTIONS
            text = random.choice(pool)
            talked = True
        when = when + timedelta(hours=random.randint(1, 72), minutes=random.randint(0, 59))
        if when.date() > LAST_DAY:
            break
        text = text.format(song=song, reviewer=usernames[reviewer_id])
        new_comments.append([None, reviewer_id, album_id, author, text,
                             when.strftime("%Y-%m-%d %H:%M:%S")])

new_comments.sort(key=lambda row: row[5])
for comment_id, row in enumerate(new_comments, start=1):
    row[0] = comment_id


# ---------------------------------------------------------------- write the files

print("Writing the content pack:")
write("album.csv", ["album_id", "album_name", "release_year", "artist_id"], new_albums)
write("song.csv", ["song_id", "song_name", "duration_seconds", "track_number", "streams",
                   "album_id"], new_songs)
write("song_genre.csv", ["song_id", "genre_id"], new_song_genres)
write("listener.csv", ["listener_id", "username", "email", "joined_date"], new_listeners)
write("favorite.csv", ["listener_id", "song_id", "added_date"], new_favorites)
write("playlist.csv", ["playlist_id", "listener_id", "playlist_name", "created_date"],
      new_playlists)
write("playlist_song.csv", ["playlist_id", "song_id", "position", "added_date"],
      new_playlist_songs)
write("play.csv", ["play_id", "listener_id", "song_id", "played_at"], new_plays)
write("review.csv", ["listener_id", "album_id", "stars", "review_text", "review_date"],
      new_reviews)
write("review_comment.csv", ["comment_id", "reviewer_id", "album_id", "listener_id",
                             "comment_text", "commented_at"], new_comments)
