from pathlib import Path
import sys
import pandas as pd
from sqlalchemy import text

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR / "backend"))

from app.database import engine

FMA_FILE = BASE_DIR / "data" / "processed" / "tracks_clean.csv"
ACTIVITY_FILE = BASE_DIR / "data" / "processed" / "synthetic_activity.csv"


def create_tables(conn):
    conn.execute(text("""
        DROP TABLE IF EXISTS fact_listening;
        DROP TABLE IF EXISTS dim_song;
        DROP TABLE IF EXISTS dim_date;
        DROP TABLE IF EXISTS dim_genre;
        DROP TABLE IF EXISTS dim_artist;
        DROP TABLE IF EXISTS dim_user;

        CREATE TABLE dim_user (
            user_key BIGINT PRIMARY KEY,
            user_id BIGINT UNIQUE NOT NULL,
            user_name VARCHAR(100),
            email VARCHAR(255),
            created_at TIMESTAMP
        );

        CREATE TABLE dim_artist (
            artist_key BIGINT PRIMARY KEY,
            source_artist_id BIGINT,
            artist_name VARCHAR(255) NOT NULL
        );

        CREATE TABLE dim_genre (
            genre_key BIGINT PRIMARY KEY,
            genre_name VARCHAR(100) UNIQUE NOT NULL
        );

        CREATE TABLE dim_date (
            date_key INTEGER PRIMARY KEY,
            full_date DATE UNIQUE NOT NULL,
            day INTEGER,
            month INTEGER,
            month_name VARCHAR(20),
            quarter INTEGER,
            year INTEGER
        );

        CREATE TABLE dim_song (
            song_key BIGINT PRIMARY KEY,
            source_track_id BIGINT UNIQUE NOT NULL,
            title VARCHAR(500) NOT NULL,
            artist_key BIGINT,
            genre_key BIGINT,
            album_id BIGINT,
            album_title VARCHAR(500),
            duration_seconds NUMERIC(10,2),
            fma_listens BIGINT,
            fma_favorites BIGINT,
            fma_interest BIGINT,
            FOREIGN KEY (artist_key) REFERENCES dim_artist(artist_key),
            FOREIGN KEY (genre_key) REFERENCES dim_genre(genre_key)
        );

        CREATE TABLE fact_listening (
            listening_key BIGINT PRIMARY KEY,
            user_key BIGINT NOT NULL,
            song_key BIGINT NOT NULL,
            artist_key BIGINT,
            genre_key BIGINT,
            date_key INTEGER NOT NULL,
            started_at TIMESTAMP NOT NULL,
            duration_played NUMERIC(10,2) DEFAULT 0,
            completed BOOLEAN DEFAULT FALSE,
            liked BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (user_key) REFERENCES dim_user(user_key),
            FOREIGN KEY (song_key) REFERENCES dim_song(song_key),
            FOREIGN KEY (artist_key) REFERENCES dim_artist(artist_key),
            FOREIGN KEY (genre_key) REFERENCES dim_genre(genre_key),
            FOREIGN KEY (date_key) REFERENCES dim_date(date_key)
        );

        CREATE INDEX idx_fact_user ON fact_listening(user_key);
        CREATE INDEX idx_fact_song ON fact_listening(song_key);
        CREATE INDEX idx_fact_artist ON fact_listening(artist_key);
        CREATE INDEX idx_fact_genre ON fact_listening(genre_key);
        CREATE INDEX idx_fact_date ON fact_listening(date_key);
    """))


