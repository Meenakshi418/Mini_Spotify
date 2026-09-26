from pathlib import Path

import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score


# ---------------------------------------
# PATHS
# ---------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "synthetic_activity.csv"
OUTPUT_DIR = PROJECT_ROOT / "dwm" / "mining" / "results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------
# LOAD ACTIVITY DATA
# ---------------------------------------
df = pd.read_csv("data/processed/synthetic_activity.csv")

conn = sqlite3.connect("backend/mini_spotify.db")
songs = pd.read_sql_query(
    "SELECT id AS song_id, artist FROM songs",
    conn
)
conn.close()

df = df.merge(songs, on="song_id", how="left")

print(f"Activity records loaded: {len(df)}")
print(f"Users found: {df['user_id'].nunique()}")


# ---------------------------------------
# BASIC USER FEATURES
# ---------------------------------------
user_features = (
    df.groupby("user_id")
    .agg(
        listening_frequency=("song_id", "count"),
        total_duration=("duration_played", "sum"),
        average_duration=("duration_played", "mean"),
        total_likes=("liked", "sum"),
        completed_plays=("completed", "sum"),
        unique_songs=("song_id", "nunique"),
        unique_artists=("artist", "nunique"),
    )
    .reset_index()
)


# ---------------------------------------
# GENRE FEATURES
# ---------------------------------------
genre_counts = pd.crosstab(
    df["user_id"],
    df["genre"]
)

genre_counts.columns = [
    f"genre_{str(col).replace(' ', '_').replace('/', '_')}"
    for col in genre_counts.columns
]

genre_counts = genre_counts.reset_index()

user_features = user_features.merge(
    genre_counts,
    on="user_id",
    how="left"
)

user_features = user_features.fillna(0)


# ---------------------------------------
# FEATURES USED FOR K-MEANS
# ---------------------------------------
feature_columns = [
    c for c in user_features.columns
    if c != "user_id"
]

X = user_features[feature_columns]


# ---------------------------------------
# STANDARDIZE
# ---------------------------------------
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)


# ---------------------------------------
# K-MEANS
# ---------------------------------------
K = 4

kmeans = KMeans(
    n_clusters=K,
    random_state=42,
    n_init=20
)

user_features["cluster"] = kmeans.fit_predict(X_scaled)


# ---------------------------------------
# CLUSTER SIZE
# ---------------------------------------
cluster_sizes = (
    user_features["cluster"]
    .value_counts()
    .sort_index()
    .reset_index()
)

cluster_sizes.columns = ["cluster", "user_count"]

cluster_sizes.to_csv(
    OUTPUT_DIR / "cluster_sizes.csv",
    index=False
)


# ---------------------------------------
# CLUSTER FEATURE SUMMARY
# ---------------------------------------
summary = (
    user_features
    .groupby("cluster")[feature_columns]
    .mean()
    .round(2)
)

summary.to_csv(
    OUTPUT_DIR / "cluster_feature_summary.csv"
)


# ---------------------------------------
# SILHOUETTE SCORE
# ---------------------------------------
if len(set(user_features["cluster"])) > 1:
    silhouette = silhouette_score(
        X_scaled,
        user_features["cluster"]
    )
else:
    silhouette = 0

with open(
    OUTPUT_DIR / "kmeans_metrics.txt",
    "w",
    encoding="utf-8"
) as f:
    f.write(f"Number of users: {len(user_features)}\n")
    f.write(f"Number of clusters: {K}\n")
    f.write(f"Silhouette score: {silhouette:.4f}\n")


# ---------------------------------------
# SAVE USER CLUSTER LABELS
# ---------------------------------------
user_features[
    ["user_id", "cluster"]
].to_csv(
    OUTPUT_DIR / "user_cluster_labels.csv",
    index=False
)


# ---------------------------------------
# PCA VISUALIZATION
# ---------------------------------------
pca = PCA(n_components=2, random_state=42)

X_pca = pca.fit_transform(X_scaled)

plt.figure(figsize=(9, 7))

for cluster_id in sorted(user_features["cluster"].unique()):

    mask = user_features["cluster"] == cluster_id

    plt.scatter(
        X_pca[mask, 0],
        X_pca[mask, 1],
        label=f"Cluster {cluster_id}",
        alpha=0.7
    )

plt.xlabel("Principal Component 1")
plt.ylabel("Principal Component 2")
plt.title("Mini Spotify User Clusters - K-Means")
plt.legend()
plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "kmeans_user_clusters.png",
    dpi=200
)

plt.close()


# ---------------------------------------
# SIMPLE DOCUMENTATION
# ---------------------------------------
with open(
    OUTPUT_DIR / "kmeans_summary.md",
    "w",
    encoding="utf-8"
) as f:

    f.write("# K-Means User Clustering\n\n")

    f.write("## Dataset\n")
    f.write(
        f"- Users analyzed: {len(user_features)}\n"
    )
    f.write(
        f"- Listening events: {len(df)}\n"
    )

    f.write("\n## Features\n")

    for feature in feature_columns:
        f.write(f"- {feature}\n")

    f.write("\n## Model\n")
    f.write("- Algorithm: K-Means\n")
    f.write(f"- Number of clusters: {K}\n")
    f.write("- Random state: 42\n")

    f.write("\n## Evaluation\n")
    f.write(
        f"- Silhouette score: {silhouette:.4f}\n"
    )

    f.write("\n## Outputs\n")
    f.write("- user_cluster_labels.csv\n")
    f.write("- cluster_sizes.csv\n")
    f.write("- cluster_feature_summary.csv\n")
    f.write("- kmeans_metrics.txt\n")
    f.write("- kmeans_user_clusters.png\n")

print("\n========== K-MEANS COMPLETE ==========")
print(f"Users analyzed: {len(user_features)}")
print(f"Clusters: {K}")
print(f"Silhouette score: {silhouette:.4f}")
print("\nCluster sizes:")
print(cluster_sizes.to_string(index=False))
print("\nResults saved to:")
print(OUTPUT_DIR)
print("======================================")
