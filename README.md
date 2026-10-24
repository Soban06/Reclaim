# Reclaim

**AI-assisted return-risk prediction for e-commerce â€” Track A, Application Development.**

Reclaim aims to help e-commerce operations teams anticipate product returns. The planned application will accept purchase information and present a return-risk score. The current milestone implements the data foundations; a trained model and hosted application are future work.

## Team

| Member | Student ID | GitHub | Proposed responsibility |
| --- | --- | --- | --- |
| Muhammad Soban Sohail | 24L-2545 | [Soban06](https://github.com/Soban06) | Problem definition, report and integration |
| Mahad Jawad Rana | 24L-2504 | [Mahad-Jawad](https://github.com/Mahad-Jawad) | Acquisition, provenance and cleaning |
| Taimur Amir | 24L-2518 | [taimurrrr](https://github.com/taimurrrr) | Preprocessing, EDA and validation |

Each member reviews, runs and commits their own contribution. AI assistance was used in drafting and implementation; the team is responsible for understanding and validating the submission.

## Deliverable 1

- Problem statement, target audience and ML justification.
- Original-source download script, metadata and SHA-256 verification.
- Python cleaning, explicit duplicate policy, missing-value handling and outlier treatment.
- Train-fitted scaling/encoding and customer-separated validation split.
- Five EDA figures, a descriptive bias audit and machine-readable evidence.
- [LaTeX source](reports/deliverable1/main.tex) and compiled report (added after compilation).

## Dataset and scope

Source: [ASOS GraphReturns on OSF](https://osf.io/c793h/), described by [McGowan et al. (2023)](https://arxiv.org/abs/2302.14096), licensed **CC BY 4.0** according to OSF metadata. Credit belongs to the original dataset creators. Reclaim selects fields, joins tables, samples events and transforms features; it is not affiliated with ASOS.

The downloaded training release contains 1,369,133 purchase events, 777,001 customer rows and 411,495 product rows (about 364 MB). Raw/processed data is ignored by Git and obtained from the original repository. Allow roughly 2 GB of disk space and several GB of available RAM when running the pipeline.

The target is **an individual purchase event's return outcome**, not a complete multi-item order. The data lacks order IDs and exact event dates. Price/discount fields are product averages; shipping country is available, but shipping method and delivery duration are not.

### Important findings

- 520,679 events lack at least one required node match. The usable join contains 848,454 events. Exclusion counts are recorded in `reports/evidence/data_audit.json`.
- A deterministic 100,000-event sample yields 80,000 training and 20,000 validation rows, with zero customer overlap and 35 transformed features.
- The raw return rate is about 55.31%; the development sample rate is 54.484%.
- Customers were selected for having return history; these rates are not population estimates.
- Return-rate/count/reason features are excluded because their timing is uncertain. Average price/discount timing also needs verification before production modeling. This is a preprocessing demonstration, not a leakage-free performance benchmark.
- Repeated event tuples are preserved because they may represent real repeat purchases. Node duplicates are removed before key validation (none found in this release).

## Run locally

Python 3.12 is recommended. From the repository root:

```sh
python -m venv .venv
```

Activate on Windows PowerShell with `.venv\Scripts\Activate.ps1`, or on macOS/Linux with `source .venv/bin/activate`. Then:

```sh
python -m pip install -r requirements.txt
python "data scripts/download_data.py"
python "data scripts/clean_data.py"
python "data scripts/preprocess.py"
python "data scripts/eda.py"
python "data scripts/validate_pipeline.py"
```

The first command downloads the original three training tables and records their provenance. The next commands create an ignored development CSV, sparse matrices, labels, the fitted preprocessor, evidence JSON files and figures. For a smaller development run, pass `--sample-size 10000` to `clean_data.py`; regenerate all downstream results and the report if the sample changes.

Only checksum-pinned original files are supported by the source loader. Do not replace them with arbitrary pickle files. The optional downloader `--split testing` retrieves the official later-period files, but the current cleaning script intentionally processes training files only.

### Repository layout

```text
data scripts/              Acquisition, cleaning, preprocessing, EDA and validation
data/raw/                  Original files (ignored)
data/processed/            Generated sample, matrices and preprocessor (ignored)
docs/                      Problem definition, data card and team workflow
reports/evidence/          Download manifests, quality audit and run summaries
reports/figures/           Reproducible EDA charts
reports/deliverable1/      Self-contained LaTeX source and image copies
output/pdf/                Compiled submission report
```

### Build the report

Upload the contents of `reports/deliverable1/` to Overleaf and compile `main.tex`, or use a local LaTeX installation. Copy updated figures into `reports/deliverable1/images/` if rerunning EDA. A local Tectonic installation can compile with:

```sh
tectonic reports/deliverable1/main.tex --outdir output/pdf
```

## Validation and later milestones

`validate_pipeline.py` checks customer isolation, excluded targets, label alignment, saved matrix dimensions, missing/unseen/extreme inputs and unchanged fitted parameters during transformation. These are pipeline checks, not model evaluation.

Next: resolve timing/provenance limitations; compare simple baselines and classifiers; evaluate discrimination, calibration and group performance; then host the frontend and model backend.