def main():
    print("Reading datasets...")

    fma_df = pd.read_csv(FMA_FILE, low_memory=False)
    activity_df = pd.read_csv(ACTIVITY_FILE)

    print(f"FMA songs loaded: {len(fma_df)}")
    print(f"Activity records loaded: {len(activity_df)}")

    fma_df = fma_df.drop_duplicates(subset=["track_id"]).copy()

    with engine.begin() as conn:
        print("\nCreating PostgreSQL warehouse tables...")
        create_tables(conn)

        user_ids = sorted(activity_df["user_id"].dropna().unique())

        dim_user = pd.DataFrame({
            "user_key": range(1, len(user_ids) + 1),
            "user_id": [int(x) for x in user_ids],
            "user_name": [f"Synthetic User {int(x)}" for x in user_ids],
            "email": [None] * len(user_ids),
            "created_at": [None] * len(user_ids),
        })

        artists = (
            fma_df[["artist_id", "artist_name"]]
            .dropna(subset=["artist_name"])
            .copy()
        )

        artists["artist_name"] = (
            artists["artist_name"]
            .astype(str)
            .str.strip()
        )

        artists = artists.drop_duplicates(
            subset=["artist_id", "artist_name"]
        ).reset_index(drop=True)

        dim_artist = pd.DataFrame({
            "artist_key": range(1, len(artists) + 1),
            "source_artist_id": [
                int(x) if pd.notna(x) else None
                for x in artists["artist_id"]
            ],
            "artist_name": artists["artist_name"],
        })

        genres = sorted(
            x for x in
            fma_df["genre"].dropna().astype(str).str.strip().unique()
            if x and x.lower() != "nan"
        )

        dim_genre = pd.DataFrame({
            "genre_key": range(1, len(genres) + 1),
            "genre_name": genres,
        })

        activity_dates = (
            pd.to_datetime(activity_df["started_at"], errors="coerce")
            .dropna()
            .dt.date
            .unique()
        )

        dim_date_rows = []

        for date_value in sorted(activity_dates):
            month = date_value.month

            dim_date_rows.append({
                "date_key": int(date_value.strftime("%Y%m%d")),
                "full_date": date_value,
                "day": date_value.day,
                "month": month,
                "month_name": date_value.strftime("%B"),
                "quarter": ((month - 1) // 3) + 1,
                "year": date_value.year,
            })

        dim_date = pd.DataFrame(dim_date_rows)

        artist_by_id = {
            int(row.source_artist_id): int(row.artist_key)
            for _, row in dim_artist.iterrows()
            if pd.notna(row.source_artist_id)
        }

        artist_by_name = {
            row.artist_name: int(row.artist_key)
            for _, row in dim_artist.iterrows()
        }

        genre_map = {
            row.genre_name: int(row.genre_key)
            for _, row in dim_genre.iterrows()
        }

        user_map = {
            int(row.user_id): int(row.user_key)
            for _, row in dim_user.iterrows()
        }

        song_rows = []

        for song_key, (_, row) in enumerate(fma_df.iterrows(), start=1):
            artist_key = None

            if pd.notna(row.get("artist_id")):
                artist_key = artist_by_id.get(int(row["artist_id"]))

            if artist_key is None and pd.notna(row.get("artist_name")):
                artist_key = artist_by_name.get(
                    str(row["artist_name"]).strip()
                )

            genre_key = None

            if pd.notna(row.get("genre")):
                genre_key = genre_map.get(
                    str(row["genre"]).strip()
                )

            song_rows.append({
                "song_key": song_key,
                "source_track_id": int(row["track_id"]),
                "title": str(row["title"]),
                "artist_key": artist_key,
                "genre_key": genre_key,
                "album_id": (
                    int(row["album_id"])
                    if pd.notna(row.get("album_id"))
                    else None
                ),
                "album_title": (
                    str(row["album_title"])
                    if pd.notna(row.get("album_title"))
                    else None
                ),
                "duration_seconds": (
                    float(row["duration_seconds"])
                    if pd.notna(row.get("duration_seconds"))
                    else None
                ),
                "fma_listens": (
                    int(row["fma_listens"])
                    if pd.notna(row.get("fma_listens"))
                    else None
                ),
                "fma_favorites": (
                    int(row["fma_favorites"])
                    if pd.notna(row.get("fma_favorites"))
                    else None
                ),
                "fma_interest": (
                    int(row["fma_interest"])
                    if pd.notna(row.get("fma_interest"))
                    else None
                ),
            })

        dim_song = pd.DataFrame(song_rows)

        song_map = dict(
            zip(
                dim_song["source_track_id"].astype(int),
                dim_song["song_key"].astype(int),
            )
        )

        song_lookup = dim_song[
            [
                "source_track_id",
                "song_key",
                "artist_key",
                "genre_key",
            ]
        ].copy()

        activity = activity_df.copy()

        activity["user_key"] = (
            activity["user_id"]
            .astype(int)
            .map(user_map)
        )

        activity = activity.merge(
            song_lookup,
            left_on="song_id",
            right_on="source_track_id",
            how="inner",
        )

        activity["started_at"] = pd.to_datetime(
            activity["started_at"],
            errors="coerce",
        )

        activity = activity.dropna(subset=["started_at"])

        activity["date_key"] = activity["started_at"].dt.strftime(
            "%Y%m%d"
        ).astype(int)

        activity["duration_played"] = pd.to_numeric(
            activity["duration_played"],
            errors="coerce",
        ).fillna(0)

        activity["completed"] = activity["completed"].astype(bool)
        activity["liked"] = activity["liked"].astype(bool)

        fact_listening = pd.DataFrame({
            "listening_key": range(1, len(activity) + 1),
            "user_key": activity["user_key"].astype(int),
            "song_key": activity["song_key"].astype(int),
            "artist_key": activity["artist_key"],
            "genre_key": activity["genre_key"],
            "date_key": activity["date_key"],
            "started_at": activity["started_at"],
            "duration_played": activity["duration_played"],
            "completed": activity["completed"],
            "liked": activity["liked"],
        })

        dim_user.to_sql(
            "dim_user",
            conn,
            if_exists="append",
            index=False,
            chunksize=2000,
            method="multi",
        )

        dim_artist.to_sql(
            "dim_artist",
            conn,
            if_exists="append",
            index=False,
            chunksize=2000,
            method="multi",
        )

        dim_genre.to_sql(
            "dim_genre",
            conn,
            if_exists="append",
            index=False,
            chunksize=2000,
            method="multi",
        )

        dim_date.to_sql(
            "dim_date",
            conn,
            if_exists="append",
            index=False,
            chunksize=2000,
            method="multi",
        )

        dim_song.to_sql(
            "dim_song",
            conn,
            if_exists="append",
            index=False,
            chunksize=2000,
            method="multi",
        )

        fact_listening.to_sql(
            "fact_listening",
            conn,
            if_exists="append",
            index=False,
            chunksize=2000,
            method="multi",
        )

        print("\n========== POSTGRESQL WAREHOUSE COMPLETE ==========")
        print(f"dim_user: {len(dim_user)}")
        print(f"dim_song: {len(dim_song)}")
        print(f"dim_genre: {len(dim_genre)}")
        print(f"dim_artist: {len(dim_artist)}")
        print(f"dim_date: {len(dim_date)}")
        print(f"fact_listening: {len(fact_listening)}")
        print("Database: PostgreSQL")
        print("====================================================")


if __name__ == "__main__":
    main()