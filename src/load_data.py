"""Read and check the cleaned Phase 1 purchase sample."""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
EVIDENCE = ROOT / "reports" / "evidence"
FIGURES = ROOT / "reports" / "figures"
SAMPLE = PROCESSED / "development_sample.csv"
FEATURES = ["productType", "brandDesc"]
TARGET = "isReturned"
SEED = 42


def load_sample():
    if not SAMPLE.exists():
        raise FileNotFoundError("Run the Phase 1 download and cleaning commands first.")
    data = pd.read_csv(SAMPLE)
    needed = ["source_row", "customer_id", "shippingCountry", TARGET, *FEATURES]
    missing = set(needed) - set(data.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    if data.source_row.isna().any() or not data.source_row.is_unique:
        raise ValueError("Each purchase must have a unique source_row.")
    if data.customer_id.isna().any() or set(data[TARGET]) != {0, 1}:
        raise ValueError("Expected customer IDs and both binary return labels.")
    return data


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    data = load_sample()
    print(f"Ready: {len(data):,} purchases, {data[TARGET].mean():.2%} returned.")
    print("Model inputs:", ", ".join(FEATURES))

