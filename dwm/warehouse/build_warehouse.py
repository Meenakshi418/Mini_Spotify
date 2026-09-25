from pathlib import Path
import sqlite3

import pandas as pd


# Project root
BASE_DIR = Path(__file__).resolve().parents[2]

# Input files
FMA_FILE = BASE_DIR / "data" / "processed" / "tracks_clean.csv"
ACTIVITY_FILE = BASE_DIR / "data" / "processed" / "synthetic_activity.csv"

# Existing application database
APP_DB = BASE_DIR / "backend" / "mini_spotify.db"

# New warehouse database
WAREHOUSE_DB = BASE_DIR / "dwm" / "warehouse" / "mini_spotify_warehouse.db"


def create_tables(conn):
    """Create the DWM star-schema tables."""

    conn.executescript(
        """
        DROP TABLE IF EXISTS fact_listening;
        DROP TABLE IF EXISTS dim_song;
        DROP TABLE IF EXISTS dim_artist;
        DROP TABLE IF EXISTS dim_genre;
        DROP TABLE IF EXISTS dim_date;
        DROP TABLE IF EXISTS dim_user;

        CREATE TABLE dim_user (
            user_key INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            user_name TEXT,
            email TEXT,
            created_at TEXT
        );

        CREATE TABLE dim_artist (
            artist_key INTEGER PRIMARY KEY AUTOINCREMENT,
            source_artist_id INTEGER,
            artist_name TEXT NOT NULL
        );

        CREATE TABLE dim_genre (
            genre_key INTEGER PRIMARY KEY AUTOINCREMENT,
            genre_name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE dim_date (
            date_key INTEGER PRIMARY KEY,
            full_date TEXT UNIQUE NOT NULL,
            day INTEGER,
            month INTEGER,
            month_name TEXT,
            quarter INTEGER,
            year INTEGER
        );

        CREATE TABLE dim_song (
            song_key INTEGER PRIMARY KEY AUTOINCREMENT,
            source_track_id INTEGER UNIQUE NOT NULL,
            title TEXT NOT NULL,
            artist_key INTEGER,
            genre_key INTEGER,
            album_id INTEGER,
            album_title TEXT,
            duration_seconds REAL,
            fma_listens INTEGER,
            fma_favorites INTEGER,
            fma_interest INTEGER,
            FOREIGN KEY (artist_key) REFERENCES dim_artist(artist_key),
            FOREIGN KEY (genre_key) REFERENCES dim_genre(genre_key)
        );

        CREATE TABLE fact_listening (
            listening_key INTEGER PRIMARY KEY AUTOINCREMENT,
            user_key INTEGER NOT NULL,
            song_key INTEGER NOT NULL,
            artist_key INTEGER,
            genre_key INTEGER,
            date_key INTEGER NOT NULL,
            started_at TEXT NOT NULL,
            duration_played REAL DEFAULT 0,
            completed INTEGER DEFAULT 0,
            liked INTEGER DEFAULT 0,
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
        """
    )


