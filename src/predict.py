"""Load the final model, check purchase inputs, and score them."""
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

MODEL_FILE = Path(__file__).resolve().parents[1] / "models" / "final_model.joblib"
LABELS = {
    "productType": "Product type",
    "brandDesc": "Brand",
    "shippingCountry": "Shipping country",
    "age_2021": "Customer age",
    "isMale": "Customer is male",
    "premier": "Premier member",
}
# Lower-case names used inside warning messages.
NOUNS = {
    "productType": "product type",
    "brandDesc": "brand",
    "shippingCountry": "shipping country",
    "age_2021": "age",
    "isMale": "gender flag",
    "premier": "premier flag",
}


def load_model(path=MODEL_FILE):
    model = joblib.load(path)
    for key in ("pipeline", "features", "threshold", "options", "reference"):
        if key not in model:
            raise ValueError(f"The model file is missing '{key}'.")
    return model


def check_inputs(data, model):
    """Return a cleaned copy of the inputs and a list of warnings."""
    missing = [c for c in model["features"] if c not in data.columns]
    if missing:
        names = ", ".join(missing)
        raise ValueError(f"Missing columns: {names}. Required columns: {', '.join(model['features'])}.")
    if data.empty:
        raise ValueError("The file has no purchases to score.")
    clean = data[model["features"]].copy()
    warnings = []
    for column in model["categorical"]:
        clean[column] = clean[column].astype("string").str.strip()
        unknown = clean[column].notna() & ~clean[column].isin(model["options"][column])
        if unknown.any():
            values = ", ".join(sorted(clean.loc[unknown, column].unique())[:5])
            warnings.append(f"{unknown.sum()} rows have an unseen {NOUNS[column]} ({values}). "
                            "The model ignores that value.")
        if clean[column].isna().any():
            warnings.append(f"{clean[column].isna().sum()} rows have no {NOUNS[column]}. "
                            "The most common value is used.")
    for column in model["numeric"]:
        values = pd.to_numeric(clean[column], errors="coerce")
        bad = values.isna() & clean[column].notna()
        if column == "age_2021":
            low, high = model["age_range"]
            bad |= values.notna() & ~values.between(low, high)
        elif column in ("isMale", "premier"):
            bad |= values.notna() & ~values.isin([0, 1])
        if bad.any():
            warnings.append(f"{bad.sum()} rows have an invalid {NOUNS[column]}. "
                            "It is treated as unknown.")
        clean[column] = values.mask(bad)
    return clean, warnings


def risk_band(probability, threshold):
    if probability >= threshold + 0.10:
        return "High"
    if probability >= threshold:
        return "Elevated"
    if probability >= threshold - 0.10:
        return "Moderate"
    return "Low"


def predict(data, model):
    """Score purchases and return them with the probability and decision."""
    clean, warnings = check_inputs(data, model)
    probability = model["pipeline"].predict_proba(clean)[:, 1]
    result = data.copy()
    result["return_probability"] = np.round(probability, 4)
    result["prediction"] = np.where(probability >= model["threshold"], "Likely return", "Likely keep")
    result["risk_band"] = [risk_band(p, model["threshold"]) for p in probability]
    return result, warnings


def explain(row, model):
    """Show how much each input moves the score away from a typical purchase.

    Each input is swapped for the most common (or median) training value in
    turn. The change in probability is that input's effect on this purchase.
    """
    clean, _ = check_inputs(pd.DataFrame([row]), model)
    base = model["pipeline"].predict_proba(clean)[0, 1]
    swaps = pd.concat([clean] * len(model["features"]), ignore_index=True)
    for index, column in enumerate(model["features"]):
        swaps.loc[index, column] = model["reference"][column]
    typical = model["pipeline"].predict_proba(swaps)[:, 1]
    effects = pd.DataFrame({
        "input": [LABELS[c] for c in model["features"]],
        "value": [row.get(c) for c in model["features"]],
        "effect": np.round(base - typical, 4),
    })
    return effects.reindex(effects.effect.abs().sort_values(ascending=False).index).reset_index(drop=True)
