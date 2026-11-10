"""Create separate train, validation, and test sets by customer."""
from hashlib import sha256

import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

from load_data import EVIDENCE, FEATURES, PROCESSED, SAMPLE, SEED, TARGET, load_sample, write_json

SPLIT_FILE = PROCESSED / "d2_split.csv"
SPLITS = ("train", "validation", "test")


def check_split(data):
    if set(data.split) != set(SPLITS):
        raise ValueError("Expected train, validation, and test assignments.")
    if data.groupby("customer_id").split.nunique().max() != 1:
        raise ValueError("A customer appears in more than one split.")
    for name, part in data.groupby("split"):
        if set(part[TARGET]) != {0, 1}:
            raise ValueError(f"{name} needs both return outcomes.")


def load_split():
    sample = load_sample()
    assignments = pd.read_csv(SPLIT_FILE)
    data = sample.merge(assignments, on="source_row", how="outer", validate="one_to_one", indicator=True)
    if not data["_merge"].eq("both").all():
        raise ValueError("Split assignments do not match the cleaned sample.")
    data = data.drop(columns="_merge")
    check_split(data)
    return data


def main():
    data = load_sample()
    first = GroupShuffleSplit(n_splits=1, test_size=0.30, random_state=SEED)
    train_idx, rest_idx = next(first.split(data, groups=data.customer_id))
    rest = data.iloc[rest_idx]
    second = GroupShuffleSplit(n_splits=1, test_size=0.50, random_state=SEED)
    valid_idx, test_idx = next(second.split(rest, groups=rest.customer_id))

    data.loc[data.index[train_idx], "split"] = "train"
    data.loc[rest.index[valid_idx], "split"] = "validation"
    data.loc[rest.index[test_idx], "split"] = "test"
    check_split(data)
    data[["source_row", "split"]].to_csv(SPLIT_FILE, index=False)
    counts = {}
    for name in SPLITS:
        part = data.loc[data.split == name]
        counts[name] = {
            "purchases": len(part),
            "customers": int(part.customer_id.nunique()),
            "returned": int(part[TARGET].sum()),
            "kept": int(part[TARGET].eq(0).sum()),
        }
        print(f"{name}: {len(part):,} purchases")
    write_json(EVIDENCE / "d2_data.json", {
        "seed": SEED,
        "sample_sha256": sha256(SAMPLE.read_bytes()).hexdigest(),
        "features": FEATURES,
        "customer_overlap": 0,
        "splits": counts,
    })
    print("Split saved. No customer appears in two sets.")


if __name__ == "__main__":
    main()

