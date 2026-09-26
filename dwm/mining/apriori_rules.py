from pathlib import Path

import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules


BASE_DIR = Path(__file__).resolve().parents[2]

ACTIVITY_FILE = BASE_DIR / "data" / "processed" / "synthetic_activity.csv"
FMA_FILE = BASE_DIR / "data" / "processed" / "tracks_clean.csv"
RESULTS_DIR = BASE_DIR / "dwm" / "mining" / "results"

MIN_SUPPORT = 0.01
MIN_CONFIDENCE = 0.20
TOP_SONGS = 100


def main():
    print("Reading listening activity...")

    df = pd.read_csv(ACTIVITY_FILE)

    print(f"Activity records loaded: {len(df)}")
    print(f"Users found: {df['user_id'].nunique()}")

    # Load real song titles and artists from the cleaned FMA dataset
    songs = pd.read_csv(
        FMA_FILE,
        usecols=["track_id", "title", "artist_name"],
    )

    songs = songs.rename(
        columns={
            "track_id": "song_id",
            "artist_name": "artist",
        }
    )

    songs["song_id"] = songs["song_id"].astype(int)
    df["song_id"] = df["song_id"].astype(int)

    # Count how many different users listened to each song
    song_user_counts = (
        df.groupby("song_id")["user_id"]
        .nunique()
        .sort_values(ascending=False)
    )

    # Keep the most widely co-listened songs
    top_song_ids = song_user_counts.head(TOP_SONGS).index.tolist()

    df = df[df["song_id"].isin(top_song_ids)].copy()

    print(f"Songs selected for Apriori: {df['song_id'].nunique()}")

    # One transaction = one user
    # Items = unique songs listened to by that user
    transactions = (
        df.groupby("user_id")["song_id"]
        .apply(
            lambda song_ids: sorted(
                set(int(song_id) for song_id in song_ids)
            )
        )
        .tolist()
    )

    # Keep only users who listened to at least 2 selected songs
    transactions = [
        items for items in transactions
        if len(items) >= 2
    ]

    print(f"Transactions used: {len(transactions)}")

    if not transactions:
        print("No transactions contain at least 2 songs.")
        return

    # Convert transactions into True/False table
    encoder = TransactionEncoder()

    encoded_data = encoder.fit(transactions).transform(transactions)

    basket = pd.DataFrame(
        encoded_data,
        columns=encoder.columns_,
    )

    # Find frequent song combinations
    frequent_itemsets = apriori(
        basket,
        min_support=MIN_SUPPORT,
        use_colnames=True,
        max_len=2,
    )

    frequent_itemsets["item_count"] = frequent_itemsets[
        "itemsets"
    ].apply(len)

    # Generate association rules
    if len(frequent_itemsets) > 0:
        rules = association_rules(
            frequent_itemsets,
            metric="confidence",
            min_threshold=MIN_CONFIDENCE,
        )
    else:
        rules = pd.DataFrame()

    # Create song lookup: song_id -> title + artist
    song_lookup = (
        songs.set_index("song_id")[["title", "artist"]]
        .to_dict("index")
    )

    def format_song_ids(items):
        return ", ".join(
            str(int(song_id))
            for song_id in sorted(items)
        )

    def format_song_names(items):
        names = []

        for song_id in sorted(items):
            info = song_lookup.get(int(song_id))

            if info:
                title = str(info["title"])
                artist = str(info["artist"])
                names.append(f"{title} — {artist}")
            else:
                names.append(f"Song ID {int(song_id)}")

        return " | ".join(names)

    # Prepare readable frequent itemsets
    itemsets_output = frequent_itemsets.copy()

    itemsets_output["song_ids"] = itemsets_output[
        "itemsets"
    ].apply(format_song_ids)

    itemsets_output["songs"] = itemsets_output[
        "itemsets"
    ].apply(format_song_names)

    itemsets_output = itemsets_output[
        [
            "song_ids",
            "songs",
            "support",
            "item_count",
        ]
    ]

    itemsets_output = itemsets_output.sort_values(
        ["item_count", "support"],
        ascending=[True, False],
    )

    # Prepare readable association rules
    if len(rules) > 0:
        rules_output = rules.copy()

        rules_output["antecedent_song_ids"] = rules_output[
            "antecedents"
        ].apply(format_song_ids)

        rules_output["consequent_song_ids"] = rules_output[
            "consequents"
        ].apply(format_song_ids)

        rules_output["antecedent_songs"] = rules_output[
            "antecedents"
        ].apply(format_song_names)

        rules_output["consequent_songs"] = rules_output[
            "consequents"
        ].apply(format_song_names)

        rules_output = rules_output[
            [
                "antecedent_song_ids",
                "antecedent_songs",
                "consequent_song_ids",
                "consequent_songs",
                "support",
                "confidence",
                "lift",
            ]
        ]

        rules_output = rules_output.sort_values(
            ["lift", "confidence"],
            ascending=[False, False],
        )

    else:
        rules_output = pd.DataFrame(
            columns=[
                "antecedent_song_ids",
                "antecedent_songs",
                "consequent_song_ids",
                "consequent_songs",
                "support",
                "confidence",
                "lift",
            ]
        )

    # Create results folder
    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Output files
    itemsets_file = RESULTS_DIR / "apriori_frequent_itemsets.csv"
    rules_file = RESULTS_DIR / "apriori_rules.csv"
    summary_file = RESULTS_DIR / "apriori_summary.md"

    itemsets_output.to_csv(
        itemsets_file,
        index=False,
    )

    rules_output.to_csv(
        rules_file,
        index=False,
    )

    # Documentation
    with open(
        summary_file,
        "w",
        encoding="utf-8",
    ) as f:

        f.write("# Apriori Song Association Analysis\n\n")

        f.write("## Method\n")

        f.write(
            "Each user's listening history is treated as one transaction. "
            "The items are unique songs listened to by that user.\n\n"
        )

        f.write(f"- Activity records: {len(df)}\n")
        f.write(f"- Users found: {df['user_id'].nunique()}\n")
        f.write(f"- Songs selected: {df['song_id'].nunique()}\n")
        f.write(f"- Transactions used: {len(transactions)}\n")
        f.write(f"- Minimum support: {MIN_SUPPORT}\n")
        f.write(f"- Minimum confidence: {MIN_CONFIDENCE}\n\n")

        f.write(
            f"- Frequent itemsets found: "
            f"{len(itemsets_output)}\n"
        )

        f.write(
            f"- Association rules found: "
            f"{len(rules_output)}\n\n"
        )

        f.write("## Interpretation\n")

        f.write(
            "Frequent itemsets represent songs commonly listened to "
            "by the same users. Association rules describe directional "
            "relationships between song combinations using support, "
            "confidence, and lift.\n"
        )

    # Console output
    print("\n========== APRIORI COMPLETE ==========")
    print(f"Songs analyzed: {df['song_id'].nunique()}")
    print(f"Transactions: {len(transactions)}")
    print(f"Frequent itemsets: {len(itemsets_output)}")
    print(f"Association rules: {len(rules_output)}")

    print("\nTop frequent song itemsets:")

    if len(itemsets_output) > 0:
        print(
            itemsets_output[
                [
                    "songs",
                    "support",
                    "item_count",
                ]
            ]
            .head(10)
            .to_string(index=False)
        )
    else:
        print("No frequent itemsets found.")

    print("\nTop song association rules:")

    if len(rules_output) > 0:
        print(
            rules_output[
                [
                    "antecedent_songs",
                    "consequent_songs",
                    "support",
                    "confidence",
                    "lift",
                ]
            ]
            .head(10)
            .to_string(index=False)
        )
    else:
        print(
            "No association rules found "
            "with the current thresholds."
        )

    print("\nResults saved to:")
    print(RESULTS_DIR)

    print("=======================================")


if __name__ == "__main__":
    main()
