# Deliverable 1: step-by-step team guide

Repository: https://github.com/Soban06/Reclaim

This guide is for Windows PowerShell. Run commands one line at a time and wait for each one to finish. If a command fails, stop at that step and read the troubleshooting section.

## Who does what?

| Person | Your part | Order |
| --- | --- | --- |
| Soban | Project setup, problem definition, report and final submission | Setup is available |
| Mahad | Download, inspect and clean the data | First |
| Taimur | Prepare features, make charts and validate the pipeline | After Mahad pushes his scripts |

**Mahad pushes → Taimur pulls and completes his part → Soban checks and submits.**

Each person reads and runs their assigned code, records their own observations and commits using their own GitHub account. The ZIPs contain prepared starting files; investigate any errors and explain the results in your own words. You do not need to invent code changes if the code already works.

## 1. Setup for both members

### 1.1 Get your ZIP from Soban

- Mahad: `Mahad-review-and-commit.zip`.
- Taimur: `Taimur-review-and-commit.zip`.

Keep the ZIP outside your cloned repository. You will copy the extracted folders into the repository later. Do not upload the ZIP itself.

### 1.2 Check Git and Python

Open PowerShell:

~~~powershell
git --version
py -3.12 --version
~~~

Expect a Git version and Python 3.12.x. If missing, install Git for Windows and Python 3.12, then reopen PowerShell. If the Python launcher is unavailable but `python --version` prints Python 3.12, use `python -m venv .venv` in step 1.5.

### 1.3 Clone the repository

Choose a folder in File Explorer where you want to keep the project and open a terminal there:

~~~powershell
git clone https://github.com/Soban06/Reclaim.git
cd Reclaim
git status
~~~

The main `Reclaim` folder containing `README.md` is called the **repository root**. All commands below run from there.

If you already have a clone, open it and run `git status`. If it has no uncommitted changes, update it:

~~~powershell
git pull --ff-only origin main
~~~

Do not create a second Reclaim folder inside the first. If you already have changes, ask Soban before pulling or replacing files.

### 1.4 Set your own Git identity

Mahad runs:

~~~powershell
git config user.name "Mahad Jawad Rana"
~~~

Taimur runs:

~~~powershell
git config user.name "Taimur Amir"
~~~

Both run the following after replacing `YOUR_GITHUB_EMAIL` with an email connected to their own GitHub account:

~~~powershell
git config user.email "YOUR_GITHUB_EMAIL"
git config --get user.name
git config --get user.email
~~~

Find your linked email in GitHub → Settings → Emails. You can use the exact GitHub-provided no-reply address shown there for privacy. Do not use Soban's email.

These commands set the author for this repository only. When Git asks you to sign in during a push, use your own collaborator account: `Mahad-Jawad` or `taimurrrr`.

### 1.5 Install the Python dependencies

From the repository root:

~~~powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
~~~

Wait for the install to finish without an error. The commands below use this Python executable directly, so you do not need to activate the environment or change PowerShell execution policy.

Allow roughly 2 GB of free space and several GB of available RAM.

### What Git commands mean

- **Clone:** download a working copy of the repository.
- **Pull:** bring other members' commits into your copy.
- **Commit:** save a named snapshot of selected changes on your computer.
- **Push:** upload your commits to GitHub.
- **Stage / git add:** select the files for your next commit.

## 2. Mahad: acquisition and cleaning

### 2.1 Copy your assigned files

1. Extract `Mahad-review-and-commit.zip`.
2. Open the extracted folder.
3. Copy its `data scripts`, `docs` and `reports` folders.
4. Paste them beside `README.md` inside your cloned `Reclaim` folder.
5. Merge folders, keeping unrelated existing files.

The resulting paths must look like this:

~~~text
Reclaim/
  README.md
  data scripts/
    download_data.py
    source_io.py
    clean_data.py
  docs/
    data_card.md
  reports/
    evidence/
      osf_file_listing.json
      dataset_metadata.json
      download_manifest_training.json
      data_audit.json
~~~

There should not be an extra `Mahad-review-and-commit` folder between `Reclaim` and `data scripts`. If Windows asks to replace an existing assigned file, check with Soban that it is not a newer version someone has already changed.

