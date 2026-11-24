"""Check the prediction backend used by the Streamlit app."""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from predict import check_inputs, explain, load_model, predict, risk_band  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def model():
    return load_model()


@pytest.fixture
def purchase():
    return {"productType": "productType_B", "brandDesc": "Brand_C", "shippingCountry": "Country_G",
            "age_2021": 30, "isMale": 0, "premier": 1}


def test_model_file_has_what_the_app_needs(model):
    assert 0.3 <= model["threshold"] <= 0.7
    assert set(model["categorical"]) <= set(model["options"])
    assert all(model["options"][c] for c in model["categorical"])


def test_single_purchase_gets_a_probability_and_decision(model, purchase):
    result, warnings = predict(pd.DataFrame([purchase]), model)
    row = result.iloc[0]
    assert warnings == []
    assert 0 <= row.return_probability <= 1
    assert row.prediction == ("Likely return" if row.return_probability >= model["threshold"] else "Likely keep")


def test_sample_upload_file_scores_without_warnings(model):
    sample = pd.read_csv(ROOT / "app" / "sample_purchases.csv")
    result, warnings = predict(sample, model)
    assert len(result) == len(sample)
    assert result.return_probability.between(0, 1).all()
    assert warnings == []


def test_missing_column_is_reported(model, purchase):
    del purchase["brandDesc"]
    with pytest.raises(ValueError, match="brandDesc"):
        predict(pd.DataFrame([purchase]), model)


def test_empty_file_is_rejected(model):
    with pytest.raises(ValueError, match="no purchases"):
        predict(pd.DataFrame(columns=model["features"]), model)


def test_bad_values_become_warnings_not_errors(model, purchase):
    rows = pd.DataFrame([purchase, {**purchase, "brandDesc": "Brand_Unknown", "age_2021": 5, "isMale": "yes"}])
    result, warnings = predict(rows, model)
    assert len(result) == 2
    assert any("unseen brand" in w for w in warnings)
    assert any("invalid age" in w for w in warnings)
    assert any("invalid gender flag" in w for w in warnings)
    clean, _ = check_inputs(rows, model)
    assert pd.isna(clean.loc[1, "age_2021"])


def test_explanation_covers_every_input(model, purchase):
    effects = explain(purchase, model)
    assert len(effects) == len(model["features"])
    assert effects.effect.abs().is_monotonic_decreasing


def test_risk_bands_follow_the_cutoff():
    assert risk_band(0.70, 0.55) == "High"
    assert risk_band(0.60, 0.55) == "Elevated"
    assert risk_band(0.50, 0.55) == "Moderate"
    assert risk_band(0.30, 0.55) == "Low"
