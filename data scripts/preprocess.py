"""Split by customer, then fit imputation, outlier treatment, scaling and encoding."""
import json
import joblib
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from source_io import ROOT
from feature_transformers import QuantileClipper

NUMERIC = ["avgGbpPrice", "avgDiscountValue"]
CATEGORICAL = ["productType", "brandDesc", "shippingCountry", "premier"]


def main():
    data = pd.read_csv(ROOT / "data/processed/development_sample.csv")
    split = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, validation_idx = next(split.split(data, groups=data.customer_id))
    train, validation = data.iloc[train_idx], data.iloc[validation_idx]
    numeric = Pipeline([("impute", SimpleImputer(strategy="median", keep_empty_features=True)),
                        ("clip", QuantileClipper()), ("scale", StandardScaler())])
    categorical = Pipeline([("impute", SimpleImputer(strategy="most_frequent", keep_empty_features=True)),
                            ("encode", OneHotEncoder(handle_unknown="ignore", sparse_output=True))])
    transformer = ColumnTransformer([("numeric", numeric, NUMERIC),
                                     ("categorical", categorical, CATEGORICAL)], sparse_threshold=1.0)
    X_train = sparse.csr_matrix(transformer.fit_transform(train[NUMERIC+CATEGORICAL]))
    X_valid = sparse.csr_matrix(transformer.transform(validation[NUMERIC+CATEGORICAL]))
    assert not set(train.customer_id) & set(validation.customer_id), "Customer leakage"
    assert np.isfinite(X_train.data).all() and np.isfinite(X_valid.data).all()
    out = ROOT / "data/processed"
    sparse.save_npz(out / "X_train.npz", X_train)
    sparse.save_npz(out / "X_validation.npz", X_valid)
    np.save(out / "y_train.npy", train.isReturned.to_numpy())
    np.save(out / "y_validation.npy", validation.isReturned.to_numpy())
    joblib.dump(transformer, out / "preprocessor.joblib")
    pd.DataFrame({"source_row":data.source_row,
                  "split":np.where(data.index.isin(train_idx),"train","validation")}).to_csv(out / "split_assignment.csv",index=False)
    clipper = transformer.named_transformers_["numeric"].named_steps["clip"]
    summary = {"train_rows":len(train),"validation_rows":len(validation),
               "train_customers":int(train.customer_id.nunique()),
               "validation_customers":int(validation.customer_id.nunique()),
               "customer_overlap":0,"transformed_features":X_train.shape[1],
               "train_return_rate":float(train.isReturned.mean()),
               "validation_return_rate":float(validation.isReturned.mean()),
               "numeric_features":NUMERIC,"categorical_features":CATEGORICAL,
               "lower_clip_bounds":dict(zip(NUMERIC,clipper.lower_bounds_.tolist())),
               "upper_clip_bounds":dict(zip(NUMERIC,clipper.upper_bounds_.tolist())),
               "feature_names":transformer.get_feature_names_out().tolist(),
               "scope":"Development preprocessing only. Aggregate price/discount timing is unverified. Not a chronological test or evidence of deployment-ready accuracy."}
    (ROOT / "reports/evidence/preprocessing_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))


if __name__ == "__main__":
    main()
