# Focused TWSA climate, GLDAS and RMSE plots

Climate baseline means naturalized WaterGAP TWSA. Climate emulator means the weather-based reconstruction of that parent target. GLDAS land storage means soil + canopy + snow; it excludes groundwater and surface water.

## Figure 1 Spatial storage trends

2003–2023 common available months within each basin; calendar-month fixed-effect OLS. These differ from full-record seasonal Sen slopes. GLDAS land storage excludes groundwater and surface water. Each panel has its own scale; the three storage definitions are not interchangeable.

## Figure 2 National temporal comparison

Separate panels retain different storage definitions. Top: observed and naturalized total storage. Bottom: matching land compartments. Gaps are retained; no direct full-TWS error is assigned to partial GLDAS land storage.

## Figure 3 TWSA climate reconstruction for all 22 basins

Naturalized parent-model target and frozen meteorological ensemble reconstruction. Green shading identifies the held-out 2016–2023 period; earlier values are training or validation context. The emulator targets a hydrological model, not independently observed storage.

## Figure 4 Matched GLDAS time series for all 22 basins

Matched soil + canopy + snow anomalies in mm. GLDAS and WaterGAP share climatic influences. Agreement evaluates land-component consistency; it cannot validate groundwater or the entire human residual.

## Figure 5 Spatial RMSE by evaluation target

Pooled 2016–2023 metrics. Climate reconstruction targets naturalized TWSA; the climate baseline is separately compared with observed GRACE TWSA; land storage is compared with matching GLDAS compartments. Pair counts differ because GRACE has gaps. Compare basins within the same panel, rather than ranking models across different targets.

## Figure 6 Annual RMSE through time

Years 2016–2023; at least eight paired months are required per annual score. GRACE mission-gap years may have no score. Shading describes variation among basins, not a confidence interval. Each panel has its own vertical scale and evaluation target.

## Figure 7 Annual RMSE for all 22 basins

All three explicitly labelled evaluation targets are retained. Different targets and compartment variances prevent interpreting a smaller cross-target RMSE as a better climate model. Missing annual scores remain gaps.

RMSE maps and annual plots use 2016–2023; annual scores require eight observed pairs. Spatial storage trends use 2003–2023 common available months and month-effect OLS, not the main report seasonal Sen estimates. Full-precision CSV values, sample counts and basin names are included. Rebuild after the complete scientific run by setting TWSA_RESEARCH_ROOT and running script 54. Install the additional PDF dependency with: python -m pip install pypdf==6.21.2 . All other numerical dependencies are in the main research lock file. Scientific models are not refitted.
