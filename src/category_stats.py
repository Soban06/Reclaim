"""Save each category's training return rate and share for the app's dropdowns.

The dataset anonymises most product types, brands and countries, so the app
shows these figures next to each code to make the options meaningful.
"""
from load_data import ROOT, TARGET, write_json
from make_split import load_split

STATS_FILE = ROOT / "app" / "category_stats.json"
COLUMNS = ["productType", "brandDesc", "shippingCountry"]


def main():
    data = load_split()
    train = data.loc[data.split == "train"]
    stats = {}
    for column in COLUMNS:
        groups = train.groupby(column)[TARGET].agg(["mean", "size"])
        stats[column] = {str(name): {"return_rate": round(float(row["mean"]), 4),
                                     "share": round(float(row["size"]) / len(train), 4),
                                     "purchases": int(row["size"])}
                         for name, row in groups.iterrows()}
    write_json(STATS_FILE, {"source": "training purchases", "purchases": len(train), **stats})
    print(f"Saved category statistics from {len(train):,} training purchases.")


if __name__ == "__main__":
    main()
