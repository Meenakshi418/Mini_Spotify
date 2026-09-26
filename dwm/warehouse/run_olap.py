from pathlib import Path
import sqlite3
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]
WAREHOUSE_DB = BASE_DIR / "dwm" / "warehouse" / "mini_spotify_warehouse.db"
RESULTS_DIR = BASE_DIR / "dwm" / "warehouse" / "results"


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(WAREHOUSE_DB)

    # 1. Most played songs
    most_played_songs = pd.read_sql_query(
        """
        SELECT
            s.title,
            a.artist_name,
            COUNT(*) AS total_plays
        FROM fact_listening f
        JOIN dim_song s
            ON f.song_key = s.song_key
        JOIN dim_artist a
            ON f.artist_key = a.artist_key
        GROUP BY s.title, a.artist_name
        ORDER BY total_plays DESC
        LIMIT 10
        """,
        conn,
    )

    # 2. Most played artists
    most_played_artists = pd.read_sql_query(
        """
        SELECT
            a.artist_name,
            COUNT(*) AS total_plays
        FROM fact_listening f
        JOIN dim_artist a
            ON f.artist_key = a.artist_key
        GROUP BY a.artist_name
        ORDER BY total_plays DESC
        LIMIT 10
        """,
        conn,
    )

    # 3. Listening by genre and month
    listening_by_genre_month = pd.read_sql_query(
        """
        SELECT
            d.year,
            d.month,
            d.month_name,
            g.genre_name,
            COUNT(*) AS total_plays,
            SUM(f.duration_played) AS total_seconds
        FROM fact_listening f
        JOIN dim_date d
            ON f.date_key = d.date_key
        JOIN dim_genre g
            ON f.genre_key = g.genre_key
        GROUP BY
            d.year,
            d.month,
            d.month_name,
            g.genre_name
        ORDER BY
            d.year,
            d.month,
            total_plays DESC
        """,
        conn,
    )

    # 4. User listening patterns
    user_listening_patterns = pd.read_sql_query(
        """
        SELECT
            u.user_id,
            u.user_name,
            COUNT(*) AS total_plays,
            ROUND(SUM(f.duration_played), 2) AS total_seconds,
            ROUND(AVG(f.duration_played), 2) AS average_duration,
            COUNT(DISTINCT f.song_key) AS unique_songs,
            COUNT(DISTINCT f.genre_key) AS unique_genres,
            SUM(CASE WHEN f.completed = 1 THEN 1 ELSE 0 END)
                AS completed_plays,
            SUM(CASE WHEN f.liked = 1 THEN 1 ELSE 0 END)
                AS total_likes,
            ROUND(
                100.0 *
                SUM(CASE WHEN f.completed = 1 THEN 1 ELSE 0 END)
                / COUNT(*),
                2
            ) AS completion_rate
        FROM fact_listening f
        JOIN dim_user u
            ON f.user_key = u.user_key
        GROUP BY u.user_id, u.user_name
        ORDER BY total_plays DESC
        """,
        conn,
    )

    conn.close()

    # Save results
    most_played_songs.to_csv(
        RESULTS_DIR / "most_played_songs.csv",
        index=False,
    )

    most_played_artists.to_csv(
        RESULTS_DIR / "most_played_artists.csv",
        index=False,
    )

    listening_by_genre_month.to_csv(
        RESULTS_DIR / "listening_by_genre_month.csv",
        index=False,
    )

    user_listening_patterns.to_csv(
        RESULTS_DIR / "user_listening_patterns.csv",
        index=False,
    )

    print("\n========== OLAP COMPLETE ==========")

    print("\nMost played songs:")
    print(most_played_songs.to_string(index=False))

    print("\nMost played artists:")
    print(most_played_artists.to_string(index=False))

    print("\nGenre/month rows generated:")
    print(len(listening_by_genre_month))

    print("\nUser listening patterns:")
    print(
        user_listening_patterns.head(10).to_string(index=False)
    )

    print("\nResults saved to:")
    print(RESULTS_DIR)

    print("===================================")


if __name__ == "__main__":
    main()
