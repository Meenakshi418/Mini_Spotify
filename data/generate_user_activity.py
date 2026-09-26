from pathlib import Path
import random
import sys
from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy import select, func

# ---------------------------------------------------------
# PROJECT PATH
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Allow importing backend.app from this script
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.database import SessionLocal
from backend.app.models import User, Song, ListeningHistory, Like


# ---------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------

RANDOM_SEED = 42

# Existing demo user + 199 synthetic users = ~200 total
SYNTHETIC_USERS = 199

EVENTS_PER_USER_MIN = 40
EVENTS_PER_USER_MAX = 80

random.seed(RANDOM_SEED)


# ---------------------------------------------------------
# OUTPUT
# ---------------------------------------------------------

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ACTIVITY_CSV = OUTPUT_DIR / "synthetic_activity.csv"


# ---------------------------------------------------------
# DATABASE
# ---------------------------------------------------------

db = SessionLocal()

try:

    # -----------------------------------------------------
    # LOAD REAL SONGS FROM POSTGRESQL
    # -----------------------------------------------------

    song_rows = db.execute(
        select(
            Song.id,
            Song.title,
            Song.artist,
            Song.genre,
            Song.popularity,
        )
    ).all()

    if not song_rows:
        raise RuntimeError("No songs found in PostgreSQL.")

    print(f"Songs available: {len(song_rows)}")

    # Convert to dataframe for easier handling
    songs = pd.DataFrame(
        song_rows,
        columns=[
            "id",
            "title",
            "artist",
            "genre",
            "popularity",
        ],
    )

    songs["genre"] = (
        songs["genre"]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
    )

    songs["artist"] = (
        songs["artist"]
        .fillna("Unknown Artist")
        .astype(str)
        .str.strip()
    )

    # -----------------------------------------------------
    # GROUP SONGS BY GENRE
    # -----------------------------------------------------

    genre_groups = {
        genre: group
        for genre, group in songs.groupby("genre")
    }

    genres = list(genre_groups.keys())

    if not genres:
        raise RuntimeError("No usable genres found.")

    print(f"Genres available: {len(genres)}")


    # -----------------------------------------------------
    # REMOVE PREVIOUS SYNTHETIC DATA
    # -----------------------------------------------------

    synthetic_pattern = "synthetic_user_%@minispotify.local"

    synthetic_users = (
        db.query(User)
        .filter(User.email.like(synthetic_pattern))
        .all()
    )

    synthetic_user_ids = [user.id for user in synthetic_users]

    if synthetic_user_ids:

        db.query(ListeningHistory).filter(
            ListeningHistory.user_id.in_(synthetic_user_ids)
        ).delete(synchronize_session=False)

        db.query(Like).filter(
            Like.user_id.in_(synthetic_user_ids)
        ).delete(synchronize_session=False)

        db.query(User).filter(
            User.id.in_(synthetic_user_ids)
        ).delete(synchronize_session=False)

        db.commit()

        print(
            f"Removed previous synthetic users: "
            f"{len(synthetic_user_ids)}"
        )


    # -----------------------------------------------------
    # CREATE SYNTHETIC USERS
    # -----------------------------------------------------

    user_ids = []

    for i in range(1, SYNTHETIC_USERS + 1):

        user = User(
            name=f"Synthetic User {i}",
            email=f"synthetic_user_{i}@minispotify.local",
            password_hash="SYNTHETIC_ANALYTICAL_USER",
        )

        db.add(user)
        db.flush()

        user_ids.append(user.id)

    db.commit()

    print(
        f"Synthetic users created: "
        f"{len(user_ids)}"
    )


    # -----------------------------------------------------
    # GENERATE LISTENING EVENTS
    # -----------------------------------------------------

    activity_rows = []

    start_date = datetime.now() - timedelta(days=90)

    for user_id in user_ids:

        # Each synthetic user prefers 1–3 genres
        preferred_genres = random.sample(
            genres,
            k=min(
                random.choice([1, 2, 3]),
                len(genres)
            ),
        )

        event_count = random.randint(
            EVENTS_PER_USER_MIN,
            EVENTS_PER_USER_MAX,
        )

        current_time = start_date + timedelta(
            days=random.randint(0, 30)
        )

        for _ in range(event_count):

            # 75% preferred genre
            if random.random() < 0.75:
                genre = random.choice(preferred_genres)
            else:
                genre = random.choice(genres)

            genre_songs = genre_groups[genre]

            song = genre_songs.sample(
                n=1,
                random_state=random.randint(
                    0,
                    1_000_000
                ),
            ).iloc[0]

            song_id = int(song["id"])

            duration = random.randint(30, 300)

            completed = random.random() < 0.65

            liked = random.random() < 0.18

            current_time += timedelta(
                minutes=random.randint(5, 180)
            )

            history = ListeningHistory(
                user_id=user_id,
                song_id=song_id,
                started_at=current_time,
                duration_played=duration,
                completed=completed,
                liked=liked,
            )

            db.add(history)

            activity_rows.append(
                {
                    "user_id": user_id,
                    "song_id": song_id,
                    "genre": genre,
                    "started_at": current_time,
                    "duration_played": duration,
                    "completed": completed,
                    "liked": liked,
                }
            )

    db.commit()

    print(
        f"Listening events generated: "
        f"{len(activity_rows)}"
    )


    # -----------------------------------------------------
    # CREATE PERSISTENT LIKES
    # -----------------------------------------------------

    liked_pairs = {
        (row["user_id"], row["song_id"])
        for row in activity_rows
        if row["liked"]
    }

    for user_id, song_id in liked_pairs:

        existing_like = (
            db.query(Like)
            .filter(
                Like.user_id == user_id,
                Like.song_id == song_id,
            )
            .first()
        )

        if not existing_like:
            db.add(
                Like(
                    user_id=user_id,
                    song_id=song_id,
                )
            )

    db.commit()

    print(
        f"Likes generated: "
        f"{len(liked_pairs)}"
    )


    # -----------------------------------------------------
    # SAVE ANALYTICAL CSV
    # -----------------------------------------------------

    activity_df = pd.DataFrame(activity_rows)

    activity_df.to_csv(
        ACTIVITY_CSV,
        index=False,
    )


    # -----------------------------------------------------
    # FINAL REPORT
    # -----------------------------------------------------

    total_users = db.query(User).count()

    total_history = (
        db.query(ListeningHistory).count()
    )

    total_likes = db.query(Like).count()

    print("\n==========================================")
    print("       SYNTHETIC ACTIVITY GENERATION")
    print("==========================================")
    print(f"Total users in PostgreSQL: {total_users}")
    print(f"Synthetic users added: {len(user_ids)}")
    print(f"Listening events generated: {len(activity_df)}")
    print(f"Likes generated: {len(liked_pairs)}")
    print(f"Activity CSV: {ACTIVITY_CSV}")
    print("------------------------------------------")
    print("Synthetic users use:")
    print("synthetic_user_<number>@minispotify.local")
    print("==========================================")

finally:
    db.close()