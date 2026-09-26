import sqlite3

from app.database import engine
from sqlalchemy import text


SQLITE_DB = "mini_spotify.db"

TABLES = [
    "users",
    "playlists",
    "playlist_songs",
    "likes",
    "listening_history",
]

SEQUENCE_TABLES = [
    "users",
    "songs",
    "playlists",
    "listening_history",
]

def get_sqlite_columns(conn, table):
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return [row[1] for row in rows]


def migrate_table(sqlite_conn, pg_conn, table):
    columns = get_sqlite_columns(sqlite_conn, table)

    rows = sqlite_conn.execute(
        f"SELECT {', '.join(columns)} FROM {table}"
    ).fetchall()

    if not rows:
        print(f"{table}: 0 rows")
        return

    column_list = ", ".join(columns)
    placeholders = ", ".join(f":c{i}" for i in range(len(columns)))

    sql = text(
        f"""
        INSERT INTO {table} ({column_list})
        VALUES ({placeholders})
        ON CONFLICT DO NOTHING
        """
    )

    data = []

    for row in rows:
        converted = {}

        for i, value in enumerate(row):
            column = columns[i]

            if table == "listening_history" and column in {"completed", "liked"}:
                value = None if value is None else bool(value)

            converted[f"c{i}"] = value

        data.append(converted)

    pg_conn.execute(sql, data)
    print(f"{table}: {len(rows)} rows migrated")


def migrate_youtube_ids(sqlite_conn, pg_conn):
    rows = sqlite_conn.execute(
        """
        SELECT id, youtube_video_id
        FROM songs
        WHERE youtube_video_id IS NOT NULL
        """
    ).fetchall()

    for song_id, video_id in rows:
        pg_conn.execute(
            text(
                """
                UPDATE songs
                SET youtube_video_id = :video_id
                WHERE id = :song_id
                """
            ),
            {
                "video_id": video_id,
                "song_id": song_id,
            },
        )

    print(f"youtube_video_id: {len(rows)} mappings migrated")


def reset_sequences(pg_conn):
    for table in SEQUENCE_TABLES:
        result = pg_conn.execute(
            text(
                """
                SELECT pg_get_serial_sequence(
                    :table_name,
                    'id'
                )
                """
            ),
            {"table_name": table},
        ).scalar()

        if result:
            pg_conn.execute(
                text(
                    f"""
                    SELECT setval(
                        :sequence_name,
                        COALESCE(
                            (SELECT MAX(id) FROM {table}),
                            1
                        ),
                        true
                    )
                    """
                ),
                {"sequence_name": result},
            )

            print(f"{table}: sequence reset")

def main():
    sqlite_conn = sqlite3.connect(SQLITE_DB)

    with engine.begin() as pg_conn:
        print("Migrating SQLite → PostgreSQL...\n")

        for table in TABLES:
            migrate_table(sqlite_conn, pg_conn, table)

        migrate_youtube_ids(sqlite_conn, pg_conn)

        reset_sequences(pg_conn)

    sqlite_conn.close()

    print("\nMigration complete.")


if __name__ == "__main__":
    main()