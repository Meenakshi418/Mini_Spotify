import os
import requests
from pathlib import Path


# Read API key from backend/.env
env_file = Path(__file__).with_name(".env")

for line in env_file.read_text().splitlines():
    line = line.strip()

    if line.startswith("YOUTUBE_API_KEY="):
        os.environ["YOUTUBE_API_KEY"] = line.split("=", 1)[1].strip()
        break


api_key = os.getenv("YOUTUBE_API_KEY")

if not api_key:
    raise SystemExit("YOUTUBE_API_KEY not found in .env")


params = {
    "part": "snippet",
    "q": "Night Owl Broke For Free",
    "type": "video",
    "maxResults": 1,
    "key": api_key,
}


response = requests.get(
    "https://www.googleapis.com/youtube/v3/search",
    params=params,
    timeout=15,
)

print("Status:", response.status_code)

data = response.json()

if response.status_code != 200:
    print(data)
    raise SystemExit("YouTube API request failed.")

items = data.get("items", [])

if not items:
    print("No video found.")
else:
    video_id = items[0]["id"]["videoId"]
    title = items[0]["snippet"]["title"]

    print("Video:", title)
    print("Video ID:", video_id)