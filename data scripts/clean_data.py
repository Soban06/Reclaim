"""Audit original tables and build a validated event-level development sample."""
import argparse
import json
import numpy as np
import pandas as pd
from source_io import ROOT, read_source


def audit_table(frame):
    return {"rows": len(frame), "columns": len(frame.columns),
            "missing_cells": int(frame.isna().sum().sum()),
            "exact_duplicate_rows": int(frame.duplicated().sum()),
            "duplicate_column_names": list(frame.columns[frame.columns.duplicated()])}


def clean_nodes(frame, key, columns):
    # Select only unambiguous fields. Return-reason columns have repeated names.
    selected = frame[columns].drop_duplicates().copy()
    if selected[key].duplicated().any():
        raise ValueError(f"Conflicting node records for {key}; investigate before joining")
    return selected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-size", type=int, default=100000)
    args = parser.parse_args()
    if args.sample_size < 100:
        parser.error("sample-size must be at least 100")
    events = read_source("event_table_training.p")
    customers = read_source("customer_nodes_training.p")
    products = read_source("product_nodes_training.p")
    audit = {"source_tables": {"events": audit_table(events),
                              "customers": audit_table(customers), "products": audit_table(products)}}
    audit["raw_return_counts"] = {str(k): int(v) for k,v in events.isReturned.value_counts().items()}
    customer_key, product_key = "hash(customerId)", "hash(variantID)"
    customers = clean_nodes(customers, customer_key,
                           [customer_key, "yearOfBirth", "isMale", "shippingCountry", "premier"])
    products = clean_nodes(products, product_key,
                          [product_key, "productType", "brandDesc", "avgGbpPrice", "avgDiscountValue"])
    # An identical event tuple can be a legitimate repeat purchase. There is no
    # unique order ID or timestamp, so preserve these rows and record the count.
    valid = events.isReturned.isin([0, 1]) & events[[customer_key, product_key]].notna().all(axis=1)
    audit["invalid_events_removed"] = int((~valid).sum())
    events = events.loc[valid].copy()
    events["source_row"] = events.index
    joined = events.merge(customers, on=customer_key, how="left", validate="many_to_one", indicator=True)
    audit["unmatched_customer_events"] = int((joined["_merge"] != "both").sum())
    joined["customer_matched"] = joined["_merge"] == "both"
    joined = joined.drop(columns="_merge").merge(products, on=product_key, how="left",
                                               validate="many_to_one", indicator=True)
    audit["unmatched_product_events"] = int((joined["_merge"] != "both").sum())
    complete = joined.customer_matched & (joined["_merge"] == "both")
    audit["events_excluded_missing_nodes"] = int((~complete).sum())
    audit["excluded_event_return_rate"] = float(joined.loc[~complete,"isReturned"].mean()) if (~complete).any() else None
    joined = joined.loc[complete].drop(columns=["_merge","customer_matched"]).rename(columns={customer_key:"customer_id",product_key:"variant_id"})
    if joined.empty:
        raise ValueError("No complete events remain after joining the source tables")
    audit["invalid_numeric_values_to_missing"] = {}
    for column in ["avgGbpPrice", "avgDiscountValue"]:
        joined[column] = pd.to_numeric(joined[column], errors="coerce")
        invalid = ~np.isfinite(joined[column]) | (joined[column] < 0)
        if column == "avgGbpPrice":
            invalid |= joined[column] == 0
        audit["invalid_numeric_values_to_missing"][column] = int(invalid.sum())
        joined.loc[invalid, column] = np.nan
    joined["age_2021"] = 2021 - joined["yearOfBirth"]
    invalid_age = ~joined.age_2021.between(0, 100)
    audit["invalid_age_events"] = int(invalid_age.sum())
    joined.loc[invalid_age, "age_2021"] = np.nan
    for column in ["shippingCountry", "productType", "brandDesc"]:
        joined[column] = joined[column].astype("string").str.strip().replace("", pd.NA)
    # Keep raw financial values in the cleaned table. Train-only percentile
    # clipping and imputation happen later, inside the fitted pipeline.
    sample = joined.sample(n=min(args.sample_size, len(joined)), random_state=42).sort_values("source_row")
    out = ROOT / "data" / "processed"
    out.mkdir(parents=True, exist_ok=True)
    sample.to_csv(out / "development_sample.csv", index=False)
    audit["joined_events"] = len(joined)
    audit["sample_rows"] = len(sample)
    audit["sample_seed"] = 42
    audit["sample_return_rate"] = float(sample.isReturned.mean())
    audit["sample_missing_by_column"] = sample.isna().sum().astype(int).to_dict()
    audit["event_duplicate_policy"] = "Preserved: repeated customer-variant-outcome tuples cannot be distinguished from legitimate repeat purchases. Node-table exact duplicates are removed before key validation."
    audit["excluded_predictors"] = ["customer and product IDs", "yearOfBirth / age_2021", "isMale",
        "sales/returns counts", "customerReturnRate", "productReturnRate", "all return-reason proportions"]
    report = ROOT / "reports" / "evidence"
    report.mkdir(parents=True, exist_ok=True)
    (report / "data_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
