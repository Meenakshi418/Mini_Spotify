import sqlite3

conn = sqlite3.connect("mini_spotify.db")
cursor = conn.cursor()

cursor.execute(
    """
    UPDATE songs
    SET youtube_video_id = ?
    WHERE id = ?
    """,
    ("uvY8fdgezLQ", 1)
)

conn.commit()
conn.close()

print("YouTube video ID updated successfully.")