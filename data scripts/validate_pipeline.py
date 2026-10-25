"""Verify leakage boundaries and preprocessing behavior on awkward inputs."""
import json
import joblib
import numpy as np
import pandas as pd
from scipy import sparse
from source_io import ROOT
from preprocess import NUMERIC, CATEGORICAL


def main():
    folder = ROOT / "data/processed"
    data = pd.read_csv(folder / "development_sample.csv")
    assignments = pd.read_csv(folder / "split_assignment.csv")
    merged = data.merge(assignments, on="source_row", validate="one_to_one")
    training = merged[merged.split == "train"]
    validation = merged[merged.split == "validation"]
    assert len(training) + len(validation) == len(data)
    assert set(training.customer_id).isdisjoint(validation.customer_id)
    transformer = joblib.load(folder / "preprocessor.joblib")
    selected = [c for _,_,columns in transformer.transformers_ if isinstance(columns,list) for c in columns]
    assert selected == NUMERIC + CATEGORICAL
    assert "isReturned" not in selected and "customerReturnRate" not in selected
    numeric = transformer.named_transformers_["numeric"]
    bounds = numeric.named_steps["clip"].upper_bounds_.copy()
    scale = numeric.named_steps["scale"].mean_.copy()
    probe = data[NUMERIC+CATEGORICAL].head(3).copy()
    probe.loc[probe.index[0], NUMERIC] = np.nan
    probe.loc[probe.index[1], "productType"] = "never_seen_before"
    probe.loc[probe.index[2], "avgGbpPrice"] = 1e12
    transformed = sparse.csr_matrix(transformer.transform(probe))
    assert np.isfinite(transformed.data).all()
    np.testing.assert_array_equal(bounds, numeric.named_steps["clip"].upper_bounds_)
    np.testing.assert_array_equal(scale, numeric.named_steps["scale"].mean_)
    X_train = sparse.load_npz(folder / "X_train.npz")
    X_valid = sparse.load_npz(folder / "X_validation.npz")
    assert X_train.shape[0] == len(training) and X_valid.shape[0] == len(validation)
    assert X_train.shape[1] == X_valid.shape[1] == transformed.shape[1]
    np.testing.assert_array_equal(np.load(folder / "y_train.npy"), training.isReturned.to_numpy())
    np.testing.assert_array_equal(np.load(folder / "y_validation.npy"), validation.isReturned.to_numpy())
    result = {"status":"passed", "checks":["customer isolation", "target excluded from features",
        "missing-value transformation", "unknown-category transformation", "extreme-value transformation",
        "no transform-time refitting", "matrix dimensions", "label alignment"],
        "train_shape":list(X_train.shape), "validation_shape":list(X_valid.shape)}
    (ROOT / "reports/evidence/validation_results.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))


if __name__ == "__main__":
    main()
