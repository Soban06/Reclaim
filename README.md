# Reclaim

Reclaim is a Track A AI project for estimating whether an individual fashion purchase will be returned. The Deliverable 2 model uses product type and brand to score purchase events.

## Deliverables

- **Deliverable 1 — Data foundations:** [report](output/pdf/Reclaim_Deliverable_1.pdf) and [LaTeX source](reports/deliverable1/main.tex).
- **Deliverable 2 — Model and evaluation:** [report](output/pdf/Reclaim_Deliverable_2.pdf), [LaTeX source](reports/deliverable2/main.tex), [validation results](reports/evidence/d2_validation.json), and [held-out results](reports/evidence/d2_test.json).
- **[Download the trained model](https://raw.githubusercontent.com/Soban06/Reclaim/3317eb0d46996ac69a0430b513bf9ddc4d84a55c/models/d2_model.joblib)** (2,976 bytes). The file contains the fitted scikit-learn pipeline, the two input column names, and the validation-selected cutoff. Use scikit-learn 1.9.1 to load it. Load only a trusted copy of the artifact.

## Team

| Member | Student ID | GitHub | Deliverable 2 work |
| --- | --- | --- | --- |
| Muhammad Soban Sohail | 24L-2545 | [Soban06](https://github.com/Soban06) | Held-out metrics and group error analysis |
| Mahad Jawad Rana | 24L-2504 | [Mahad-Jawad](https://github.com/Mahad-Jawad) | Data checks, customer split, and split evidence |
| Taimur Amir | 24L-2518 | [taimurrrr](https://github.com/taimurrrr) | Baselines, model selection, and learning curves |

AI assistance was used to generate code and draft documentation. The report maps repository commits to the files and outputs they added.

## Reproduce Deliverable 2

Run from the repository root. Use an environment that can install the pinned packages in [requirements-lock.txt](requirements-lock.txt). The published evaluation run used Python 3.14 and scikit-learn 1.9.1. The following commands use the Python executable in your active environment.

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
```

Acquisition needs internet access and downloads about 364 MB. The training and evaluation commands create their working files in data/processed/, including a regenerated d2_model.joblib. Summary JSON and figures go to reports/evidence/ and reports/figures/. Run the original Phase 1 scripts preprocess.py, eda.py, and validate_pipeline.py under data scripts/ to reproduce the earlier preprocessing and EDA.

To rebuild the Deliverable 2 PDF from the repository root in PowerShell:

```sh
tectonic reports/deliverable2/main.tex --outdir output/pdf
if ($LASTEXITCODE -eq 0) { Move-Item -Force output/pdf/main.pdf output/pdf/Reclaim_Deliverable_2.pdf }
```

## Evaluation

The 100,000-event development sample was divided by customer into 69,996 training, 14,964 validation, and 15,040 test events, with zero customer overlap. Preprocessing was fitted on training data. Validation selected logistic regression and a cutoff of 0.42. Test results were:

| Method | Accuracy | Precision | Recall | F1 | ROC-AUC |
| --- | ---: | ---: | ---: | ---: | ---: |
| Always predict returned | 0.547 | 0.547 | 1.000 | 0.707 | 0.500 |
| Product-type return-rate rule | 0.580 | 0.666 | 0.466 | 0.548 | 0.607 |
| Logistic regression | 0.547 | 0.547 | 1.000 | 0.707 | 0.614 |

The logistic model ranked returns slightly better than the product-type rule. At 0.42 it flagged all 15,040 test purchases, including all 6,808 kept purchases. The report documents this operating-point failure and the [group error analysis](reports/evidence/d2_errors.json).

## Data and scope

The [ASOS GraphReturns dataset](https://osf.io/c793h/) is described by [McGowan et al.](https://arxiv.org/abs/2302.14096) and listed as CC BY 4.0 by OSF. Reclaim uses a sample of joined events from the original training release. About 38% of raw events lacked a required customer or product match. The source selected customers with return history, and the separate later-period release was unused. The target is an individual purchase event, since the release has no basket identifiers. Product-average price and discount were excluded because their timing is uncertain. Shipping country was used for error analysis. See the [data card](docs/data_card.md) for provenance and limitations.
