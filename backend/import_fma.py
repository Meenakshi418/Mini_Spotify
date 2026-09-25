import os
import pandas as pd
import numpy as np

from app.database import SessionLocal
from app.models import Song, Like, ListeningHistory, PlaylistSong


CSV_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "data",
    "processed",
    "tracks_clean.csv",
)


def clean_value(value):
    if pd.isna(value):
        return None

    value = str(value).strip()

    if not value or value.lower() in {"nan", "none"}:
        return None

    return value


def main():
    print("Reading FMA dataset...")
    print(f"File: {CSV_PATH}")

    # FMA uses a multi-level header.
    df = pd.read_csv(
        CSV_PATH,
        low_memory=False,
    )

    required = [
        "track_id",
        "title",
        "artist_name",
        "album_title",
        "duration_seconds",
        "genre",
        "fma_listens",
    ]

    missing = [column for column in required if column not in df.columns]

    if missing:
        print("\nMissing columns:")
        for column in missing:
            print(" -", column)

        print("\nAvailable columns:")
        for column in df.columns:
            print(" -", column)

        raise SystemExit("FMA column mapping failed.")

    # -------------------------------------------------
    # CLEAN / CONVERT
    # -------------------------------------------------

    df["duration_seconds"] = pd.to_numeric(
        df["duration_seconds"],
        errors="coerce",
    )

    df["fma_listens"] = pd.to_numeric(
        df["fma_listens"],
        errors="coerce",
    ).fillna(0)

    df["release_year"] = None

    # Remove invalid IDs/titles.
    df = df.dropna(
        subset=[
            "track_id",
            "title",
        ]
    )

    df["track_id"] = df["track_id"].astype(int)

    # Remove duplicate track IDs.
    df = df.drop_duplicates(
        subset=["track_id"]
    )

    # -------------------------------------------------
    # POPULARITY
    # -------------------------------------------------

    # FMA listens can vary enormously, so use log scaling
    # and convert the result to 0-100 for your frontend.
    listens_log = np.log1p(df["fma_listens"])

    min_value = listens_log.min()
    max_value = listens_log.max()

    if max_value > min_value:
        df["popularity"] = (
            (listens_log - min_value)
            / (max_value - min_value)
            * 100
        )
    else:
        df["popularity"] = 0

    df["popularity"] = (
        df["popularity"]
        .round()
        .astype(int)
    )

    # -------------------------------------------------
    # DATABASE
    # -------------------------------------------------

    db = SessionLocal()

    try:
        print("\nClearing demo song data...")

        # Remove dependent rows first.
        db.query(PlaylistSong).delete(
            synchronize_session=False
        )

        db.query(Like).delete(
            synchronize_session=False
        )

        db.query(ListeningHistory).delete(
            synchronize_session=False
        )

        # Remove existing songs.
        db.query(Song).delete(
            synchronize_session=False
        )

        db.commit()

        print("Demo songs removed.")
        print("Starting FMA import...\n")

        records = []

        has_duration = hasattr(Song, "duration")

        for _, row in df.iterrows():

            title = clean_value(row["title"])

            if not title:
                continue

            artist = (
                clean_value(row["artist_name"])
                or "Unknown Artist"
            )

            album = (
                clean_value(row["album_title"])
                or "Unknown Album"
            )

            genre = (
                clean_value(row["genre"])
                or "Unknown"
            )

            release_year = None

            if pd.notna(row["release_year"]):
                release_year = int(
                    row["release_year"]
                )

            record = {
                "id": int(row["track_id"]),
                "title": title,
                "artist": artist,
                "album": album,
                "genre": genre,
                "release_year": release_year,
                "popularity": int(row["popularity"]),
                "youtube_video_id": None,
            }

            if has_duration:
                duration = row["duration_seconds"]

                if pd.notna(duration):
                    record["duration"] = float(duration)
                else:
                    record["duration"] = 0

            records.append(record)

            # Insert in batches.
            if len(records) >= 2000:
                db.bulk_insert_mappings(
                    Song,
                    records,
                )

                db.commit()

                print(
                    f"Imported {len(records):,} tracks in current batch..."
                )

                records = []

        # Remaining records.
        if records:
            db.bulk_insert_mappings(
                Song,
                records,
            )

            db.commit()

        total = db.query(Song).count()

        print("\n===================================")
        print("FMA IMPORT COMPLETE")
        print("===================================")
        print(f"Songs in database: {total:,}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()