# G3P water-storage compartments for Thailand

Public source: [GFZ G3P v1.12](https://doi.org/10.5880/G3P.2024.001), [archive](https://isdc-data.gfz.de/grace/GravIS/G3P/v1.12/), [methodology](https://gravis.gfz.de/gws).

Files named `G3P_v1.12_*_Thailand_buffer_monthly_200204_202309.nc` retain native variables and uncertainties, clipped by coordinate slice to 94–109 E, 2–24 N. Actual cell centres are 94.25–108.75 E, 2.25–23.75 N at 0.5-degree spacing. Global source files are retained unchanged. Downloader scripts and per-compartment JSON provenance are included.

* SWS: `sws` and `std`, mm equivalent water height. GloFAS version 4.0 / LISFLOOD modeled river, lake and man-made reservoir storage anomalies, 250-km Gaussian filtered. Not reservoir observations. 225 monthly epochs between April 2002 and September 2023, with missing GRACE periods retained as gaps. `std` is the absolute deviation of LISFLOOD from the LISFLOOD/WaterGAP ensemble mean, with late-period uncertainty climatology; it is not an observational standard error.
* RZSM: `rzsm` and `std`, mm equivalent water height, four soil layers summed and 250-km Gaussian filtered. 258 consecutive calendar months April 2002–September 2023. Metadata states anomaly mean April 2002–September 2023.
* GWSA: `gwsa` and `uncertainty`, mm equivalent water height, 225 epochs. Native GFZ benchmark derived as COST-G TWS minus filtered root-zone soil moisture, surface water, snow and glaciers. No separate canopy term is specified. Metadata states anomaly baseline April 2002–December 2020.
* TWS: native COST-G GRACE/GRACE-FO anomaly and uncertainty benchmark. Native details are retained in its NetCDF and JSON provenance.

Match products by calendar month, not array position. Rebase all components onto one shared baseline and valid-month mask before subtraction. Do not extrapolate September 2023 surface water values into later months. Combining the filtered SWS with another GRACE solution or unfiltered GLDAS compartments incurs spatial-response mismatch, especially in small basins. G3P does not provide independent validation of an analysis using the same GRACE observations.

The 0.5-degree grid does not imply independent 0.5-degree spatial resolving power: the 250-km spatial filter strongly limits interpretation for Thailand's smallest basins.
