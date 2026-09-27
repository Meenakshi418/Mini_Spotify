from pathlib import Path
import csv
import random
import re
import sys
from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy import select

PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.database import SessionLocal
from app.models import Like, ListeningHistory, Playlist, PlaylistSong, Song, User
from app.security import hash_password


RANDOM_SEED = 42

USER_COUNT = 199
USER_PASSWORD = "Music1234!"

EVENTS_PER_USER_MIN = 40
EVENTS_PER_USER_MAX = 80

random.seed(RANDOM_SEED)

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ACTIVITY_CSV = OUTPUT_DIR / "synthetic_activity.csv"
GENERATED_USERS_CSV = OUTPUT_DIR / "generated_users.csv"


FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Arjun", "Rohan",
    "Ishaan", "Kabir", "Reyansh", "Krish", "Dhruv",
    "Kunal", "Rahul", "Aman", "Sahil", "Yash",
    "Neel", "Aryan", "Varun", "Akash", "Dev",
    "Ananya", "Aanya", "Isha", "Meera", "Diya",
    "Riya", "Aadhya", "Myra", "Kiara", "Sara",
    "Anika", "Nisha", "Tanya", "Pooja", "Sneha",
    "Kavya", "Shreya", "Simran", "Avni", "Mahi",
    "Prisha", "Navya", "Sana", "Ritika", "Aditi",
    "Mira", "Saanvi", "Ira", "Pallavi", "Neha",
]

LAST_NAMES = [
    "Sharma", "Verma", "Patil", "Shah", "Mehta",
    "Joshi", "Kulkarni", "Deshmukh", "Kapoor", "Malhotra",
    "Gupta", "Agarwal", "Singh", "Chauhan", "Pawar",
    "Jadhav", "More", "Bansal", "Kadam", "Mishra",
    "Rao", "Nair", "Iyer", "Menon", "Saxena",
    "Chopra", "Sethi", "Khanna", "Arora", "Bhat",
    "Naik", "Sawant", "Salunkhe", "Gaikwad", "Shetty",
    "Desai", "Gokhale", "Tiwari", "Pandey", "Reddy",
    "Khan", "Patel", "Vyas", "Thakur", "Yadav",
    "Mhatre", "Dighe",
]

name_pool = [
    f"{first} {last}"
    for first in FIRST_NAMES
    for last in LAST_NAMES
]

random.shuffle(name_pool)
generated_names = name_pool[:USER_COUNT]

password_hash = hash_password(USER_PASSWORD)

db = SessionLocal()

try:
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

    genre_groups = {
        genre: group
        for genre, group in songs.groupby("genre")
    }

    genres = list(genre_groups.keys())

    if not genres:
        raise RuntimeError("No usable genres found.")

    print(f"Genres available: {len(genres)}")

    # Find users created by earlier versions of this generator.
    old_users = db.query(User).filter(
        (User.email.like("synthetic_user_%@minispotify.local")) |
        (User.email.like("synthetic_%@analytics.local"))
    ).all()

    old_emails = {
        user.email
        for user in old_users
    }

    # Also include users recorded in generated_users.csv.
    if GENERATED_USERS_CSV.exists():
        previous_users_df = pd.read_csv(GENERATED_USERS_CSV)

        if "email" in previous_users_df.columns:
            old_emails.update(
                previous_users_df["email"]
                .dropna()
                .astype(str)
                .tolist()
            )

    previous_users = []

    if old_emails:
        previous_users = (
            db.query(User)
            .filter(User.email.in_(list(old_emails)))
            .all()
        )

    previous_user_ids = [
        user.id
        for user in previous_users
    ]

    if previous_user_ids:
        # Delete playlist entries before deleting playlists/users.
        playlist_ids = [
            playlist.id
            for playlist in db.query(Playlist)
            .filter(Playlist.user_id.in_(previous_user_ids))
            .all()
        ]

        if playlist_ids:
            db.query(PlaylistSong).filter(
                PlaylistSong.playlist_id.in_(playlist_ids)
            ).delete(
                synchronize_session=False
            )

            db.query(Playlist).filter(
                Playlist.id.in_(playlist_ids)
            ).delete(
                synchronize_session=False
            )

        db.query(ListeningHistory).filter(
            ListeningHistory.user_id.in_(previous_user_ids)
        ).delete(
            synchronize_session=False
        )

        db.query(Like).filter(
            Like.user_id.in_(previous_user_ids)
        ).delete(
            synchronize_session=False
        )

        db.query(User).filter(
            User.id.in_(previous_user_ids)
        ).delete(
            synchronize_session=False
        )

        db.commit()

        print(
            f"Removed previous generated users: "
            f"{len(previous_user_ids)}"
        )
    else:
        print("No previous generated users found.")

    # Create 199 normal-looking users.
    user_ids = []
    generated_user_rows = []

    for i in range(1, USER_COUNT + 1):
        name = generated_names[i - 1]

        email_name = re.sub(
            r"[^a-z0-9]+",
            ".",
            name.lower(),
        ).strip(".")

        email = (
            f"{email_name}{i:02d}"
            "@minispotify.local"
        )

        user = User(
            name=name,
            email=email,
            password_hash=password_hash,
            role="user",
        )

        db.add(user)
        db.flush()

        user_ids.append(user.id)

        generated_user_rows.append(
            {
                "user_id": user.id,
                "name": name,
                "email": email,
            }
        )

    db.commit()

    print(f"Users created: {len(user_ids)}")

    pd.DataFrame(
        generated_user_rows
    ).to_csv(
        GENERATED_USERS_CSV,
        index=False,
    )

    activity_rows = []

    start_date = datetime.now() - timedelta(days=90)

    for user_id in user_ids:

        preferred_genres = random.sample(
            genres,
            k=min(
                random.choice([1, 2, 3]),
                len(genres),
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

            if random.random() < 0.75:
                genre = random.choice(
                    preferred_genres
                )
            else:
                genre = random.choice(genres)

            genre_songs = genre_groups[genre]

            song = genre_songs.sample(
                n=1,
                random_state=random.randint(
                    0,
                    1_000_000,
                ),
            ).iloc[0]

            song_id = int(song["id"])

            duration = random.randint(
                30,
                300,
            )

            completed = (
                random.random() < 0.65
            )

            liked = (
                random.random() < 0.18
            )

            current_time += timedelta(
                minutes=random.randint(
                    5,
                    180,
                )
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

    liked_pairs = {
        (
            row["user_id"],
            row["song_id"],
        )
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

    activity_df = pd.DataFrame(
        activity_rows
    )

    activity_df.to_csv(
        ACTIVITY_CSV,
        index=False,
    )

    total_users = db.query(User).count()
    total_history = db.query(ListeningHistory).count()
    total_likes = db.query(Like).count()

    print()
    print("USER ACTIVITY GENERATION")
    print("-----------------------")
    print(
        f"Total users in PostgreSQL: "
        f"{total_users}"
    )
    print(
        f"Generated users added: "
        f"{len(user_ids)}"
    )
    print(
        f"Listening events generated: "
        f"{len(activity_df)}"
    )
    print(
        f"Likes generated: "
        f"{len(liked_pairs)}"
    )
    print(
        f"Total history rows: "
        f"{total_history}"
    )
    print(
        f"Total like rows: "
        f"{total_likes}"
    )
    print(
        f"User list CSV: "
        f"{GENERATED_USERS_CSV}"
    )
    print(
        f"Activity CSV: "
        f"{ACTIVITY_CSV}"
    )
    print(
        f"Login password for generated users: "
        f"{USER_PASSWORD}"
    )

finally:
    db.close()