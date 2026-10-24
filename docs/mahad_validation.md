# Mahad validation: acquisition and data quality

Run date: 2026-10-24

## What I ran

- Copied the handoff ZIP contents into the repo root and set up the `.venv` from the README.
- `python "data scripts/download_data.py"`
- `python "data scripts/clean_data.py"`
- Compared `download_manifest_training.json` against the OSF file listing by hand (size and SHA-256).

## What I observed

- **Checksums:** size and SHA-256 match the OSF listing for all 3 training files (events 32,859,910 B, product nodes 143,204,587 B, customer nodes 188,037,655 B). The 3 testing files in the listing were not downloaded.
- **Original row counts:** events 1,369,133; customers 777,001; products 411,495.
- **Excluded events:** 520,679 (71,648 unmatched customers, 474,590 unmatched products), matching the expected figure.
- **Joined events:** 848,454 (1,369,133 - 520,679).
- **Sampled rows:** 100,000 (seed 42), matching the expected figure.
- **Duplicate policy:** 6,551 exact duplicate event rows are kept. The events table has only variant, customer and outcome, with no order ID or timestamp, so a repeated row can't be told apart from a real repeat purchase. Exact duplicates in the customer and product tables are removed (none found).

## What I changed

No source changes; ran the provided scripts as-is.

## Not checked

- I did not recompute file hashes locally (for example with `Get-FileHash`).
