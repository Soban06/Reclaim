"""Summarize held-out errors by group and draw the confusion matrix."""
import matplotlib
import numpy as np
from sklearn.metrics import ConfusionMatrixDisplay, confusion_matrix

from evaluate_model import score_test
from load_data import EVIDENCE, FIGURES, TARGET, write_json

matplotlib.use("Agg")
from matplotlib import pyplot as plt


def group_results(test, column):
    groups = test[column].fillna("(missing)")
    summary = []
    for name, part in test.groupby(groups, sort=True):
        tn, fp, fn, tp = map(int, confusion_matrix(
            part[TARGET], part.predicted_return, labels=[0, 1]).ravel())
        positives, negatives = tp + fn, tn + fp
        summary.append({
            "group": str(name),
            "purchases": len(part),
            "returns": positives,
            "kept": negatives,
            "false_positives": fp,
            "false_negatives": fn,
            "recall": tp / positives if positives else None,
            "false_positive_rate": fp / negatives if negatives else None,
            "small_group": min(positives, negatives) < 20,
        })
    return summary


def main():
    test, results = score_test()
    write_json(EVIDENCE / "d2_errors.json", {
        "shipping_country": group_results(test, "shippingCountry"),
        "product_type": group_results(test, "productType"),
    })
    model = results["selected_model"]
    display = ConfusionMatrixDisplay(
        np.array([[model["tn"], model["fp"]], [model["fn"], model["tp"]]]),
        display_labels=["Kept", "Returned"],
    )
    display.plot(cmap="Blues", colorbar=False, values_format="d")
    display.ax_.set_title("Held-out purchases")
    FIGURES.mkdir(parents=True, exist_ok=True)
    display.figure_.savefig(FIGURES / "d2_confusion_matrix.png", dpi=160, bbox_inches="tight")
    plt.close(display.figure_)
    print("Saved the group checks and confusion matrix.")


if __name__ == "__main__":
    main()