### 2.2 Understand your scripts

| File | Purpose |
| --- | --- |
| `download_data.py` | Downloads the original data, verifies checksums and records its source |
| `source_io.py` | Verifies and reads the expected original tables |
| `clean_data.py` | Audits data quality, joins tables and creates a 100,000-event sample |

A **checksum** is a file fingerprint used to check the download. A **join** combines purchase, customer and product information using their IDs. Open the scripts and read their comments before running them.

### 2.3 Download the data first

~~~powershell
.\.venv\Scripts\python.exe "data scripts/download_data.py"
~~~

Keep the quotes: the folder name contains a space.

Wait for all three messages:

~~~text
Verified event_table_training.p
Verified product_nodes_training.p
Verified customer_nodes_training.p
~~~

The script creates `data/raw/` automatically and downloads about 364 MB. It also updates the source metadata and download manifest in `reports/evidence/`. Your verification timestamps will differ from Soban's run; that is expected.

**The raw data is deliberately excluded from GitHub and from the handoff ZIPs. Every computer needs its own download. An empty data/raw folder is not sufficient.**

Do not manually edit the downloaded files or fetch the testing split for this milestone.

### 2.4 Run cleaning

After downloading succeeds:

~~~powershell
.\.venv\Scripts\python.exe "data scripts/clean_data.py"
~~~

This creates:

- `data/processed/development_sample.csv` — input for Taimur's scripts.
- `reports/evidence/data_audit.json` — the audit results.

Open the audit JSON in your editor. The unchanged source and default sample size should give:

| Result | Expected value |
| --- | ---: |
| Raw purchase events | 1,369,133 |
| Customer records | 777,001 |
| Product records | 411,495 |
| Events excluded because a required node is absent | 520,679 |
| Complete events after joining | 848,454 |
| Sample rows | 100,000 |
| Sample return rate | 0.54484 = 54.484% |

There are 6,551 repeated customer-product-outcome combinations. We retain them because the data cannot distinguish accidental duplicate records from real repeat purchases. Customer/product-table duplicates are removed by the implementation before checking unique IDs; none were found in those tables.

If results differ, save the error/output and tell Soban. Do not edit results just to match the expected numbers.

### 2.5 Write your own verification notes

Create `docs/mahad_validation.md`. Use these prompts and fill them with your actual observations:

~~~text
# Mahad's data validation

Date and Python version:
Commands I ran:
Did all three file checksums pass?
Raw event count:
Complete event count:
Sample row count:
Why repeated event tuples are retained:
One data-quality issue or limitation I noticed:
Code changes I made, if any, and why:
~~~

It is fine to say no code changes were needed. Do not claim a command passed if you did not run it.

### 2.6 Commit the acquisition files

~~~powershell
git status --short
git add "data scripts/download_data.py" "data scripts/source_io.py" reports/evidence/osf_file_listing.json reports/evidence/dataset_metadata.json reports/evidence/download_manifest_training.json
git diff --cached --stat
git commit -m "Add verified ASOS acquisition and source provenance"
~~~

`git diff --cached --stat` lists the selected files. Raw data and `.venv` should not appear.

### 2.7 Commit cleaning and notes

~~~powershell
git add "data scripts/clean_data.py" docs/data_card.md reports/evidence/data_audit.json docs/mahad_validation.md
git diff --cached --stat
git commit -m "Audit source quality and implement validated event cleaning"
~~~

### 2.8 Push and confirm

~~~powershell
git pull --rebase origin main
git push origin main
~~~

If either fails, see troubleshooting. Do not force-push.

Open GitHub and confirm your scripts, notes and commits are visible, with your GitHub account attached to the commits. Tell Soban and Taimur that your work is pushed.

## 3. Taimur: preprocessing, EDA and checks

### 3.1 Pull Mahad's scripts

After Mahad confirms his push, go to your cloned repository:

~~~powershell
git status
git pull --ff-only origin main
Test-Path "data scripts/download_data.py"
Test-Path "data scripts/clean_data.py"
~~~

Both `Test-Path` commands should print `True`. Pull before copying your ZIP files. If you already have uncommitted changes, check with Soban before pulling.

