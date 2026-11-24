"""Train the final model with order-time inputs and choose a balanced cutoff."""
import joblib
import matplotlib
import numpy as np
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, log_loss, roc_auc_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from load_data import EVIDENCE, FIGURES, ROOT, SEED, TARGET, write_json
from make_split import load_split

matplotlib.use("Agg")
from matplotlib import pyplot as plt

MODEL_FILE = ROOT / "models" / "final_model.joblib"
# Every input is known when the order is placed. Price and discount stay out
# because the source only gives product averages of uncertain timing.
CATEGORICAL = ["productType", "brandDesc", "shippingCountry"]
NUMERIC = ["age_2021", "isMale", "premier"]
FEATURES = CATEGORICAL + NUMERIC
# The Deliverable 2 inputs, kept as a comparison.
D2_FEATURES = ["productType", "brandDesc"]
AGE_RANGE = (16, 90)


def preprocessor(features):
    steps = [("categories", make_pipeline(
        SimpleImputer(strategy="most_frequent"),
        OneHotEncoder(handle_unknown="ignore", sparse_output=False),
    ), [f for f in features if f in CATEGORICAL])]
    numeric = [f for f in features if f in NUMERIC]
    if numeric:
        steps.append(("numbers", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), numeric))
    return ColumnTransformer(steps)


def pipeline(kind, settings, features):
    if kind == "logistic":
        estimator = LogisticRegression(solver="lbfgs", max_iter=2000, **settings)
    else:
        estimator = HistGradientBoostingClassifier(early_stopping=False, random_state=SEED, **settings)
    return make_pipeline(preprocessor(features), estimator)


def clean_ages(data):
    # Ages outside a plausible shopper range are treated as unknown.
    data = data.copy()
    data.loc[~data.age_2021.between(*AGE_RANGE), "age_2021"] = np.nan
    return data


def choose_cutoff(y, scores):
    # Balanced accuracy weighs returns and kept purchases equally, so flagging
    # every purchase cannot win the way it did with F1 in Deliverable 2.
    cutoffs = np.round(np.arange(0.30, 0.701, 0.01), 2)
    values = [balanced_accuracy_score(y, scores >= c) for c in cutoffs]
    best = int(np.argmax(values))
    return float(cutoffs[best]), float(values[best])


def training_history(settings, train, validation):
    model = pipeline("boosting", settings, FEATURES).fit(train[FEATURES], train[TARGET])
    history = {"Training": [], "Validation": []}
    for label, part in (("Training", train), ("Validation", validation)):
        for scores in model.steps[-1][1].staged_predict_proba(model.steps[0][1].transform(part[FEATURES])):
            history[label].append(log_loss(part[TARGET], scores[:, 1]))
    fig, ax = plt.subplots(figsize=(5.2, 3.3), layout="constrained")
    for label, values in history.items():
        ax.plot(range(1, len(values) + 1), values, label=label)
    ax.set(xlabel="Boosting iteration", ylabel="Log loss", title="Training history")
    ax.legend()
    fig.savefig(FIGURES / "final_training_history.png", dpi=160)
    plt.close(fig)


def learning_curves(kind, settings, train, validation):
    counts, auc = [], {"Training": [], "Validation": []}
    for fraction in (0.25, 0.50, 0.75, 1.0):
        subset = train
        if fraction < 1:
            splitter = GroupShuffleSplit(n_splits=1, train_size=fraction, random_state=SEED)
            indices, _ = next(splitter.split(train, groups=train.customer_id))
            subset = train.iloc[indices]
        model = pipeline(kind, settings, FEATURES).fit(subset[FEATURES], subset[TARGET])
        counts.append(len(subset))
        for label, part in (("Training", subset), ("Validation", validation)):
            auc[label].append(roc_auc_score(part[TARGET], model.predict_proba(part[FEATURES])[:, 1]))
    fig, ax = plt.subplots(figsize=(5.2, 3.3), layout="constrained")
    for label, values in auc.items():
        ax.plot(counts, values, marker="o", label=label)
    ax.set(xlabel="Training purchases", ylabel="ROC-AUC", title="Learning curve")
    ax.legend()
    fig.savefig(FIGURES / "final_learning_curve.png", dpi=160)
    plt.close(fig)


def main():
    data = clean_ages(load_split())
    train = data.loc[data.split == "train"]
    validation = data.loc[data.split == "validation"]

    candidates = [("logistic", {"C": c}) for c in (0.1, 1.0, 10.0)]
    candidates += [("boosting", {"max_depth": depth, "learning_rate": rate, "max_iter": 300})
                   for depth in (3, 5) for rate in (0.03, 0.1)]
    results = []
    for features, label in ((D2_FEATURES, "deliverable_2_inputs"), (FEATURES, "order_time_inputs")):
        for kind, settings in candidates:
            model = pipeline(kind, settings, features).fit(train[features], train[TARGET])
            scores = model.predict_proba(validation[features])[:, 1]
            results.append({"inputs": label, "kind": kind, "settings": settings,
                            "roc_auc": float(roc_auc_score(validation[TARGET], scores))})
            print(f"{label:22s} {kind:9s} {settings} ROC-AUC {results[-1]['roc_auc']:.4f}")

    # Only order-time candidates can win. max keeps the first entry on a tie,
    # so the simpler logistic models win ties.
    winner = max((r for r in results if r["inputs"] == "order_time_inputs"), key=lambda r: r["roc_auc"])
    kind, settings = winner["kind"], winner["settings"]
    model = pipeline(kind, settings, FEATURES).fit(train[FEATURES], train[TARGET])
    scores = model.predict_proba(validation[FEATURES])[:, 1]
    cutoff, balanced = choose_cutoff(validation[TARGET], scores)

    MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({
        "pipeline": model,
        "features": FEATURES,
        "categorical": CATEGORICAL,
        "numeric": NUMERIC,
        "threshold": cutoff,
        "options": {c: sorted(train[c].dropna().astype(str).unique()) for c in CATEGORICAL},
        "reference": {**{c: train[c].mode()[0] for c in CATEGORICAL},
                      **{c: float(train[c].median()) for c in NUMERIC}},
        "age_range": AGE_RANGE,
        "training_return_rate": float(train[TARGET].mean()),
        "product_return_rates": {str(k): float(v) for k, v in train.groupby("productType")[TARGET].mean().items()},
        "sklearn_version": sklearn.__version__,
    }, MODEL_FILE, compress=3)
    write_json(EVIDENCE / "final_validation.json", {
        "features": FEATURES,
        "candidates": results,
        "winner": winner,
        "threshold": cutoff,
        "threshold_rule": "maximum validation balanced accuracy, cutoffs 0.30 to 0.70",
        "validation_balanced_accuracy": balanced,
    })
    FIGURES.mkdir(parents=True, exist_ok=True)
    best_boosting = max((r for r in results if r["inputs"] == "order_time_inputs" and r["kind"] == "boosting"),
                        key=lambda r: r["roc_auc"])
    training_history(best_boosting["settings"], train, validation)
    learning_curves(kind, settings, train, validation)
    print(f"Saved {kind} model to {MODEL_FILE.relative_to(ROOT)}. "
          f"Validation ROC-AUC {winner['roc_auc']:.3f}, cutoff {cutoff:.2f}.")


if __name__ == "__main__":
    main()
