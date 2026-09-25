from pathlib import Path

import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules


# Project root folder
BASE_DIR = Path(__file__).resolve().parents[2]

# Input and output locations
ACTIVITY_FILE = BASE_DIR / "data" / "processed" / "synthetic_activity.csv"
RESULTS_DIR = BASE_DIR / "dwm" / "mining" / "results"

# Apriori settings
MIN_SUPPORT = 0.10
MIN_CONFIDENCE = 0.50


def main():
    print("Reading listening activity...")

    df = pd.read_csv(ACTIVITY_FILE)

    print(f"Activity records loaded: {len(df)}")
    print(f"Users found: {df['user_id'].nunique()}")

    # Remove rows without a genre
    df = df.dropna(subset=["user_id", "genre"]).copy()

    # Make genre names consistent
    df["genre"] = df["genre"].astype(str).str.strip()

    # Create one transaction per user:
    # all unique genres listened to by that user
    transactions = (
        df.groupby("user_id")["genre"]
        .apply(lambda genres: sorted(set(genres)))
        .tolist()
    )

    # Apriori needs transactions containing at least 2 items
    transactions = [items for items in transactions if len(items) >= 2]

    print(f"Transactions used: {len(transactions)}")

    # Convert transactions into True/False table
    encoder = TransactionEncoder()
    encoded_data = encoder.fit(transactions).transform(transactions)

    basket = pd.DataFrame(
        encoded_data,
        columns=encoder.columns_
    )

    print(f"Genres found: {len(basket.columns)}")

    # Find frequent genre combinations
    frequent_itemsets = apriori(
        basket,
        min_support=MIN_SUPPORT,
        use_colnames=True
    )

    # Add number of genres in each itemset
    frequent_itemsets["item_count"] = frequent_itemsets["itemsets"].apply(len)

    # Generate association rules
    rules = association_rules(
        frequent_itemsets,
        metric="confidence",
        min_threshold=MIN_CONFIDENCE
    )

    # Sort results
    frequent_itemsets = frequent_itemsets.sort_values(
        ["item_count", "support"],
        ascending=[True, False]
    )

    rules = rules.sort_values(
        ["lift", "confidence"],
        ascending=[False, False]
    )

    # Make itemsets readable before saving
    itemsets_output = frequent_itemsets.copy()
    itemsets_output["itemsets"] = itemsets_output["itemsets"].apply(
        lambda items: ", ".join(sorted(items))
    )

    rules_output = rules.copy()
    rules_output["antecedents"] = rules_output["antecedents"].apply(
        lambda items: ", ".join(sorted(items))
    )
    rules_output["consequents"] = rules_output["consequents"].apply(
        lambda items: ", ".join(sorted(items))
    )

    # Create results folder if needed
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Save results
    itemsets_file = RESULTS_DIR / "apriori_frequent_itemsets.csv"
    rules_file = RESULTS_DIR / "apriori_rules.csv"
    summary_file = RESULTS_DIR / "apriori_summary.md"

    itemsets_output.to_csv(itemsets_file, index=False)
    rules_output.to_csv(rules_file, index=False)

    # Create short documentation
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write("# Apriori Analysis\n\n")
        f.write("## Method\n")
        f.write(
            "Each user's listening history is treated as one transaction. "
            "The items are the unique genres listened to by that user.\n\n"
        )
        f.write(f"- Activity records: {len(df)}\n")
        f.write(f"- Users: {df['user_id'].nunique()}\n")
        f.write(f"- Transactions used: {len(transactions)}\n")
        f.write(f"- Minimum support: {MIN_SUPPORT}\n")
        f.write(f"- Minimum confidence: {MIN_CONFIDENCE}\n\n")

        f.write(f"- Frequent itemsets found: {len(itemsets_output)}\n")
        f.write(f"- Association rules found: {len(rules_output)}\n\n")

        f.write("## Interpretation\n")
        f.write(
            "Frequent itemsets show genres that commonly occur together "
            "in users' listening activity. Association rules show directional "
            "relationships between genre combinations using confidence and lift.\n"
        )

    print("\n========== APRIORI COMPLETE ==========")
    print(f"Frequent itemsets: {len(itemsets_output)}")
    print(f"Association rules: {len(rules_output)}")

    print("\nTop frequent itemsets:")
    print(
        itemsets_output[
            ["itemsets", "support", "item_count"]
        ].head(10).to_string(index=False)
    )

    print("\nTop association rules:")
    if len(rules_output) > 0:
        print(
            rules_output[
                [
                    "antecedents",
                    "consequents",
                    "support",
                    "confidence",
                    "lift",
                ]
            ].head(10).to_string(index=False)
        )
    else:
        print("No association rules found with the current thresholds.")

    print("\nResults saved to:")
    print(RESULTS_DIR)
    print("======================================")


if __name__ == "__main__":
    main()
