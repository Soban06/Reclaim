# Validation Report – Taimur

## 1. Data Constraint Confirmation

Source: `reports/evidence/validation_results.json` (overall status: **passed**).

| Constraint | Expected | Observed | Status |
|---|---|---|---|
| Train rows | 80,000 | 80,000 | ✅ |
| Validation rows | 20,000 | 20,000 | ✅ |
| Feature columns | 35 | 35 (train and validation) | ✅ |
| Customer overlap (train ∩ validation) | 0 | 0 (`customer isolation` check passed) | ✅ |

Train shape is `(80000, 35)` and validation shape is `(20000, 35)`, so both
matrices have identical feature dimensions.

The full set of checks that passed: customer isolation, target excluded from
features, missing-value transformation, unknown-category transformation,
extreme-value transformation, no transform-time refitting, matrix dimensions,
and label alignment.

### Leakage safeguards
- **Fit on train only.** Scalers and imputers are fit on the training set and
  only applied (`transform`) to validation. Fitting before the split would let
  validation statistics (mean, variance, min/max) shape the preprocessing, so
  the model would indirectly see the validation distribution and metrics would
  be inflated. The `no transform-time refitting` check confirms nothing is
  refit at transform time.
- **Aggregate-feature timing.** Aggregates such as "customer average purchase
  amount" must be computed only from data before the prediction timestamp.
  Computing them over the whole timeline before a chronological split would
  push future information into past records.
- **Target exclusion.** The `target excluded from features` check confirms the
  label is not among the 35 features.

## 2. Figure Analysis

### Figure 1: `class_distribution.png` (return outcomes)
**Evidence:** In the raw training release, 611,906 events were kept (44.7%)
and 757,227 were returned (55.3%).

**What it proves:**
- The target is moderately imbalanced toward returns, but not severely so.
  The minority class is still about 45% of the data, so no resampling is
  strictly required.
- A trivial "always predict returned" classifier would score about 55.3%
  accuracy. That is the baseline any model must beat, and it is why precision,
  recall, and AUC should be reported alongside accuracy.
- The split should be checked for preserving this ratio in both train and
  validation. (Note this figure covers the raw release, not the 80k/20k sample.)

### Figure 2: `correlations.png` (Pearson correlations)
**Evidence:** Correlation with the target (`Returned`): average price +0.13,
average discount -0.03, Premier 0.00. Correlations among the predictors are
all near zero (-0.03 to 0.01).

**What it proves:**
- No numeric feature is a near-perfect proxy for the target, so there is no
  sign of direct target leakage in these variables.
- Price has only a weak positive linear association with returns, and
  discount and Premier status have essentially none. Any predictive power must
  come from other features (such as categorical ones) or non-linear
  interactions.
- The predictors are nearly uncorrelated with each other, so multicollinearity
  is not a concern for these four variables.
- Pearson only measures linear association and does not imply causation.

### Figure 3: `price_discount.png` (distributions)
**Evidence:** Average price is strongly right-skewed. It peaks around 10-20
GBP with a long tail toward 100 (top 1% omitted from display). Average
discount is roughly symmetric and bell-shaped, centred near 17-18 with almost
all values between about 12 and 21.

**What it proves:**
- Price has extreme values, which justifies the extreme-value handling that
  the `extreme-value transformation` check validates (for example clipping
  or a log/robust transform) so outliers don't dominate scaling.
- Discount is well behaved and needs no special treatment beyond standard
  scaling.

### Additional figures (descriptive)
- `product_return_rates.png`: return rates vary widely by product type, from
  about 0.43 (productType_H) to about 0.72 (productType_B), so product type
  is likely an informative categorical feature.
- `country_audit.png`: observed return fractions range from about 0.43
  (Country_D) to about 0.69 (Country_E). This is a descriptive audit only
  (as its title says), not a model fairness assessment.

## 3. Conclusion
The pipeline meets all stated constraints: 80,000 training rows, 20,000
validation rows, 35 features, and no customer overlap, with all eight
validation checks passing. The figures show a moderately imbalanced target, a
skewed price feature that needs robust handling, and weak linear relationships
between the numeric features and returns.