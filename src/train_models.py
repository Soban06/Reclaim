"""Choose a model and cutoff using validation purchases only."""
import joblib
import matplotlib
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, log_loss, roc_auc_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeClassifier

from load_data import EVIDENCE, FEATURES, FIGURES, PROCESSED, SEED, TARGET, write_json
from make_split import load_split

matplotlib.use("Agg")
from matplotlib import pyplot as plt

MODEL_FILE = PROCESSED / "d2_model.joblib"


def pipeline(kind, settings):
    if kind == "logistic":
        estimator = LogisticRegression(solver="lbfgs", max_iter=1000, **settings)
    else:
        estimator = DecisionTreeClassifier(criterion="gini", random_state=SEED, **settings)
    return make_pipeline(
        SimpleImputer(strategy="most_frequent"),
        OneHotEncoder(handle_unknown="ignore"),
        estimator,
    )


def learning_curves(kind, settings, train, validation):
    counts = []
    values = {"Training": [], "Validation": []}
    for fraction in (0.25, 0.50, 0.75, 1.0):
        subset = train
        if fraction < 1:
            splitter = GroupShuffleSplit(n_splits=1, train_size=fraction, random_state=SEED)
            indices, _ = next(splitter.split(train, groups=train.customer_id))
            subset = train.iloc[indices]
        model = pipeline(kind, settings).fit(subset[FEATURES], subset[TARGET])
        counts.append(len(subset))
        for label, part in (("Training", subset), ("Validation", validation)):
            scores = model.predict_proba(part[FEATURES])[:, 1]
            values[label].append((log_loss(part[TARGET], scores), accuracy_score(part[TARGET], scores >= 0.5)))
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.3), layout="constrained")
    for index, title in enumerate(("Log loss", "Accuracy at cutoff 0.5")):
        for label, points in values.items():
            axes[index].plot(counts, [point[index] for point in points], marker="o", label=label)
        axes[index].set(xlabel="Training purchases", ylabel=title)
        axes[index].legend()
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES / "d2_learning_curves.png", dpi=160)
    plt.close(fig)


def main():
    data = load_split()
    train = data.loc[data.split == "train"]
    validation = data.loc[data.split == "validation"]
    candidates = [("logistic", {"C": c}) for c in (0.1, 1.0, 10.0)]
    candidates += [("tree", {"max_depth": depth, "min_samples_leaf": leaf})
                   for depth in (3, 6) for leaf in (200, 50)]
    results = []
    for kind, settings in candidates:
        model = pipeline(kind, settings).fit(train[FEATURES], train[TARGET])
        scores = model.predict_proba(validation[FEATURES])[:, 1]
        results.append({"kind": kind, "settings": settings,
                        "roc_auc": float(roc_auc_score(validation[TARGET], scores))})

    # max keeps the first entry on a tie, with simpler candidates listed first.
    winner = max(results, key=lambda row: row["roc_auc"])
    kind, settings = winner["kind"], winner["settings"]
    model = pipeline(kind, settings).fit(train[FEATURES], train[TARGET])
    scores = model.predict_proba(validation[FEATURES])[:, 1]
    cutoffs = sorted((float(v) for v in np.linspace(0.1, 0.9, 81)), key=lambda v: (abs(v - 0.5), v))
    cutoff = max(cutoffs, key=lambda v: f1_score(validation[TARGET], scores >= v, zero_division=0))
    joblib.dump({"pipeline": model, "features": FEATURES, "threshold": cutoff}, MODEL_FILE)
    write_json(EVIDENCE / "d2_validation.json", {
        "candidates": results,
        "winner": winner,
        "threshold": cutoff,
        "validation_f1_at_threshold": float(f1_score(validation[TARGET], scores >= cutoff)),
    })
    learning_curves(kind, settings, train, validation)
    print(f"Saved {kind} model. Validation ROC-AUC: {winner['roc_auc']:.3f}. Cutoff: {cutoff:.2f}.")


if __name__ == "__main__":
    main()

