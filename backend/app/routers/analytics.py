from fastapi import APIRouter
from sqlalchemy import text

from app.database import engine

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
)


@router.get("/dashboard")
def dashboard():
    with engine.connect() as conn:

        summary = conn.execute(
            text(
                """
                SELECT
                    (SELECT COUNT(*) FROM users) AS total_users,
                    (SELECT COUNT(*) FROM likes) AS total_likes,
                    COUNT(*) AS total_plays,
                    COALESCE(SUM(duration_played), 0) AS total_seconds,
                    COUNT(DISTINCT user_key) AS active_users,
                    COUNT(DISTINCT song_key) AS active_songs
                FROM fact_listening
                """
            )
        ).mappings().one()

        catalog = conn.execute(
            text(
                """
                SELECT
                    (SELECT COUNT(*) FROM dim_song) AS total_songs,
                    (SELECT COUNT(*) FROM dim_artist) AS total_artists,
                    (SELECT COUNT(*) FROM dim_genre) AS total_genres
                """
            )
        ).mappings().one()

        top_songs = conn.execute(
            text(
                """
                SELECT
                    s.title,
                    a.artist_name,
                    COUNT(*) AS total_plays
                FROM fact_listening f
                JOIN dim_song s
                    ON s.song_key = f.song_key
                JOIN dim_artist a
                    ON a.artist_key = f.artist_key
                GROUP BY s.title, a.artist_name
                ORDER BY total_plays DESC
                LIMIT 10
                """
            )
        ).mappings().all()

        top_artists = conn.execute(
            text(
                """
                SELECT
                    a.artist_name,
                    COUNT(*) AS total_plays
                FROM fact_listening f
                JOIN dim_artist a
                    ON a.artist_key = f.artist_key
                GROUP BY a.artist_name
                ORDER BY total_plays DESC
                LIMIT 10
                """
            )
        ).mappings().all()

        genres = conn.execute(
            text(
                """
                SELECT
                    g.genre_name,
                    COUNT(*) AS total_plays
                FROM fact_listening f
                JOIN dim_genre g
                    ON g.genre_key = f.genre_key
                GROUP BY g.genre_name
                ORDER BY total_plays DESC
                """
            )
        ).mappings().all()

        trends = conn.execute(
            text(
                """
                SELECT
                    d.year,
                    d.month,
                    d.month_name,
                    COUNT(*) AS total_plays,
                    COALESCE(SUM(f.duration_played), 0) AS total_seconds
                FROM fact_listening f
                JOIN dim_date d
                    ON d.date_key = f.date_key
                GROUP BY
                    d.year,
                    d.month,
                    d.month_name
                ORDER BY
                    d.year,
                    d.month
                """
            )
        ).mappings().all()

        users = conn.execute(
            text(
                """
                SELECT
                    u.user_id,
                    u.user_name,
                    COUNT(*) AS total_plays,
                    COALESCE(SUM(f.duration_played), 0) AS total_seconds,
                    COUNT(DISTINCT f.song_key) AS unique_songs,
                    COUNT(DISTINCT f.genre_key) AS unique_genres
                FROM fact_listening f
                JOIN dim_user u
                    ON u.user_key = f.user_key
                GROUP BY u.user_id, u.user_name
                ORDER BY total_plays DESC
                LIMIT 10
                """
            )
        ).mappings().all()

    def clean(rows):
        return [dict(row) for row in rows]

    return {
        "summary": {
            "total_plays": int(summary["total_plays"] or 0),
            "total_seconds": float(summary["total_seconds"] or 0),
            "total_users": int(summary["total_users"] or 0),
            "total_likes": int(summary["total_likes"] or 0),
            "active_users": int(summary["active_users"] or 0),
            "active_songs": int(summary["active_songs"] or 0),
            "total_songs": int(catalog["total_songs"] or 0),
            "total_artists": int(catalog["total_artists"] or 0),
            "total_genres": int(catalog["total_genres"] or 0),
        },
        "top_songs": clean(top_songs),
        "top_artists": clean(top_artists),
        "genres": clean(genres),
        "trends": clean(trends),
        "users": clean(users),
    }