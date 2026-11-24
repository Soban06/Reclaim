"""Reclaim: score the return risk of fashion purchases with the final model."""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from predict import LABELS, explain, load_model, predict  # noqa: E402

SAMPLE_FILE = ROOT / "app" / "sample_purchases.csv"
BAND_COLOURS = {"High": "#B42318", "Elevated": "#C4320A", "Moderate": "#B54708", "Low": "#067647"}

st.set_page_config(page_title="Reclaim", page_icon=":package:", layout="wide")


@st.cache_resource
def get_model():
    return load_model()


def show_result(row, model):
    probability = row.return_probability
    colour = BAND_COLOURS[row.risk_band]
    left, middle, right = st.columns(3)
    left.metric("Return probability", f"{probability:.0%}")
    middle.markdown(f"**Decision**<br><span style='font-size:1.6rem;color:{colour}'>{row.prediction}</span>",
                    unsafe_allow_html=True)
    right.markdown(f"**Risk band**<br><span style='font-size:1.6rem;color:{colour}'>{row.risk_band}</span>",
                   unsafe_allow_html=True)
    st.progress(float(probability))
    product_rate = model["product_return_rates"].get(row.productType, model["training_return_rate"])
    st.caption(f"The model flags a purchase at {model['threshold']:.0%} or above. "
               f"In the training data, {product_rate:.0%} of {row.productType} purchases were returned, "
               f"and {model['training_return_rate']:.0%} of all purchases were returned.")


def single_purchase(model):
    st.subheader("Score one purchase")
    st.caption("The score updates as soon as you change a detail.")
    first, second = st.columns(2)
    options = model["options"]
    reference = model["reference"]
    product = first.selectbox(LABELS["productType"], options["productType"],
                              index=options["productType"].index(reference["productType"]))
    brand = first.selectbox(LABELS["brandDesc"], options["brandDesc"],
                            index=options["brandDesc"].index(reference["brandDesc"]))
    country = first.selectbox(LABELS["shippingCountry"], options["shippingCountry"],
                              index=options["shippingCountry"].index(reference["shippingCountry"]))
    low, high = model["age_range"]
    age = second.number_input(LABELS["age_2021"], min_value=low, max_value=high,
                              value=int(reference["age_2021"]), step=1)
    gender = second.radio("Customer gender", ["Female", "Male"], horizontal=True)
    premier = second.radio("Premier delivery member", ["No", "Yes"], horizontal=True)
    purchase = {"productType": product, "brandDesc": brand, "shippingCountry": country,
                "age_2021": age, "isMale": int(gender == "Male"), "premier": int(premier == "Yes")}
    st.divider()
    result, _ = predict(pd.DataFrame([purchase]), model)
    show_result(result.iloc[0], model)

    st.markdown("**What drives this score**")
    effects = explain(purchase, model)
    effects["value"] = effects["value"].astype(str)
    effects["change"] = effects.effect.map(lambda v: f"{v * 100:+.1f} points")
    st.bar_chart(effects.set_index("input")["effect"] * 100, horizontal=True, height=240,
                 x_label="", y_label="Change in return probability (percentage points)")
    st.dataframe(effects[["input", "value", "change"]], hide_index=True, use_container_width=True)
    st.caption("Each bar compares this purchase with the same purchase using the most common "
               "training value for that one input. Positive bars raise the return risk.")


def batch_upload(model):
    st.subheader("Score a file of purchases")
    st.write("Upload a CSV with these columns: " + ", ".join(f"`{c}`" for c in model["features"]) + ".")
    st.download_button("Download a sample CSV", SAMPLE_FILE.read_bytes(), "sample_purchases.csv", "text/csv")
    upload = st.file_uploader("CSV file", type="csv")
    use_sample = st.checkbox("Use the sample file instead")
    if upload is None and not use_sample:
        return
    try:
        data = pd.read_csv(upload if upload is not None else SAMPLE_FILE)
        result, warnings = predict(data, model)
    except (ValueError, pd.errors.ParserError, UnicodeDecodeError) as error:
        st.error(f"This file could not be scored. {error}")
        return
    for warning in warnings:
        st.warning(warning)
    flagged = result.prediction.eq("Likely return")
    first, second, third = st.columns(3)
    first.metric("Purchases scored", f"{len(result):,}")
    second.metric("Flagged as likely returns", f"{flagged.sum():,}")
    third.metric("Average return probability", f"{result.return_probability.mean():.0%}")
    st.dataframe(result.sort_values("return_probability", ascending=False), hide_index=True,
                 use_container_width=True,
                 column_config={"return_probability": st.column_config.ProgressColumn(
                     "Return probability", min_value=0.0, max_value=1.0, format="percent")})
    st.download_button("Download scored CSV", result.to_csv(index=False).encode("utf-8"),
                       "reclaim_predictions.csv", "text/csv", type="primary")


def about(model):
    st.subheader("About the model")
    st.markdown(f"""
Reclaim estimates whether a single fashion purchase will be returned. It was trained on a
customer-separated sample of the [ASOS GraphReturns dataset](https://osf.io/c793h/) (CC BY 4.0).

- **Model:** histogram gradient boosting (scikit-learn), chosen by validation ROC-AUC.
- **Inputs:** product type, brand, shipping country, customer age, gender and premier membership.
  All of them are known when an order is placed.
- **Cutoff:** {model['threshold']:.2f}, chosen on validation data to balance missed returns and false alarms.
- **Held-out results:** ROC-AUC 0.651 and accuracy 0.607 on 15,040 purchases from unseen customers.

**Limits.** The dataset anonymises most product types, brands and countries (for example `productType_B`),
so the app shows those codes. The source chose customers with return history, so probabilities run
higher than for a typical shopper. Treat the score as a planning signal, not a decision about a customer.
""")


model = get_model()
st.title("Reclaim")
st.write("Estimate the chance that a fashion purchase will be returned, for one order or a whole file.")
single, upload, info = st.tabs(["Single purchase", "Upload a file", "About"])
with single:
    single_purchase(model)
with upload:
    batch_upload(model)
with info:
    about(model)
