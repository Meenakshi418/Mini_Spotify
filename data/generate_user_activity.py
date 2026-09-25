from pathlib import Path
import random
import sqlite3
from datetime import datetime, timedelta

import pandas as pd

# -----------------------------
# SETTINGS
# -----------------------------
RANDOM_SEED = 42
SYNTHETIC_USERS = 199          # + existing demo user = 200 total
EVENTS_PER_USER_MIN = 40
EVENTS_PER_USER_MAX = 80

random.seed(RANDOM_SEED)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "backend" / "mini_spotify.db"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ACTIVITY_CSV = OUTPUT_DIR / "synthetic_activity.csv"

# -----------------------------
# CONNECT TO DATABASE
# -----------------------------
conn = sqlite3.connect(DB_PATH)

songs = pd.read_sql_query(
    """
    SELECT id, title, artist, genre, popularity
    FROM songs
    WHERE id IS NOT NULL
    """,
    conn
)

if songs.empty:
    raise RuntimeError("No songs found in the database.")

print(f"Songs available: {len(songs)}")

# -----------------------------
# PREPARE SONG GROUPS BY GENRE
# -----------------------------
songs["genre"] = songs["genre"].fillna("Unknown").astype(str).str.strip()
songs["artist"] = songs["artist"].fillna(
    "Unknown Artist").astype(str).str.strip()

genre_groups = {
    genre: group.copy()
    for genre, group in songs.groupby("genre")
}

genres = list(genre_groups.keys())

print(f"Genres available: {len(genres)}")

# -----------------------------
# REMOVE PREVIOUS SYNTHETIC DATA
# -----------------------------
conn.execute(
    "DELETE FROM listening_history WHERE user_id IN "
    "(SELECT id FROM users WHERE email LIKE 'synthetic_user_%@minispotify.local')"
)

conn.execute(
    "DELETE FROM likes WHERE user_id IN "
    "(SELECT id FROM users WHERE email LIKE 'synthetic_user_%@minispotify.local')"
)

conn.execute(
    "DELETE FROM users WHERE email LIKE 'synthetic_user_%@minispotify.local'"
)

conn.commit()

# -----------------------------
# CREATE SYNTHETIC USERS
# -----------------------------
user_ids = []

for i in range(1, SYNTHETIC_USERS + 1):

    name = f"Synthetic User {i}"
    email = f"synthetic_user_{i}@minispotify.local"

    cursor = conn.execute(
        """
        INSERT INTO users (name, email, password_hash)
        VALUES (?, ?, ?)
        """,
        (
            name,
            email,
            "SYNTHETIC_ANALYTICAL_USER"
        )
    )

    user_ids.append(cursor.lastrowid)

conn.commit()

print(f"Synthetic users created: {len(user_ids)}")

# -----------------------------
# GENERATE LISTENING EVENTS
# -----------------------------
activity_rows = []

start_date = datetime.now() - timedelta(days=90)

for user_id in user_ids:

    # Each user gets 1–3 preferred genres.
    preferred_genres = random.sample(
        genres,
        k=min(random.choice([1, 2, 3]), len(genres))
    )

    event_count = random.randint(
        EVENTS_PER_USER_MIN,
        EVENTS_PER_USER_MAX
    )

    current_time = start_date + timedelta(
        days=random.randint(0, 30)
    )

    for _ in range(event_count):

        # 75% of the time select from the user's preferred genres.
        if random.random() < 0.75:
            genre = random.choice(preferred_genres)
        else:
            genre = random.choice(genres)

        genre_songs = genre_groups[genre]

        song = genre_songs.sample(
            n=1,
            random_state=random.randint(0, 1_000_000)
        ).iloc[0]

        song_id = int(song["id"])

        duration = random.randint(30, 300)

        completed = random.random() < 0.65

        liked = random.random() < 0.18

        current_time += timedelta(
            minutes=random.randint(5, 180)
        )

        conn.execute(
            """
            INSERT INTO listening_history
            (
                user_id,
                song_id,
                started_at,
                duration_played,
                completed,
                liked
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                song_id,
                current_time.strftime("%Y-%m-%d %H:%M:%S"),
                duration,
                completed,
                liked
            )
        )

        activity_rows.append(
            {
                "user_id": user_id,
                "song_id": song_id,
                "genre": genre,
                "started_at": current_time,
                "duration_played": duration,
                "completed": completed,
                "liked": liked
            }
        )

conn.commit()

# -----------------------------
# CREATE LIKES
# -----------------------------
liked_pairs = {
    (row["user_id"], row["song_id"])
    for row in activity_rows
    if row["liked"]
}

for user_id, song_id in liked_pairs:
    conn.execute(
        """
        INSERT OR IGNORE INTO likes
        (user_id, song_id)
        VALUES (?, ?)
        """,
        (user_id, song_id)
    )

conn.commit()

# -----------------------------
# SAVE ANALYTICAL CSV
# -----------------------------
activity_df = pd.DataFrame(activity_rows)

activity_df.to_csv(
    ACTIVITY_CSV,
    index=False
)

# -----------------------------
# FINAL REPORT
# -----------------------------
total_users = conn.execute(
    "SELECT COUNT(*) FROM users"
).fetchone()[0]

total_history = conn.execute(
    "SELECT COUNT(*) FROM listening_history"
).fetchone()[0]

total_likes = conn.execute(
    "SELECT COUNT(*) FROM likes"
).fetchone()[0]

conn.close()

print("\n========== ACTIVITY GENERATION ==========")
print(f"Total users in database: {total_users}")
print(f"Synthetic users added: {len(user_ids)}")
print(f"Listening events generated: {len(activity_df)}")
print(f"Likes generated: {len(liked_pairs)}")
print(f"Activity CSV: {ACTIVITY_CSV}")
print("Synthetic data is clearly labeled by email prefix.")
print("==========================================")
