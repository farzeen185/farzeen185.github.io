# Historical Thai groundwater observations from GROW

Source: [GROW Zenodo record 15149480](https://zenodo.org/records/15149480). Original Thai observations are attributed to Thailand's Ministry of Natural Resources and Environment through IGRAC. The complete compressed Parquet member of the public Zenodo ZIP was downloaded by HTTP byte ranges and inflated locally; Thailand was selected using the 511 authoritative GROW_ID values in the country metadata.

`GROW_Thailand_observations.csv` contains 5,484 observed aggregates for 511 wells: 5,259 annual observations for 506 wells from 2004–2024, and 225 monthly observations for 5 wells from March 2018–June 2023. Six rows with missing observed depth were removed from the 5,490-row Thai source subset. No gap-filled groundwater columns are used. There are no duplicate well/date observations.

- `GROW_Thailand_timeseries_raw.csv`: the original Thai source rows and all original columns.
- `GROW_Thailand_attributes.csv`: well metadata, source descriptions, interval and quality flags.
- `GROW_Thailand_annual_observations.csv` and `GROW_Thailand_monthly_observations.csv`: normalized observations split by original aggregation interval.
- `GROW_Thailand_observed_coverage.csv` and `observed_coverage_summary.csv`: actual observed coverage.
- `provenance.json`: source, licenses, processing details and limitations.

`depth_to_water_m` is depth below ground surface in meters, positive downward. `groundwater_head_anomaly_m` is negative depth centered on each well's full observed-period mean, so positive anomalies indicate rising head. This is not a GRACE baseline and should be recentered over the joint comparison period. `groundwater_level_m_asl` uses the provider's ground elevation, not a global DEM. Groundwater depth units are meters; the GROW mm/year convention applies to climate flux columns, not groundwater levels.

For validation, match annual observations to annual storage/residual means, monthly observations to monthly means, and compare common dates. Retain counts of wells and observations per basin. The data include 61 annual records flagged by GROW as outliers/change points and 26 records with nonzero plateau flags; carry these flags into sensitivity analyses. Negative depths can indicate artesian heads and require inspection rather than automatic removal. Water-level fluctuations are not storage changes without defensible aquifer storage coefficients, and correlation alone cannot establish human causation.

The Thai source metadata reports CC BY 4.0. The GROW package description and Readme explicitly state CC BY-NC-SA 4.0; retain this package notice and attribution when redistributing the extracted package-derived tables. Cite Bäthge et al., “A Global-Scale Time Series Dataset for Groundwater Studies within the Earth System” using the source record's citation.

`acquire_grow_thailand.py` supports resumable source acquisition. `normalize_observations.py` rebuilds normalized files from the extracted Thai raw table. The 1.734 GB global Parquet and compressed range-part cache are acquisition intermediates, not inputs required by the basin validation pipeline.
