"""Make two simple comparisons from the training purchases."""
from load_data import PROCESSED, TARGET, write_json
from make_split import load_split

BASELINES_FILE = PROCESSED / "d2_baselines.json"


def make_baselines(train):
    prevalence = float(train[TARGET].mean())
    rates = train.groupby("productType")[TARGET].mean()
    return {
        "prevalence": prevalence,
        "majority_label": int(prevalence >= 0.5),
        "product_rates": {str(name): float(rate) for name, rate in rates.items()},
        "rule_threshold": 0.5,
    }


def product_scores(data, baseline):
    return data.productType.map(baseline["product_rates"]).fillna(baseline["prevalence"])


def main():
    data = load_split()
    baseline = make_baselines(data.loc[data.split == "train"])
    write_json(BASELINES_FILE, baseline)
    print(f"Baselines ready. Training return rate: {baseline['prevalence']:.2%}.")


if __name__ == "__main__":
    main()