Extract your ZIP and copy its `data scripts` and `reports` folders into the repository root, merging folders. Your four scripts must sit beside Mahad's three:

- `feature_transformers.py`
- `preprocess.py`
- `eda.py`
- `validate_pipeline.py`

### 3.2 Download and clean on your own computer

**Mahad running the downloader does not put the data on your computer. GitHub does not contain the raw files or generated sample.**

Run these in order, waiting for each to finish successfully:

~~~powershell
.\.venv\Scripts\python.exe "data scripts/download_data.py"
Get-ChildItem data/raw
.\.venv\Scripts\python.exe "data scripts/clean_data.py"
~~~

The folder listing must contain all three completed files:

~~~text
event_table_training.p
product_nodes_training.p
customer_nodes_training.p
~~~

If you only see a `.partial` file, that download is not complete. Rerun the downloader and wait for all three `Verified` messages before cleaning.

The cleaning command creates `data/processed/development_sample.csv`. Keep the default 100,000-row sample so your results can be compared with the report. If you already successfully downloaded and cleaned in this same checkout, you may reuse the local sample.

### 3.3 Understand your scripts

| File | Purpose |
| --- | --- |
| `feature_transformers.py` | Learns numerical limits for extreme values from training data |
| `preprocess.py` | Splits customers, handles missing values, scales numbers and encodes categories |
| `eda.py` | Creates five charts and their summary statistics |
| `validate_pipeline.py` | Checks the split and saved preprocessing outputs |

**Features** are inputs a model will use. **Encoding** turns categories into numerical columns. **Scaling** makes numerical values more comparable.

The training set is where preparation learns its settings. The validation set is kept separate for later assessment. Events belonging to one customer must not appear in both.

### 3.4 Run preprocessing

~~~powershell
.\.venv\Scripts\python.exe "data scripts/preprocess.py"
~~~

Open `reports/evidence/preprocessing_summary.json` and confirm:

| Result | Expected value |
| --- | ---: |
| Training rows | 80,000 |
| Validation rows | 20,000 |
| Customers shared between the two sets | 0 |
| Transformed feature columns | 35 |

The script creates feature matrices, labels and a saved preprocessor in `data/processed/`. They stay local.

Understand these two separate issues:

1. Missing-value rules, numerical limits, scaling settings and category lists are learned from training rows only. Using validation rows to learn them would allow validation information to influence preparation.
2. The source's average price and discount may include information from the target period. Customer separation does not resolve that timing uncertainty. The current work demonstrates preprocessing; it is not a production-ready return predictor.

### 3.5 Make and inspect the charts

~~~powershell
.\.venv\Scripts\python.exe "data scripts/eda.py"
~~~

Open all five images in `reports/figures/`:

| Image | What it shows |
| --- | --- |
| `class_distribution.png` | Kept versus returned events in the raw release |
| `price_discount.png` | Price/discount distributions; the top 1% is omitted from display only |
| `product_return_rates.png` | Return frequency across product types |
| `correlations.png` | Numerical associations; these do not prove causation |
| `country_audit.png` | Descriptive differences across anonymized country groups |

Make sure labels are readable and not cut off. Statistics are in `reports/evidence/eda_summary.json`. The country chart describes the data; it is not evidence that a trained model is fair.

### 3.6 Run validation

~~~powershell
.\.venv\Scripts\python.exe "data scripts/validate_pipeline.py"
~~~

Expect `"status": "passed"`. Open `reports/evidence/validation_results.json` and check:

- Training shape: `[80000, 35]`.
- Validation shape: `[20000, 35]`.
- Eight passing checks covering customer separation, excluded targets, missing/unseen/extreme inputs, unchanged fitted settings, matrix dimensions and label alignment.

These checks verify the pipeline, not prediction accuracy. No prediction model is trained in this milestone.

### 3.7 Write your own verification notes

Create `docs/taimur_validation.md` and fill in your own results:

~~~text
# Taimur's preprocessing and EDA validation

Date and Python version:
Commands I ran:
Training rows, validation rows and feature columns:
Customer overlap:
Validation script result:
My observation from one chart:
My observation from a second chart:
Why preparation is fitted on training rows only:
One limitation I noticed:
Code changes I made, if any, and why:
~~~

