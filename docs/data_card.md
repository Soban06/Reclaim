# Dataset card: ASOS GraphReturns

- Original repository: https://osf.io/c793h/
- Paper: https://arxiv.org/abs/2302.14096
- License recorded by OSF: Creative Commons Attribution 4.0 International.
- Source: real anonymized fashion retail purchases and returns, published by the dataset authors.
- This run: three training tables only; the official test period is untouched.
- Acquisition: download original files, verify SHA-256, save timestamps and metadata.
- Modifications: selected unambiguous columns, validated joins, excluded events lacking nodes, sampled 100,000 events with seed 42, fitted preprocessing on the training split.

## Feature contract

| Field | Meaning | Use |
| --- | --- | --- |
| `isReturned` | Binary purchase-event outcome | Label only |
| `hash(customerId)` | Anonymized customer key | Join and group split |
| `hash(variantID)` | Anonymized product-variant key | Join only |
| `avgGbpPrice` | Product-average price in GBP | Provisional numerical feature |
| `avgDiscountValue` | Product-average discount, source units | Provisional numerical feature |
| `productType`, `brandDesc` | Mostly anonymized product categories | One-hot features |
| `shippingCountry` | Anonymized country category | One-hot feature and descriptive audit |
| `premier` | Customer membership indicator | Categorical feature |
| `yearOfBirth`, `isMale` | Demographic fields | Audit only; excluded from prediction |
| Counts, return rates and reason proportions | Aggregate behavioral statistics | Excluded pending timing verification |

Average price and discount are not exact order-time values. Their temporal provenance remains unresolved. Do not present models trained with these fields as production-ready.

## Quality and selection limitations

The source contains 6,551 repeated event tuples but no event identifier to determine whether they are duplicate records. They are preserved. Node duplicates are removed by the implementation; no exact duplicates were observed. Duplicate return-reason column names are avoided by selecting explicit fields.

Of 1,369,133 events, 520,679 lack a required node match. Their exclusion leaves 848,454 complete events. This may introduce selection bias and requires investigation. Raw missing cells are zero; invalid approximate ages are marked missing for auditing. No financial invalid values were found in the retained events.

The paper states that customers have at least one return. The data cannot estimate return prevalence across all customers or retailers. Country labels cannot be interpreted as named countries. Demographic exclusion does not eliminate proxy bias.

The current 80/20 split separates customer identities, not time. No future performance, fairness, calibration or savings claim is supported by this milestone.
