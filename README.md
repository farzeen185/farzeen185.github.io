# Thailand three objective research release

Author: Farzeen Khanal. Advisor: Dr. Natthachet Tangdamrongsub. MS in Water Engineering and Management, Asian Institute of Technology. Release: 24 October 2026.

## Run the research

The **[reproducible research package](research/README.md)** includes the analysis code, 25 required Thai input files (45 MB), pinned dependencies, a single-command runner and comparisons against the reported results. It runs independently of the author's workstation.

```sh
git clone https://github.com/pratikkhanal16/thailand-water-storage-dss.git
cd thailand-water-storage-dss/research
conda env create -f environment.yml
conda activate thailand-water-research
python run.py --mode full
```

See the [professor's run guide](research/README.md) for quick checks, output locations and local dashboard instructions. Scientific inputs and frozen reference results are preserved; recomputed outputs go into `research/work/`.

## Research results

Objective 1 is complete for 22 principal basins plus national context: TWSA/GWSA time series, seasonal Sen trends, original/seasonal Mann–Kendall tests, FDR, coverage and bootstrap uncertainty. Original national slopes: TWSA −7.46 mm/year (through September 2024); GWSA −6.82 mm/year (through September 2023).

Objective 2 now uses matched naturalized and historical-human WaterGAP22e GSWP3–ERA5 simulations, not GRACE-trained predictions relabelled natural. Climate emulators use meteorological P/PET, causal memory and seasonal harmonics. Train 1991–2009, validation 2010–2015 and untouched test 2016–2023 follow ten warm-up years. National model-emulation test NSE: TWSA 0.981, GWSA 0.961; anomaly NSE 0.888 and 0.781. These are verification against a parent model, not independent groundwater validation. GLDAS Noah benchmarks matching land compartments only (national NSE 0.738).

The exact decomposition is residual = observed − naturalized = modeled human effect + observation–historical-model discrepancy. Most national residual decline is not reproduced by the paired modeled-human effect. Raw annual residual/head correlations are TWSA 0.142 (18 years) and GWSA 0.054 (17 years); controlling naturalized climate gives 0.131 and 0.029. Validation does not confirm interpreting the entire residual as human depletion.

Groundwater heads can assess the groundwater component's consistency; they cannot directly validate human TWSA, which includes soil and surface water. Heads themselves contain climate and human effects. Storage volumes require aquifer yield/storativity, which are unavailable and have not been invented. Source-flag, fixed-eligibility, climate-controlled, detrended and consecutive-year checks are retained.

Objective 3 is the hosted decision-support app: https://pratikkhanal16.github.io/thailand-water-storage-dss/ . CSV exports distinguish full-footprint observations, common-footprint observations, naturalized storage, historical-human model, residual, modeled human effect and discrepancy.

Authoritative outputs: Objective 1 `Thailand_Objective1/analysis_v3`; revised Objective 2 `Thailand_Objective2/analysis_v4`; app `Thailand_Objective3/web_app`; report/manuscript/slides `deliverables/`. Earlier Objective 2 `analysis_v3` is an empirical sensitivity, not the current attribution baseline.

The supplied GRACE file identifies units and grid but not processing centre, product release or leakage correction. That provenance must be recovered before definitive publication. Magnitudes also depend on compartment choice and filtering. A completed research draft is not an externally approved thesis or causal pumping validation. Original inputs and downloaded Thai source subsets are retained; previous redundant intermediates were removed with an audit.

## Reproducibility and licenses

Use `research/run.py` for the portable, bundled-data workflow. The `research_source/` folder contains earlier source snapshots; use `research/` for the runnable current method. The static website itself needs only a web server, with no API key or build step. Input checksums, source-specific provenance and scientific limitations are documented in the research package.

WaterGAP outputs are CC BY 4.0; GROW observation derivatives retain CC BY-NC-SA 4.0 package terms and Thai source metadata CC BY 4.0. This is a noncommercial research release. Original G3P, NASA, FAO, CHIRPS, GLEAM, ESA CCI and ONWR source terms remain applicable; no universal license is asserted. Vendored Leaflet and ECharts retain their included licenses.
