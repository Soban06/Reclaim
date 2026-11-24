# Reclaim

Reclaim predicts whether a single fashion purchase will be returned. It is a Track A (application development) project for the Artificial Intelligence course. Operations, inventory and customer-experience teams can score one order or a whole CSV file in a Streamlit web app and see the return probability, a likely-return or likely-keep decision, and the inputs that drive the score.

**Live app:** [reclaim-return-risk.streamlit.app](https://reclaim-return-risk.streamlit.app)

## Deliverables

| Deliverable | Report | Main outputs |
| --- | --- | --- |
| 1. Data foundations | [PDF](output/pdf/Reclaim_Deliverable_1.pdf), [LaTeX](reports/deliverable1/main.tex) | [Data card](docs/data_card.md), [data audit](reports/evidence/data_audit.json) |
| 2. Model and evaluation | [PDF](output/pdf/Reclaim_Deliverable_2.pdf), [LaTeX](reports/deliverable2/main.tex) | [Validation](reports/evidence/d2_validation.json), [held-out results](reports/evidence/d2_test.json) |
| 3. Final deployment and report | [PDF](output/pdf/Reclaim_Final_Report.pdf), [LaTeX](reports/final/main.tex) | [Streamlit app](app/streamlit_app.py), [final model](models/final_model.joblib), [held-out results](reports/evidence/final_test.json) |

## Team

| Member | Student ID | GitHub | Deliverable 3 work |
| --- | --- | --- | --- |
| Muhammad Soban Sohail | 24L-2545 | [Soban06](https://github.com/Soban06) | Streamlit app, deployment, final report and README |
| Mahad Jawad Rana | 24L-2504 | [Mahad-Jawad](https://github.com/Mahad-Jawad) | Prediction backend, input checks, tests and held-out evaluation |
| Taimur Amir | 24L-2518 | [taimurrrr](https://github.com/taimurrrr) | Final model training, cutoff selection and training history |

AI assistance was used to generate code and draft documentation. The team reviewed, ran and committed each part.

## Results

All scores come from 15,040 held-out purchases made by customers who were not used for training or model selection.

| Method | Accuracy | Precision | Recall | F1 | ROC-AUC |
| --- | ---: | ---: | ---: | ---: | ---: |
| Always predict returned | 0.547 | 0.547 | 1.000 | 0.707 | 0.500 |
| Product-type return-rate rule | 0.580 | 0.666 | 0.466 | 0.548 | 0.607 |
| Deliverable 2 logistic model | 0.547 | 0.547 | 1.000 | 0.707 | 0.614 |
| **Final gradient boosting model** | **0.607** | **0.678** | **0.536** | 0.599 | **0.651** |

The Deliverable 2 model chose its cutoff by F1 and flagged every purchase. The final model adds shipping country, customer age, gender and premier membership, and chooses its cutoff (0.57) by balanced accuracy on validation data. It flags 6,513 of the 15,040 held-out purchases.

## Run the app locally

Use Python 3.12 or newer. From the repository root:

```sh
python -m venv .venv
```

Activate it with `.venv\Scripts\Activate.ps1` in Windows PowerShell or `source .venv/bin/activate` on macOS and Linux. Then run:

```sh
python -m pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

The app opens at http://localhost:8501. It loads the trained model from `models/final_model.joblib`, so it does not need the dataset.

- **Single purchase:** pick a product type, brand, shipping country and customer details, and the score updates straight away.
- **Upload a file:** upload a CSV with the columns `productType`, `brandDesc`, `shippingCountry`, `age_2021`, `isMale` and `premier`. You can download [a sample file](app/sample_purchases.csv) from the app. Results can be downloaded as a CSV.

Run the tests with:

```sh
python -m pytest
```

## Reproduce the results

These steps rebuild the data, models, figures and evidence files. The download needs internet access and about 364 MB. Use `requirements-lock.txt` for the exact package versions used to train the published model (scikit-learn 1.9.1).

```sh
python -m pip install -r requirements-lock.txt
python "data scripts/download_data.py"
python "data scripts/clean_data.py"
python src/load_data.py
python src/make_split.py
python src/baselines.py
python src/train_models.py
python src/evaluate_model.py
python src/check_errors.py
python src/train_final.py
python src/evaluate_final.py
```

The Deliverable 2 scripts write working files to `data/processed/`. `train_final.py` saves the final model to `models/`. Summary files go to `reports/evidence/` and figures to `reports/figures/`. The Deliverable 1 scripts `preprocess.py`, `eda.py` and `validate_pipeline.py` in `data scripts/` reproduce the earlier preprocessing and charts.

To rebuild the final report with [Tectonic](https://tectonic-typesetting.github.io/):

```sh
tectonic reports/final/main.tex --outdir output/pdf
```

Then rename `output/pdf/main.pdf` to `output/pdf/Reclaim_Final_Report.pdf`.

## Repository layout

| Path | Contents |
| --- | --- |
| `app/` | Streamlit app and sample upload file |
| `src/` | Data loading, split, baselines, training, evaluation and the prediction backend (`predict.py`) |
| `data scripts/` | Deliverable 1 download, cleaning, preprocessing and charts |
| `models/` | Trained Deliverable 2 and final models |
| `tests/` | Tests for the prediction backend |
| `reports/` | LaTeX reports, figures and JSON evidence |
| `docs/` | Problem definition, data card and team notes |

## Data and limitations

The data is the [ASOS GraphReturns dataset](https://osf.io/c793h/), described by [McGowan et al. (2023)](https://arxiv.org/abs/2302.14096) and licensed CC BY 4.0. Reclaim is not affiliated with ASOS. The raw and processed data are not stored in this repository.

- The target is one purchase event, because the data has no order or basket IDs.
- Most product types, brands and countries are anonymised (for example `productType_B`), so the app shows those codes.
- The source selected customers with a return history, so probabilities are higher than for a typical shopper.
- Average price and discount were left out because it is unclear when they were recorded.
- A ROC-AUC of 0.651 means the model ranks returns better than chance and better than the baselines, but it will still make many mistakes. Use it as a planning signal, not to make decisions about individual customers.

See the [data card](docs/data_card.md) for full provenance.
