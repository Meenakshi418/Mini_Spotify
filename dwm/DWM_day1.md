# Mini Spotify DWM — Day 1

## 1. Dataset

Dataset:
Free Music Archive (FMA) Metadata

Main source:
tracks.csv

Original file:
data/raw/tracks.csv

Official FMA metadata:
106,574 actual track records

Verified in our downloaded file:
106,575 rows were read initially because the CSV contains an extra header row.

After removing the extra header:
106,574 actual track records

## 2. Data Cleaning

Cleaning script:
dwm/etl/clean_tracks.py

Cleaning steps:

1. Read the two-level FMA CSV header.
2. Remove the extra header row.
3. Standardize the track ID.
4. Remove duplicate track IDs.
5. Remove records missing essential song identity.
6. Standardize important text fields.
7. Handle missing values in important fields.
8. Export the processed dataset.

Results:

Raw rows read:
106,575

Actual tracks:
106,574

Duplicate IDs:
0

Invalid identity rows removed:
1

Cleaned records:
106,573

## 3. Useful FMA fields

Track:
- track ID
- title
- duration
- listens
- favorites
- interest
- genres

Artist:
- artist ID
- artist name

Album:
- album ID
- album title

Genre:
- top genre
- detailed genre information

## 4. Star Schema

Dimensions:

- dim_user
- dim_song
- dim_artist
- dim_genre
- dim_date

Fact:

- fact_listening

## 5. Data Flow

FMA Metadata
    ↓
Pandas Cleaning
    ↓
Processed Music Data
    ↓
dim_song / dim_artist / dim_genre

Mini Spotify Application
    ↓
Listening Events
    ↓
fact_listening

Dimensions + Fact
    ↓
OLAP
    ↓
Analytics

## 6. Planned OLAP Analysis

- Most played songs
- Most played artists
- Listening by genre and month

## 7. Future Data Mining

After the DWM foundation is stable:

- K-Means user segmentation
- Apriori association rules
- Analytics dashboard