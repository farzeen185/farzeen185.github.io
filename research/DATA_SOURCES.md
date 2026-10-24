# Included inputs and provenance

All required numerical inputs are enumerated in `input_manifest.json`, including file sizes and SHA-256 checksums. The run uses the supplied Thai subsets directly; normal execution makes no data-provider requests.

| Inputs | Origin and interpretation |
|---|---|
| `Thailand_Objective2/data/GRACE_TWSA_Monthly_2002_2024.nc` | Project-supplied GRACE/GRACE-FO TWSA export, cm converted to mm. The file identifies CRS and grid spacing but not processing centre/release or complete filtering. Preserved exactly; no missing provenance is invented. |
| `Thailand_Objective2/data/BASINS/` | Project-supplied ONWR principal-basin shapefile and sidecars. Island features are grouped with parent basins for groundwater and revised attribution maps. |
| `Thailand_Objective1/outputs/tables/*Fractional_Weights.csv` | Retained authoritative polygon/grid intersection areas. Rows refer to the descending 62-latitude by 36-longitude GRACE grid. Included as upstream spatial inputs, not regenerated from simplified web geometry. |
| `shared_data/GLDAS/*.nc` | Compact monthly Thai GLDAS Noah soil layers, canopy, snow and their sum. Original conversion provenance and component-sum QA are retained beside the file. |
| `shared_data/surface_water/*.nc` | Thai-buffer SWS, RZSM and GWSA subsets from G3P v1.12. [Dataset DOI](https://doi.org/10.5880/G3P.2024.001). G3P groundwater is a related sensitivity product, not an independent well observation. Per-component provenance retains original archive members and filters. |
| `shared_data/WaterGAP/*.nc` | Ten monthly Thai-buffer WaterGAP 2.2e GSWP3–ERA5 variable/scenario subsets for 1981–2023. [Naturalized DOI](https://doi.org/10.25716/GUDE.1TWP-GNQP); [historical-human DOI](https://doi.org/10.25716/GUDE.14B4-KQ6R); [model paper](https://doi.org/10.5194/gmd-17-8817-2024). Source 360-day monthly identities are mapped to month starts without interpolation. |
| `shared_data/groundwater/GROW/*.csv` | 5,484 actual annual/monthly aggregates from 511 Thai wells, normalized from the [GROW dataset](https://doi.org/10.5281/zenodo.15149480). Provider flags retained. No filled groundwater values or invented aquifer coefficients. |

Absolute `P:\twsa` paths inside historical provenance JSON identify the original acquisition location. They are documentary records only and are not used to locate files by the runnable package. Runtime paths derive from the checkout and selected work directory.

Acquisition scripts are included to document how public subsets were obtained. They are not a guarantee that providers will preserve byte ranges or record identifiers indefinitely. The checked-in subsets and their checksums are the reproducibility inputs. The supplied GRACE export and basin weights are explicitly upstream inputs because the original export configuration and full satellite-processing provenance are unavailable.
