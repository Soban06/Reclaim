"""Compare the saved model and baselines on held-out purchases."""
import json

import joblib
import numpy as np
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             precision_score, recall_score, roc_auc_score)

from baselines import BASELINES_FILE, product_scores
from load_data import EVIDENCE, TARGET, write_json
from make_split import load_split
from train_models import MODEL_FILE


def measure(y, scores, predictions):
    tn, fp, fn, tp = map(int, confusion_matrix(y, predictions, labels=[0, 1]).ravel())
    return {
        "accuracy": float(accuracy_score(y, predictions)),
        "precision": float(precision_score(y, predictions, zero_division=0)),
        "recall": float(recall_score(y, predictions, zero_division=0)),
        "f1": float(f1_score(y, predictions, zero_division=0)),
        "roc_auc": float(roc_auc_score(y, scores)),
        "tn": tn, "fp": fp, "fn": fn, "tp": tp,
    }


def score_test():
    data = load_split()
    test = data.loc[data.split == "test"].copy()
    model = joblib.load(MODEL_FILE)
    baseline = json.loads(BASELINES_FILE.read_text(encoding="utf-8"))
    scores = model["pipeline"].predict_proba(test[model["features"]])[:, 1]
    test["predicted_return"] = scores >= model["threshold"]
    rule_scores = product_scores(test, baseline)
    y = test[TARGET]
    results = {
        "test_purchases": len(test),
        "model_threshold": model["threshold"],
        "majority": measure(y, np.full(len(test), baseline["prevalence"]),
                            np.full(len(test), baseline["majority_label"])),
        "product_type_rule": measure(y, rule_scores, rule_scores >= baseline["rule_threshold"]),
        "selected_model": measure(y, scores, test.predicted_return),
    }
    return test, results


def main():
    _, results = score_test()
    write_json(EVIDENCE / "d2_test.json", results)
    print(f"Saved results for {results['test_purchases']:,} held-out purchases.")


if __name__ == "__main__":
    main()

