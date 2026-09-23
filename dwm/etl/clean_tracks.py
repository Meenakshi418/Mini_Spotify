from pathlib import Path
import pandas as pd

# Find the project folder
PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_FILE = PROJECT_ROOT / "data" / "raw" / "tracks.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = OUTPUT_DIR / "tracks_clean.csv"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("Reading raw dataset...")
df = pd.read_csv(
    RAW_FILE,
    header=[0, 1],
    low_memory=False
)

print("Rows read:", len(df))

# The first row is an extra "track_id" header row
df = df.iloc[1:].copy()

# Rename the first column
columns = ["track_id"]

# Flatten the remaining two-level column names
for col in df.columns[1:]:
    columns.append(f"{col[0]}_{col[1]}")

df.columns = columns

# Convert ID to numeric
df["track_id"] = pd.to_numeric(df["track_id"], errors="coerce")

# Remove invalid IDs
df = df.dropna(subset=["track_id"])

# Make IDs integers
df["track_id"] = df["track_id"].astype(int)

# Remove duplicate tracks
before_duplicates = len(df)
df = df.drop_duplicates(subset=["track_id"])
duplicates_removed = before_duplicates - len(df)

# Rename useful fields
df = df.rename(columns={
    "track_title": "title",
    "track_genre_top": "genre",
    "track_genres": "genres",
    "track_genres_all": "genres_all",
    "track_duration": "duration_seconds",
    "track_listens": "fma_listens",
    "track_favorites": "fma_favorites",
    "track_interest": "fma_interest",
    "artist_id": "artist_id",
    "artist_name": "artist_name",
    "album_id": "album_id",
    "album_title": "album_title"
})

# Keep only fields useful for Mini Spotify + DWM
wanted_columns = [
    "track_id",
    "title",
    "artist_id",
    "artist_name",
    "album_id",
    "album_title",
    "genre",
    "genres",
    "genres_all",
    "duration_seconds",
    "fma_listens",
    "fma_favorites",
    "fma_interest"
]

available_columns = [c for c in wanted_columns if c in df.columns]
df = df[available_columns].copy()

# Remove rows without essential song identity
before_identity = len(df)

df = df.dropna(
    subset=["track_id", "title", "artist_name"]
)

identity_removed = before_identity - len(df)

# Fill useful text fields
if "genre" in df.columns:
    df["genre"] = df["genre"].fillna("Unknown")

if "album_title" in df.columns:
    df["album_title"] = df["album_title"].fillna("Unknown Album")

# Clean text
for column in ["title", "artist_name", "album_title", "genre"]:
    if column in df.columns:
        df[column] = df[column].astype(str).str.strip()

# Convert useful numeric fields
for column in [
    "duration_seconds",
    "fma_listens",
    "fma_favorites",
    "fma_interest"
]:
    if column in df.columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        ).fillna(0)

# Save cleaned dataset
df.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\n========== CLEANING REPORT ==========")
print("Original rows read:", 106575)
print("Actual track records:", 106574)
print("Duplicate IDs removed:", duplicates_removed)
print("Invalid identity rows removed:", identity_removed)
print("Final cleaned records:", len(df))
print("Unique track IDs:", df["track_id"].nunique())
print("Missing track IDs:", df["track_id"].isna().sum())
print("Output:", OUTPUT_FILE)
print("=====================================")