def load_dimensions(conn, fma_df, activity_df):
    """Load all dimension tables."""

    # -------------------------
    # DIM USER
    # -------------------------
    user_ids = sorted(activity_df["user_id"].dropna().unique())

    user_rows = [
        (int(user_id), f"Synthetic User {int(user_id)}", None, None)
        for user_id in user_ids
    ]

    conn.executemany(
        """
        INSERT INTO dim_user
        (user_id, user_name, email, created_at)
        VALUES (?, ?, ?, ?)
        """,
        user_rows,
    )

    # -------------------------
    # DIM ARTIST
    # -------------------------
    artists = (
        fma_df[["artist_id", "artist_name"]]
        .dropna(subset=["artist_name"])
        .copy()
    )

    artists["artist_name"] = artists["artist_name"].astype(str).str.strip()

    # Keep one record per artist ID + name
    artists = artists.drop_duplicates(
        subset=["artist_id", "artist_name"]
    )

    artist_rows = []

    for _, row in artists.iterrows():
        artist_id = row["artist_id"]

        if pd.isna(artist_id):
            artist_id = None
        else:
            artist_id = int(artist_id)

        artist_rows.append(
            (
                artist_id,
                row["artist_name"],
            )
        )

    conn.executemany(
        """
        INSERT INTO dim_artist
        (source_artist_id, artist_name)
        VALUES (?, ?)
        """,
        artist_rows,
    )

    # -------------------------
    # DIM GENRE
    # -------------------------
    genres = (
        fma_df["genre"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    genres = sorted(
        genre for genre in genres.unique()
        if genre and genre.lower() != "nan"
    )

    conn.executemany(
        """
        INSERT INTO dim_genre (genre_name)
        VALUES (?)
        """,
        [(genre,) for genre in genres],
    )

    # -------------------------
    # DIM DATE
    # -------------------------
    activity_dates = pd.to_datetime(
        activity_df["started_at"],
        errors="coerce"
    ).dropna().dt.date.unique()

    date_rows = []

    for date_value in sorted(activity_dates):
        year = date_value.year
        month = date_value.month
        day = date_value.day
        quarter = ((month - 1) // 3) + 1
        date_key = int(date_value.strftime("%Y%m%d"))

        date_rows.append(
            (
                date_key,
                date_value.isoformat(),
                day,
                month,
                date_value.strftime("%B"),
                quarter,
                year,
            )
        )

    conn.executemany(
        """
        INSERT INTO dim_date
        (
            date_key,
            full_date,
            day,
            month,
            month_name,
            quarter,
            year
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        date_rows,
    )

    # -------------------------
    # LOOKUP MAPS
    # -------------------------
    artist_map = {}

    rows = conn.execute(
        """
        SELECT artist_key, source_artist_id, artist_name
        FROM dim_artist
        """
    ).fetchall()

    for artist_key, source_artist_id, artist_name in rows:
        if source_artist_id is not None:
            artist_map[("id", int(source_artist_id))] = artist_key

        artist_map[("name", artist_name)] = artist_key

    genre_map = {
        row[1]: row[0]
        for row in conn.execute(
            "SELECT genre_key, genre_name FROM dim_genre"
        ).fetchall()
    }

    user_map = {
        row[1]: row[0]
        for row in conn.execute(
            "SELECT user_key, user_id FROM dim_user"
        ).fetchall()
    }

    date_map = {
        row[1]: row[0]
        for row in conn.execute(
            "SELECT date_key, full_date FROM dim_date"
        ).fetchall()
    }

    # -------------------------
    # DIM SONG
    # -------------------------
    song_rows = []

    for _, row in fma_df.iterrows():

        artist_key = None

        if pd.notna(row["artist_id"]):
            artist_key = artist_map.get(
                ("id", int(row["artist_id"]))
            )

        if artist_key is None and pd.notna(row["artist_name"]):
            artist_key = artist_map.get(
                ("name", str(row["artist_name"]).strip())
            )

        genre_key = None

        if pd.notna(row["genre"]):
            genre_name = str(row["genre"]).strip()
            genre_key = genre_map.get(genre_name)

        song_rows.append(
            (
                int(row["track_id"]),
                str(row["title"]),
                artist_key,
                genre_key,
                int(row["album_id"]) if pd.notna(row["album_id"]) else None,
                str(row["album_title"])
                if pd.notna(row["album_title"])
                else None,
                float(row["duration_seconds"])
                if pd.notna(row["duration_seconds"])
                else None,
                int(row["fma_listens"])
                if pd.notna(row["fma_listens"])
                else None,
                int(row["fma_favorites"])
                if pd.notna(row["fma_favorites"])
                else None,
                int(row["fma_interest"])
                if pd.notna(row["fma_interest"])
                else None,
            )
        )

    conn.executemany(
        """
        INSERT INTO dim_song
        (
            source_track_id,
            title,
            artist_key,
            genre_key,
            album_id,
            album_title,
            duration_seconds,
            fma_listens,
            fma_favorites,
            fma_interest
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        song_rows,
    )

    song_map = {
        row[1]: row[0]
        for row in conn.execute(
            """
            SELECT song_key, source_track_id
            FROM dim_song
            """
        ).fetchall()
    }

    return user_map, artist_map, genre_map, date_map, song_map


def load_fact_table(
    conn,
    activity_df,
    user_map,
    artist_map,
    genre_map,
    date_map,
    song_map,
):
    """Load listening-history events into fact_listening."""

    fact_rows = []

    for _, row in activity_df.iterrows():

        user_key = user_map.get(int(row["user_id"]))
        song_key = song_map.get(int(row["song_id"]))

        if user_key is None or song_key is None:
            continue

        artist_key = None

        genre_name = str(row["genre"]).strip()

        genre_key = genre_map.get(genre_name)

        started_at = pd.to_datetime(
            row["started_at"],
            errors="coerce"
        )

        if pd.isna(started_at):
            continue

        full_date = started_at.date().isoformat()
        date_key = date_map.get(full_date)

        # Get artist/genre from the song dimension.
        song_info = conn.execute(
            """
            SELECT artist_key, genre_key
            FROM dim_song
            WHERE song_key = ?
            """,
            (song_key,),
        ).fetchone()

        if song_info:
            artist_key = song_info[0]

            if genre_key is None:
                genre_key = song_info[1]

        fact_rows.append(
            (
                user_key,
                song_key,
                artist_key,
                genre_key,
                date_key,
                started_at.isoformat(),
                float(row["duration_played"]),
                int(bool(row["completed"])),
                int(bool(row["liked"])),
            )
        )

    conn.executemany(
        """
        INSERT INTO fact_listening
        (
            user_key,
            song_key,
            artist_key,
            genre_key,
            date_key,
            started_at,
            duration_played,
            completed,
            liked
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        fact_rows,
    )

    return len(fact_rows)


def main():
    print("Reading datasets...")

    fma_df = pd.read_csv(FMA_FILE)
    activity_df = pd.read_csv(ACTIVITY_FILE)

    print(f"FMA songs loaded: {len(fma_df)}")
    print(f"Activity records loaded: {len(activity_df)}")

    # Start with a fresh warehouse
    if WAREHOUSE_DB.exists():
        WAREHOUSE_DB.unlink()

    conn = sqlite3.connect(WAREHOUSE_DB)

    try:
        create_tables(conn)

        print("\nLoading dimensions...")

        (
            user_map,
            artist_map,
            genre_map,
            date_map,
            song_map,
        ) = load_dimensions(
            conn,
            fma_df,
            activity_df,
        )

        print(
            "Dimensions loaded:",
            "users =", len(user_map),
            "| artists =", len(artist_map),
            "| genres =", len(genre_map),
            "| dates =", len(date_map),
            "| songs =", len(song_map),
        )

        print("\nLoading fact table...")

        fact_count = load_fact_table(
            conn,
            activity_df,
            user_map,
            artist_map,
            genre_map,
            date_map,
            song_map,
        )

        conn.commit()

        print("\n========== WAREHOUSE BUILD COMPLETE ==========")
        print(f"dim_user: {len(user_map)}")
        print(f"dim_song: {len(song_map)}")
        print(f"dim_genre: {len(genre_map)}")
        print(f"dim_artist: {len(artist_map)}")
        print(f"dim_date: {len(date_map)}")
        print(f"fact_listening: {fact_count}")
        print(f"Warehouse: {WAREHOUSE_DB}")
        print("==============================================")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
