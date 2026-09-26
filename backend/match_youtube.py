import os
import requests
from pathlib import Path

from app.database import SessionLocal
from app.models import Song


# -------------------------------------------------
# LOAD API KEY FROM .env
# -------------------------------------------------

env_file = Path(__file__).with_name(".env")

for line in env_file.read_text().splitlines():
    line = line.strip()

    if line.startswith("YOUTUBE_API_KEY="):
        os.environ["YOUTUBE_API_KEY"] = line.split("=", 1)[1].strip()
        break

api_key = os.getenv("YOUTUBE_API_KEY")

if not api_key:
    raise SystemExit("YOUTUBE_API_KEY not found in .env")


# -------------------------------------------------
# YOUTUBE SEARCH
# -------------------------------------------------

def find_video(title, artist):
    query = f'"{title}" "{artist}"'

    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": 5,
        "key": api_key,
    }

    response = requests.get(
        "https://www.googleapis.com/youtube/v3/search",
        params=params,
        timeout=15,
    )

    response.raise_for_status()

    items = response.json().get("items", [])

    if not items:
        return None

    for item in items:
        video_title = item["snippet"]["title"].lower()

        if title.lower() in video_title or artist.lower() in video_title:
            return {
                "video_id": item["id"]["videoId"],
                "title": item["snippet"]["title"],
            }

    # If nothing looks like a reasonable match, don't save a random video.
    return None


# -------------------------------------------------
# MATCH 10 SONGS
# -------------------------------------------------

db = SessionLocal()

try:
    songs = (
        db.query(Song)
        .filter(Song.youtube_video_id.is_(None))
        .order_by(Song.popularity.desc())
        .limit(100)
        .all()
    )

    print(f"Found {len(songs)} songs to match.\n")

    for song in songs:

        print("=" * 60)
        print(f"FMA SONG : {song.title}")
        print(f"ARTIST   : {song.artist}")

        result = find_video(
            song.title,
            song.artist,
        )

        if not result:
            print("YouTube  : No result found")
            continue

        print(f"YouTube  : {result['title']}")
        print(f"Video ID : {result['video_id']}")

        # Save the matched video ID
        song.youtube_video_id = result["video_id"]

        db.commit()

        print("STATUS   : Saved")

finally:
    db.close()

print("\nYouTube matching test complete.")