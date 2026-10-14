# Thailand Water Storage Observatory

Interactive research decision support for Thailand's 22 principal basins and the national aggregate. Open the [live dashboard](https://pratikkhanal16.github.io/thailand-water-storage-dss/).

The release includes monthly and annual TWSA/GWSA, seasonal Sen slopes, original and seasonal Mann–Kendall tests, false-discovery-rate q-values, climate reconstructions, candidate human-related residuals, and actual Thai groundwater observation comparisons.

## Research scope

1. **Storage trends:** GRACE TWSA, April 2002–September 2024. Full-compartment GWSA, April 2002–September 2023. Missing GRACE months remain missing. GWSA = TWSA − soil moisture − surface water − canopy − snow, with components in mm water equivalent and a common 2004–2009 anomaly reference.
2. **Climate reconstruction:** Physical memory model, ElasticNet, additive splines and Random Forest in M0–M4 predictor experiments. Two-year spin-up; train 2005–2015, validation 2016–2019, independent test from 2020. Thirty model configurations per target and region; 46 ensembles across two targets and 23 regions. Preprocessing and tuning use training data. Validation selects ensemble members and weights. Test results do not select models.
3. **Decision support:** Basin maps, time-series zoom, monthly map animation, annual aggregation, storage selection, model skill, irrigation pressure, historical observation coverage, CSV downloads and explicit evidence limitations.

## Interpretation

The climate model is calibrated to observed storage, which can already contain human influences. ET and soil-moisture predictors may also contain irrigation effects. **The residual is candidate human influence plus unresolved forcing, model and observation error; it is not proven anthropogenic storage or a pumping volume.**

GLDAS Noah provides soil, canopy and snow, but **has no groundwater storage compartment**. Its land storage is a TWS reconstruction benchmark, not independent full-TWS truth. G3P GWS is a related product that shares GRACE and compartment information; it is not independent groundwater validation.

G3P surface water includes modeled rivers, lakes and reservoirs. Its native 0.5° cells are replicated into aligned 0.25° subcells without creating additional information. Its 250 km filtering may not match the local GRACE/GLDAS inputs. Reported grid spacing is not effective GRACE resolution. Small adjacent basins are not independent samples.

The observed TWSA series retains its GRACE footprint. The regional balance uses `TWSA_GWS_reference`, soil, surface-water, canopy and snow means on the identical groundwater-valid cells/months. Use that common-footprint TWSA when reproducing basin GWSA from the component CSV. Float32 component arithmetic leaves regional balance differences below 0.0001 mm. Climate and residual trend estimates use the same observed-target monthly support; internal missing GRACE months can still have model predictions for visualization.

Historical groundwater checks use **5,484 observed aggregates from 511 wells**, including 506 annual wells and five monthly wells. No interpolated observation or specific yield is invented. Annual aggregates typically contain only two source readings. Positive depth below ground is converted to signed head by negation. Co-located wells are collapsed to equal-weight station groups; source quality flags and a fixed-panel sensitivity are retained in research outputs. Aquifer metadata are missing. Correlations and trend directions compare observed patterns rather than converting head to storage. Annual validation excludes incomplete endpoint years and requires at least eight observed storage months. Short post-2015 GWS comparisons are insufficient for strong attribution.

FAO GMIA v5 is a static spatial proxy. Thailand equipped-area statistics refer to 2007; groundwater-irrigation fractions use historical crop/provincial assumptions. It does not measure current pumping or temporal abstraction changes.

Seasonal Mann–Kendall p-values do not fully account for serial dependence. Research outputs also include annual tests and calendar-year block-bootstrap slope intervals. FDR addresses multiple testing, not spatial independence. Selected-period browser tests are exploratory, with unadjusted p-values.

## Local project structure and reproducibility

The full local project is rooted at `P:\twsa`:

```text
shared_data/                        downloaded, documented source subsets
scripts/research_common.py          units, weights, statistics and metrics
scripts/01_storage_and_trends.py    Objective 1
scripts/02_climate_models.py        Objective 2 climate models
scripts/03_groundwater_and_pressure.py  real-well and irrigation checks
scripts/04_package_dss.py           aggregate dashboard export
Thailand_Objective1/analysis_v3/    NetCDF, CSV, figures and logs
Thailand_Objective2/analysis_v3/    models, NetCDF, CSV, figures and logs
Thailand_Objective3/web_app/        this static application
reports/                           verification and cleanup reports
```

Run scripts 01–04 sequentially with Python in the `thailand-sm` environment. They require the original local inputs and downloaded subsets; large source datasets are deliberately excluded from this website repository. The source paths resolve relative to the project root. For local website preview, run `python -m http.server 8765` from this directory. No API key or build step is required. Leaflet and ECharts are vendored with their licenses. Browser CSV export uses only the selected basin's published aggregate observations and reconstruction.

## Sources and licenses

- G3P v1.12: https://doi.org/10.5880/G3P.2024.001 . Full source provenance retained in the local project.
- GLDAS Noah: https://ldas.gsfc.nasa.gov/gldas . Original local input converted without altering component values.
- GROW: https://doi.org/10.5281/zenodo.15149480 . **Package CC BY-NC-SA 4.0**; Thai provider metadata states CC BY 4.0. Derived observation indices in this research release follow the package's noncommercial share-alike terms. Attribute GROW and the Thai groundwater source; consult the dataset record for authors and full license.
- FAO GMIA v5: https://www.fao.org/aquastat/en/geospatial-information/global-maps-irrigated-areas/latest-version/ . Source-specific terms apply; no universal license is claimed.
- CHIRPS, GLEAM, ESA CCI Soil Moisture and MODIS inputs retain their original source terms and provenance.
- Basin boundaries: Thailand ONWR principal-basin shapefile supplied with the project. Separate island features are attached to their parent basin.

This release is for noncommercial research and education. Third-party datasets and libraries retain their own licenses. Automated outputs are supplied with the limitations above and should be reviewed before management or publication decisions.
