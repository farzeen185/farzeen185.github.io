# Requested spatial and temporal figure coverage

The revised AIT report contains **21 numbered figures** and the separate manuscript contains **22**. The original 60-page report structure is retained. Each all-basin temporal atlas has 22 basin subplots, with identifiers linked to Appendix A. Original observation gaps remain visible.

| Requested content | AIT report figure | Manuscript figure |
|---|---|---|
| Spatial GRACE TWSA and derived GWSA trends, Sen slopes and Mann–Kendall FDR | 5.1 | 2 |
| Observed temporal subplots for all 22 basins | 5.2 | 3 |
| Climate baseline and emulator spatial trends | 5.4 | 5 |
| TWSA climate reconstruction, all-basin temporal subplots | 5.5 | 6 |
| GWSA climate reconstruction, all-basin temporal subplots | 5.6 | 7 |
| Climate-model NSE, anomaly NSE and RMSE spatial maps | 5.7 | 8 |
| Climate-model annual held-out metrics through time | 5.8 | 9 |
| TWSA/GWSA residual and modeled-human spatial trends | 5.9 | 11 |
| TWSA residual and modeled-human temporal subplots | 5.10 | 12 |
| GWSA residual and modeled-human temporal subplots | 5.11 | 13 |
| Matched GLDAS and naturalized land-storage spatial comparison | 5.12 | 15 |
| Matched GLDAS and naturalized land-storage temporal subplots | 5.13 | 16 |
| Spatial comparison of GLDAS land storage and both residuals | 5.14 | 17 |
| Temporal comparison of GLDAS land storage and both residuals | 5.15 | 18 |
| Spatial residual validation: raw/detrended head correlation and year counts | 5.16 | 19 |
| Temporal residual validation: observed heads and residuals for all basins | 5.17 | 20 |
| Independent reservoir validation: spatial correlations and coverage | 5.18 | 22 |
| Residual evaluation through time: rolling head correlation and network support | 5.19 | 21 |

Additional figures retain the basin framework, input seasonality and processing-chain ranking sensitivity. The manuscript also retains controlled climate-memory ablation and paired trend uncertainty.

## Interpretation of the evaluation metrics

The climate emulator is evaluated against its naturalized parent model using raw NSE, anomaly NSE, RMSE and annual diagnostics on held-out 2016–2023 data. These scores do not independently validate an observed climate-only counterfactual.

GLDAS comparisons match soil + canopy + snow when evaluating water-depth errors. Direct GLDAS–residual comparisons use common-month standardization and timing correlations because the variables represent different compartments. They are explicitly not human-only validation.

Residual validation uses observed groundwater-head correlations, detrended correlations, annual pair counts, station-network uncertainty and independent reservoir-component evidence. Without aquifer storage coefficients, head measurements cannot supply water-equivalent RMSE or NSE for groundwater mass. Missing validation is hatched on maps and marked as insufficient support in temporal panels.

## Reproduction

The complete `research_v5/run.py --mode full` command now includes the figure revision. After an already completed scientific run, regenerate only this atlas and verify all reference tables with:

```sh
python research_v5/run.py --mode figures --work-dir PATH_TO_EXISTING_WORK
```

`scripts/37_spatiotemporal_figure_revision.py` recomputes eight plot tables and 18 new figures. It checks matched GLDAS metrics against the base analysis and annual well correlations against the extended validation table. No models are refitted to test years or validation observations. Display geometry is simplified for rendering only; all numerical aggregation retains the original intersection weights.
