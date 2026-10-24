# Objective 2: Climate-driven water-storage reconstruction and assessment of human-associated changes across Thailand

## Aim and research questions

Estimate climate-driven TWSA and GWSA for each of Thailand's 22 principal basins, evaluate the reconstruction against hydrological simulations and observations, and assess how much of the observed change is consistent with human water management. The national aggregate supplies context; it is not a twenty-third independent basin.

The analysis asks: (1) how well climate predictors reproduce storage variability beyond the seasonal cycle; (2) how observed storage differs from a documented naturalized hydrological baseline; and (3) whether residual timing and spatial patterns agree with groundwater heads and independently specified human-impact simulations.

## What changes from the earlier analysis

The earlier model was fitted to GRACE-derived observed storage. Human effects can therefore enter both the training target and state predictors, so its residual is not a clean anthropogenic component. The revised primary baseline uses **WaterGAP 2.2e naturalized simulations**, with water use switched off and artificial reservoirs removed. A paired historical-human simulation driven by the same climate forcing provides a controlled model experiment. The earlier GRACE-trained M0–M4 models remain a separate empirical comparison.

WaterGAP's naturalized experiment and model limitations are documented by [Müller Schmied et al. (2024)](https://doi.org/10.5194/gmd-17-8817-2024). Public [naturalized GSWP3–ERA5 output](https://doi.org/10.25716/GUDE.1TWP-GNQP) and [historical-human output](https://doi.org/10.25716/GUDE.14B4-KQ6R) supply matched forcing and model versions. Source metadata and actual coverage must be verified before an analysis period is assigned.

## 1. Common observations, units and spatial support

Use the existing Objective 1 TWSA and full-compartment GWSA:

\[
GWSA_{obs}=TWSA_{obs}-SMSA-SWSA-CWSA-SWEA.
\]

All compartments use mm water equivalent and the documented 2004–2009 anomaly reference. GWSA compartments are averaged on identical valid cells and months; `TWSA_GWS_reference` supplies the corresponding TWSA footprint. Missing GRACE observations remain missing. GWSA observations end September 2023 because the modeled surface-water correction ends then.

Use fractional basin-intersection area weights. Preserve native WaterGAP resolution and distinguish grid sampling from effective GRACE resolution. Align parent-cell values to the existing grid only when cell edges actually match; replication supplies no new spatial information. Compare climate and observation components on common valid support, and report coverage and alternative soil-compartment sensitivity. Do not interpret adjacent small basins as independent GRACE observations.

Rebase each naturalized and human simulation to the same reference period and spatial support. In an anomaly study, the paired difference quantifies **changes in modeled human influence relative to the reference**, rather than historical absolute depletion before GRACE.

## 2. Documented naturalized climate baseline

For storage variable \(S\), the naturalized simulation supplies \(S_{nat}\). This is a physically generated counterfactual conditional on WaterGAP's meteorology, parameterization, land cover and routing assumptions. It is not observed natural storage and does not automatically account for every indirect human influence.

Primary climate and residual components are:

\[
C_S(t)=S_{nat}(t),\qquad R_S(t)=S_{obs}(t)-C_S(t).
\]

Where the paired historical-human simulation is available:

\[
H_{WG}(t)=S_{human}(t)-S_{nat}(t),\qquad
E_S(t)=S_{obs}(t)-S_{human}(t).
\]

Thus \(R_S=H_{WG}+E_S\) on matching support. This decomposition distinguishes **modeled direct human effects** from observation–model discrepancy. The discrepancy includes structural, forcing, compartment and observation error; it cannot be assigned entirely to human activity.

Do not fill the end of a hydrological simulation with invented values. Any climate-emulator extension must be identified as extrapolation and evaluated separately.

## 3. Develop and test climate-storage emulators

Develop interpretable dynamic regression and regularized nonlinear emulators of the **naturalized** storage target. Primary predictors are meteorological precipitation, potential evapotranspiration, seasonal harmonics and antecedent climate-memory terms. Use lagged climate values and exponential memory states to represent delayed drainage and groundwater response. No observed groundwater heads, GRACE storage lags or unrestricted calendar-year trend enters the primary predictor set.