If your results differ from the report, tell Soban so the code, evidence and report can be reconciled before submission.

### 3.8 Commit preprocessing and checks

~~~powershell
git status --short
git add "data scripts/feature_transformers.py" "data scripts/preprocess.py" "data scripts/validate_pipeline.py" reports/evidence/preprocessing_summary.json reports/evidence/validation_results.json
git diff --cached --stat
git commit -m "Implement customer-separated feature preprocessing and checks"
~~~

### 3.9 Commit charts and your interpretation

~~~powershell
git add "data scripts/eda.py" reports/figures reports/evidence/eda_summary.json docs/taimur_validation.md
git diff --cached --stat
git commit -m "Add exploratory return analysis and document findings"
~~~

Your local download may also change Mahad's committed metadata timestamps. Inspect remaining tracked changes:

~~~powershell
git diff --name-only
~~~

If the only remaining tracked changes are fresh download metadata and you did not intentionally edit them, you can return those three files to their committed versions:

~~~powershell
git restore -- reports/evidence/osf_file_listing.json reports/evidence/dataset_metadata.json reports/evidence/download_manifest_training.json
~~~

This discards your local changes to those three metadata files only. It leaves your downloaded data and committed work intact. If other files changed or you want to preserve your metadata edits, ask Soban instead of restoring blindly.

### 3.10 Push and confirm

~~~powershell
git status
git pull --rebase origin main
git push origin main
~~~

Check on GitHub that your four scripts, five charts, verification notes and commits are visible. Tell Soban when finished.

## 4. Troubleshooting

| Problem | What to do |
| --- | --- |
| `FileNotFoundError` for `data/raw/event_table_training.p` | Run `download_data.py` first on this computer. Creating an empty folder does not download the file. Wait for all three verified files, then rerun cleaning. |
| A script or requirements file cannot be found | Run `Get-Location` and `Get-ChildItem`. Go to the folder containing `README.md`. |
| The virtual-environment Python cannot be found | Complete setup step 1.5 from the repository root. |
| `ModuleNotFoundError` | Repeat dependency installation using `.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt`. |
| Download timeout or network error | Check the connection and rerun the downloader. Verified files are reused; incomplete files download again. |
| Checksum mismatch | Stop and share the error with Soban. Do not remove the check. |
| Missing `development_sample.csv` | Run downloading and cleaning before preprocessing or EDA. |
| Different counts or a failed check | Record the output and consult Soban; do not edit evidence to say it passed. |
| `Author identity unknown` | Complete step 1.4 and retry committing. |
| `nothing to commit` | Check the file locations and whether they were already committed. Do not create empty commits. |
| Push authentication/permission error | Check `git remote -v` and sign in with your own collaborator account. |
| Push rejected because GitHub has newer commits | Commit your intended work, inspect remaining changes, pull with rebase, then retry the push. |
| A rebase conflict appears | Stop. Run `git rebase --abort` to return to the state before that rebase, then ask Soban to reconcile the files. |

An LF/CRLF warning is normally a Windows line-ending warning; check whether the command actually finished successfully.

Use the explicit `git add` file lists above to review what you upload. Raw datasets, processed samples/matrices, environments and tools should stay out of Git. Do not force-push or use another member's identity.

If using GitHub's website instead of Git to upload, upload the extracted files and folders, preserving their paths, while signed into your own account. Uploading files does not replace running and understanding them.

## 5. Soban: final integration and submission

After both members confirm their pushes:

1. Inspect GitHub's commit history and confirm all three accounts are represented.
2. Read both members' verification notes.
3. Reconcile any differences between their results and the report.
4. If figures changed, update `reports/deliverable1/images/` and recompile.
5. Confirm the README, ignore rules, all seven Python scripts, dataset card, evidence, charts, LaTeX source and PDF are present.
6. Check that large data files, local environments/tools and handoff ZIPs are excluded.
7. Open the PDF and verify names, IDs, charts and wording.
8. Submit the GitHub URL and compiled PDF through the course submission channel.

Everyone should be able to explain and modify the work they reviewed. Commits record the work as it happened; counts alone do not establish understanding.
