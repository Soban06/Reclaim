"""Measure the final model on held-out purchases and save report material."""
import json

import joblib
import matplotlib
import numpy as np
from sklearn.metrics import ConfusionMatrixDisplay, RocCurveDisplay

from baselines import BASELINES_FILE, product_scores
from check_errors import group_results
from evaluate_model import measure
from load_data import EVIDENCE, FIGURES, ROOT, TARGET, write_json
from make_split import load_split
from predict import load_model, predict
from train_final import clean_ages

matplotlib.use("Agg")
from matplotlib import pyplot as plt

D2_MODEL = ROOT / "models" / "d2_model.joblib"
SAMPLE_FILE = ROOT / "app" / "sample_purchases.csv"


def main():
    data = clean_ages(load_split())
    test = data.loc[data.split == "test"].copy()
    y = test[TARGET]
    model = load_model()
    d2 = joblib.load(D2_MODEL)
    baseline = json.loads(BASELINES_FILE.read_text(encoding="utf-8"))

    scored, _ = predict(test, model)
    test["predicted_return"] = scored.prediction.eq("Likely return")
    final_scores = scored.return_probability.to_numpy()
    d2_scores = d2["pipeline"].predict_proba(test[d2["features"]])[:, 1]
    rule_scores = product_scores(test, baseline)
    results = {
        "test_purchases": len(test),
        "final_threshold": model["threshold"],
        "majority": measure(y, np.full(len(test), baseline["prevalence"]),
                            np.full(len(test), baseline["majority_label"])),
        "product_type_rule": measure(y, rule_scores, rule_scores >= baseline["rule_threshold"]),
        "deliverable_2_model": measure(y, d2_scores, d2_scores >= d2["threshold"]),
        "final_model": measure(y, final_scores, test.predicted_return),
    }
    write_json(EVIDENCE / "final_test.json", results)
    write_json(EVIDENCE / "final_errors.json", {
        "shipping_country": group_results(test, "shippingCountry"),
        "product_type": group_results(test, "productType"),
    })

    FIGURES.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(4.6, 4.2), layout="constrained")
    for name, scores in (("Final model", final_scores), ("Deliverable 2 model", d2_scores),
                         ("Product-type rule", rule_scores)):
        RocCurveDisplay.from_predictions(y, scores, name=name, ax=ax)
    ax.plot([0, 1], [0, 1], linestyle="--", color="grey", linewidth=1)
    ax.set_title("Held-out ROC curves")
    fig.savefig(FIGURES / "final_roc_curve.png", dpi=160)
    plt.close(fig)

    final = results["final_model"]
    display = ConfusionMatrixDisplay(np.array([[final["tn"], final["fp"]], [final["fn"], final["tp"]]]),
                                     display_labels=["Kept", "Returned"])
    display.plot(cmap="Blues", colorbar=False, values_format="d")
    display.ax_.set_title(f"Final model at cutoff {model['threshold']:.2f}")
    display.figure_.savefig(FIGURES / "final_confusion_matrix.png", dpi=160, bbox_inches="tight")
    plt.close(display.figure_)

    # Six held-out examples for the report: the three highest and three lowest scores.
    ranked = (scored.assign(actual=y.map({1: "Returned", 0: "Kept"}))
              .dropna(subset=model["features"]).drop_duplicates(model["features"])
              .sort_values("return_probability"))
    examples = ranked.iloc[np.r_[-3:0, 0:3]]
    write_json(EVIDENCE / "final_sample_predictions.json", examples[
        model["features"] + ["return_probability", "prediction", "actual"]].to_dict(orient="records"))

    # A small upload file for the app demo, taken from held-out purchases.
    SAMPLE_FILE.parent.mkdir(parents=True, exist_ok=True)
    sample = test.sample(25, random_state=7)[model["features"]]
    sample = sample.astype({c: "Int64" for c in model["numeric"]})
    sample.to_csv(SAMPLE_FILE, index=False)

    print(f"Final model on {len(test):,} held-out purchases: "
          f"ROC-AUC {final['roc_auc']:.3f}, accuracy {final['accuracy']:.3f}, "
          f"recall {final['recall']:.3f}, flagged {final['tp'] + final['fp']:,}.")


if __name__ == "__main__":
    main()
