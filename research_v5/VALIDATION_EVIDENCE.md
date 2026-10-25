# What can validate total minus climate?

Let O be observed TWSA or GWSA, C the naturalized climate-driven simulation, A the paired historical-human simulation, R = O − C, H = A − C and E = O − A. The identity R = H + E prevents equating the entire residual with measured human depletion. E can contain unrepresented management as well as observation, forcing and model error.

| Evidence | Appropriate comparison | Principal limit |
|---|---|---|
| Reservoir storage and releases | TWS residual, modeled surface-water contribution, timing of operation or impoundment | Storage responds to rainfall and management; requires a naturalized counterfactual to isolate operation |
| Metered pumping / abstraction and consumptive use | Groundwater residual changes and modeled human perturbation | Gross pumping is a flux, not storage; recharge and return flow must be included |
| Irrigation area / groundwater dependence | Spatial pressure consistency and dry-season response | Static pressure maps do not validate temporal mass change |
| InSAR or GNSS subsidence | Aquifer-specific depletion timing and location | Deformation is not equivalent water thickness; needs compressibility and screened aquifer information |
| Well heads with verified storage coefficients | Aquifer-specific GWS anomaly or change | Confined and unconfined conversion differs; sparse wells may not represent the basin |
| Precipitation, ET and streamflow water budget | Observed storage-change closure and unrepresented fluxes | Closure can identify mismatch but does not uniquely assign it to humans |
| A second independent naturalized hydrological model | Structural robustness of climate-only storage and the residual | Model agreement is not observational proof of the unobserved counterfactual |

The completed extension now includes MSEA-Res v2 reservoir data, derived independently from Landsat surface area and hypsometry. Twenty-seven reservoir outlet coordinates intersect Thai basin polygons; 26 commissioned before 2004 form a fixed panel. A month is retained only when every panel reservoir is represented. Level 1 retains scene gaps; Level 2 is the provider spline-interpolated and smoothed product. There is no new gap filling and missing reservoirs are not treated as zero storage.

At national scale the TWS residual has raw correlation 0.521 over 73 scene-supported months. Removing calendar-month effects and linear trend on matched months gives 0.439, with a conditional calendar-year-cluster interval of 0.188–0.665. The interpolated comparison gives 0.381 over 228 months, interval 0.144–0.552. These are surface-water consistency results. They are not independent measurements of total human storage or pumping. A positive reservoir–GWS residual association is also reported, but cannot directly validate groundwater and may expose shared climate or imperfect compartment subtraction.

Groundwater panels remain a separate evidence stream. Their strict common-period, balanced comparison gives approximately zero national GWS-residual correlation. The study reports that limiting result rather than substituting the strongest raw panel correlation. No aquifer storage coefficient or pumping history is fabricated.

GLDAS is used for matched land-storage comparisons, not as complete TWS truth. The national naturalized WaterGAP soil + canopy + snow comparison against GLDAS Noah has r=0.969 and NSE=0.738 over 261 months in the retained base analysis. Groundwater and surface water are absent from that matched benchmark. Shared meteorology and its role in GWS subtraction prevent calling it independent anthropogenic validation.

Sources: Mahto et al. (2025), [MSEA-Res paper](https://doi.org/10.5194/essd-17-2693-2025), [dataset](https://doi.org/10.5281/zenodo.14844580); Huang et al. (2015), [GRACE and hydrological-model human attribution](https://doi.org/10.1002/2015WR016923); Abhishek et al. (2022), [Upper Chao Phraya water-budget closure](https://doi.org/10.3390/rs14010173). No claim of an observed basin-wide human-storage ground truth is made.