Compare seasonal climatology, physical memory regression, regularized linear regression, additive splines and Random Forest. Tune transformations, regularization, memory constants and model complexity in chronological training folds. Select models on later validation data, then freeze them before the final test period. Report raw monthly and shared-reference deseasonalized performance, baseline-relative skill, bias, RMSE, r, coverage and trend fidelity. A high monthly r alone does not qualify a model.

Retain the original M0–M4 experiments using CHIRPS, alternative GLEAM/MODIS ET, ESA CCI SSM/RZSM and MODIS LST as an **empirical sensitivity track**. Actual ET, soil moisture and LST can respond to irrigation and land management; do not label their fitted response purely climatic. Report their contribution to prediction separately from the primary counterfactual.

If an emulator fails to improve on climatology and reproduce deseasonalized natural-storage variability, classify it as unsuitable for attribution. Keep the published physical simulation as the documented baseline rather than disguising a weak emulator as a successful climate model.

## 4. Three distinct validation layers

**Emulator verification:** held-out naturalized model output tests whether the statistical emulator reproduces its parent hydrological model. This is model emulation, not independent validation of reality.

**Hydrological benchmarking:** GLDAS Noah benchmarks matching land compartments—soil, canopy and snow—not full TWS or groundwater truth. Compare WaterGAP land storage with Noah land storage using a common baseline and footprint. [NASA documentation](https://ldas.gsfc.nasa.gov/gldas/dataset) distinguishes open-loop GLDAS 2.0/2.1 from GRACE-assimilating GLDAS 2.2. A product that assimilates GRACE must not be presented as independent validation against GRACE. Noah itself has no groundwater storage compartment.

**Observation validation:** compare historical-human TWSA/GWSA and climate residuals with actual GRACE-derived observations and sign-corrected groundwater heads at their real sampling frequency. A successful simulation–observation comparison supports consistency, not proof that all residual storage is anthropogenic.

## 5. Groundwater and human-impact evidence

Use the 5,484 genuine GROW aggregates from 511 Thai wells; keep 506 annual and five monthly records distinct. Convert positive depth below ground to signed head by negation. Collapse co-located wells to coordinate-station groups before basin averaging. Retain provider flags in the primary record and report flagged-exclusion and fixed-eligibility sensitivities. The fixed-eligibility panel is not guaranteed to contain the same stations in every year.

Match full annual head aggregates to storage years with adequate observed-month coverage, excluding incomplete endpoint years. Use well-specific anomaly and trend-direction comparisons, basin indices, paired correlations and uncertainty. Report insufficient support rather than inventing an annual-to-monthly interpolation. Missing aquifer metadata prevent aquifer-resolved validation; missing specific yield/storativity prevent direct head-to-storage conversion.

Assess both observed-storage agreement and residual agreement. Separately compare residuals with the paired modeled-human component and, where available, modeled abstraction histories. These model-derived pressure series are not measured pumping. FAO GMIA remains a static spatial sensitivity and cannot validate temporal abstraction changes.

## 6. Uncertainty and strength of evidence

Keep the following uncertainties separate: GRACE/component uncertainty and filtering mismatch; climatic forcing and hydrological structure; emulator approximation and held-out error; and groundwater sampling/aquifer mismatch. Emulator spread alone is not total counterfactual uncertainty.

Estimate component Sen slopes on identical observed monthly dates and actual elapsed years. Use seasonal/annual tests, calendar-year block-bootstrap intervals and basin-wise FDR as documented in Objective 1. Preserve the limitations of serial dependence, shared GRACE spatial support and short groundwater series.

Classify basin evidence using stated criteria: (a) adequate data coverage; (b) credible climate-emulator or physical-baseline support; (c) stable residual direction across soil-product and model sensitivities; (d) temporally adequate groundwater agreement; and (e) consistency with the paired human-impact simulation. An unsupported criterion remains visible. No classification should force every basin to show human depletion.

## 7. Deliverables

Produce the naturalized and historical-human baseline series, the paired modeled-human effect, observed residual and discrepancy, chronological model-validation tables, all-basin component trend maps, groundwater comparisons and uncertainty/coverage tables. Update the interactive dashboard and presentation only after the revised results pass data-identity and validation checks.

The defensible reporting language is: **“climate-driven storage conditional on a naturalized hydrological model; observed residual changes and their consistency with modeled human effects and groundwater observations.”** Replace it with a stronger causal claim only if the independent evidence supports that claim.
