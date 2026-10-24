# Deliverable 1: team handoff

The repository is https://github.com/Soban06/Reclaim. Use your own GitHub account and a Git email linked to that account. Review and run the code before committing. The suggested messages below describe actual changes; add your own verification notes after doing the checks.

## Soban — project definition and submission integration

Own the README, environment requirements, problem definition, workflow instructions, report source and compiled PDF. Review the report, especially its item-level prediction target and dataset limitations. Coordinate integration after the two data contributions land.

## Mahad — acquisition and data quality

Assigned files:

- `data scripts/download_data.py`, `data scripts/source_io.py`, `data scripts/clean_data.py`
- `docs/data_card.md`
- `reports/evidence/osf_file_listing.json`, `dataset_metadata.json`, `download_manifest_training.json`, `data_audit.json`

1. Clone/pull the repository and copy the contents of your handoff ZIP into its root, preserving folders.
2. Set up Python as described in the README. Run the download and cleaning commands.
3. Confirm the checksums, original row counts, 520,679 excluded events and 100,000 sampled rows. Read the duplicate policy and confirm why repeated event tuples are retained.
4. Add a short `docs/mahad_validation.md` with what you actually ran, observed and changed. Do not state that you ran checks you did not run.
5. Make meaningful commits, for example:

```sh
git add "data scripts/download_data.py" "data scripts/source_io.py" reports/evidence/osf_file_listing.json reports/evidence/dataset_metadata.json reports/evidence/download_manifest_training.json
git commit -m "Add verified ASOS acquisition and source provenance"
git add "data scripts/clean_data.py" docs/data_card.md reports/evidence/data_audit.json docs/mahad_validation.md
git commit -m "Audit source quality and implement validated event cleaning"
git pull --rebase origin main
git push origin main
```

## Taimur — preprocessing and exploratory analysis

Wait for Mahad's scripts to be available, then pull the repository and copy your ZIP contents into its root.

Assigned files:

- `data scripts/feature_transformers.py`, `preprocess.py`, `eda.py`, `validate_pipeline.py`
- `reports/figures/*.png`
- `reports/evidence/preprocessing_summary.json`, `eda_summary.json`, `validation_results.json`

1. Run the cleaning stage if the local sample does not exist. Then run preprocessing, EDA and validation.
2. Confirm 80,000/20,000 rows, 35 columns and zero shared customers. Inspect the five figures.
3. Check why fitting preprocessing before splitting would leak validation information. Explain the separate, unresolved issue of aggregate-feature timing.
4. Write `docs/taimur_validation.md` recording your actual results and interpretation of at least two charts.
5. Make meaningful commits, for example:

```sh
git add "data scripts/feature_transformers.py" "data scripts/preprocess.py" "data scripts/validate_pipeline.py" reports/evidence/preprocessing_summary.json reports/evidence/validation_results.json
git commit -m "Implement customer-separated feature preprocessing and checks"
git add "data scripts/eda.py" reports/figures reports/evidence/eda_summary.json docs/taimur_validation.md
git commit -m "Add exploratory return analysis and document findings"
git pull --rebase origin main
git push origin main
```

If using GitHub's browser interface, upload the extracted files and directories, not the ZIP archive, and keep the same relative paths. Review first and commit while signed into your own account.

## Before submission

- All three authors must appear in the actual commit history. Preserve author history when integrating; avoid combining everyone's work into a single-author squash commit.
- Confirm the scripts, figures, evidence, README, `.gitignore`, report source and PDF are on `main`.
- Keep raw datasets, processed arrays, local packages and tool binaries out of Git.
- Open the compiled PDF and check names/IDs, charts and limitations.
- Submit the repository URL and compiled report through the course's required channel before the instructor-confirmed deadline.

Commit counts alone do not establish contribution. Each member should be able to explain and modify the part they reviewed and committed.
