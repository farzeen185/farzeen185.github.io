# Thailand water-storage research: completed three-objective release

All 22 principal basins plus Thailand national aggregate; 46 climate ensembles and 1,380 candidate model configurations.

## Results
- National TWSA: seasonal Sen -7.46 mm/year, block-bootstrap 95% interval -9.60 to -5.69; 235 observed months.
- National GWSA: seasonal Sen -6.82 mm/year, block-bootstrap 95% interval -8.64 to -5.13; 223 observed months.
- National TWSA test: NSE 0.626, r 0.936, RMSE 75.20 mm, deseasonalized NSE -1.106; n=57.
- National GWSA test: NSE -0.401, r 0.800, RMSE 76.09 mm, deseasonalized NSE -2.483; n=45.

## Groundwater evidence
Actual 5,484 observation aggregates from 511 Thai wells: 506 annual and five monthly. All assigned to a principal basin. Most annual values represent only two original readings. Aquifer storage coefficients and aquifer identities are unavailable.
- TWSA observed_storage: annual n=18, r=0.2230376487687072 (exploratory; no causal attribution).
- TWSA unexplained_residual: annual n=17, r=0.3183436124730047 (exploratory; no causal attribution).
- GWSA observed_storage: annual n=17, r=0.0849979421889344 (exploratory; no causal attribution).
- GWSA unexplained_residual: annual n=16, r=0.1374969623582344 (exploratory; no causal attribution).

Observation-network composition changes affect agreement; fixed-panel and source-flag sensitivities are reported alongside primary results. Post-2015 GWS has fewer than six paired annual years, so correlation is not reported.

## Interpretation and limits
Negative storage trends are observed signals. Climate reconstruction primarily captures seasonality. Residuals include candidate human influence and unresolved errors, and are not established anthropogenic pumping volumes. GLDAS Noah has no groundwater compartment. G3P is a related benchmark, not independent groundwater validation. Modelled surface water ends September 2023; missing GRACE dates remain missing. Compartment filtering differences and coarse GRACE resolution constrain spatial interpretation. Seasonal MK p-values remain subject to serial dependence; bootstrap slope intervals and FDR q-values do not remove that limitation.

## Deliverables
- Objective 1: `Thailand_Objective1/analysis_v3/` (NetCDF, trends, time series, figures).
- Objective 2: `Thailand_Objective2/analysis_v3/` (models, validation, residuals, real-well checks).
- Objective 3: `Thailand_Objective3/web_app/`; https://pratikkhanal16.github.io/thailand-water-storage-dss/
- Presentation: `Thailand_Objective3/outputs/Thailand_Three_Objectives_Research.pptx`.

The earlier `outputs_advanced` analysis is retained as historical work; `analysis_v3` is the authoritative release. Large globally downloaded intermediates may be removed after verified Thai extraction, with an audit log. Original local inputs are retained.
