# Mini Spotify DWM — Day 2

## 1. Synthetic User Activity

The project uses the FMA metadata dataset for the music dimension data.

To create listening activity for Data Mining and DWM analysis, synthetic analytical user activity was generated.

Important: this activity is clearly documented as synthetic data and is used only for analysis/demo purposes.

### Generated Data

- Users in activity dataset: 199
- Listening events: 11,838
- Likes generated: 2,086
- Songs used: real FMA song IDs
- Genres: real FMA genres
- Listening duration: generated analytical values
- Completed plays: generated analytical values
- Likes: generated analytical values

Output:

`data/processed/synthetic_activity.csv`

Generation script:

`data/generate_user_activity.py`

---

## 2. K-Means User Clustering

K-Means was used to group users according to their listening behavior.

### Features

- listening_frequency
- total_duration
- average_duration
- total_likes
- completed_plays
- unique_songs
- unique_artists
- genre-based listening features

### Model

- Algorithm: K-Means
- Number of clusters: 4
- Random state: 42
- Users analyzed: 199
- Listening events: 11,838

### Evaluation

Silhouette score:

`0.1433`

### Cluster Sizes

| Cluster | Users |
|---|---:|
| 0 | 29 |
| 1 | 98 |
| 2 | 53 |
| 3 | 19 |

### Outputs

- `user_cluster_labels.csv`
- `cluster_sizes.csv`
- `cluster_feature_summary.csv`
- `kmeans_metrics.txt`
- `kmeans_user_clusters.png`
- `kmeans_summary.md`

Script:

`dwm/mining/kmeans_users.py`

---

## 3. Apriori Association Rule Mining

Apriori was used to identify genre combinations and association rules from user listening activity.

Each user's listening history was treated as one transaction.

The items in each transaction are the unique genres listened to by that user.

### Settings

- Activity records: 11,838
- Users: 199
- Transactions used: 199
- Minimum support: 0.10
- Minimum confidence: 0.50

### Results

- Frequent itemsets found: 5,996
- Association rules found: 33,636
- Genres analyzed: 17

Example rule metrics include:

- support
- confidence
- lift

### Outputs

- `apriori_frequent_itemsets.csv`
- `apriori_rules.csv`
- `apriori_summary.md`

Script:

`dwm/mining/apriori_rules.py`

---

## 4. Data Warehouse

A separate SQLite warehouse was created for the DWM layer.

The warehouse combines:

- FMA music metadata
- synthetic Mini Spotify listening events

### Star Schema

Dimensions:

- dim_user
- dim_song
- dim_artist
- dim_genre
- dim_date

Fact:

- fact_listening

### Warehouse Data

- dim_user: 199
- dim_song: 106,573
- dim_artist: 32,635
- dim_genre: 17
- dim_date: 36
- fact_listening: 11,838

Warehouse database:

`dwm/warehouse/mini_spotify_warehouse.db`

The warehouse database is generated locally and is not committed to Git.

Build script:

`dwm/warehouse/build_warehouse.py`

---

## 5. OLAP Analysis

The warehouse was used to perform OLAP analysis on the listening fact table.

### Analysis 1 — Most Played Songs

The top 10 most played songs were calculated by counting listening events.

Example results:

| Song | Artist | Plays |
|---|---|---:|
| Danger In Dependency (Featuring Alena Sola) | Mabafu | 40 |
| Sentimental-Fields 4 Don't Be A Luddy Duddy | The Superfools | 39 |
| The Lion & The Snake | MMFFF | 36 |

Full result:

`dwm/warehouse/results/most_played_songs.csv`

### Analysis 2 — Most Played Artists

The top 10 artists were calculated from listening events.

Example results:

| Artist | Plays |
|---|---:|
| James Kibbie | 198 |
| MMFFF | 179 |
| Glass Candy | 154 |

Full result:

`dwm/warehouse/results/most_played_artists.csv`

### Analysis 3 — Listening by Genre and Month

Listening activity was grouped by:

- year
- month
- month name
- genre
- total plays
- total listening seconds

Rows generated:

`40`

Full result:

`dwm/warehouse/results/listening_by_genre_month.csv`

OLAP runner:

`dwm/warehouse/run_olap.py`

---

## 6. Overall DWM Flow

```text
FMA Metadata
     ↓
Data Cleaning
     ↓
106,573 Cleaned Songs
     ↓
Dimensional Data
     ↓
Mini Spotify Listening Activity
     ↓
Fact Listening
     ↓
Star Schema Warehouse
     ↓
OLAP Analysis
     ↓
K-Means User Clustering
     ↓
Apriori Association Rules