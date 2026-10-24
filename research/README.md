# Reproduce the Thailand water-storage research

Author: **Farzeen Khanal**, MS in Water Engineering and Management, Asian Institute of Technology. Advisor: **Dr. Natthachet Tangdamrongsub**.

This package reruns the current Objective 1 and revised Objective 2 from the retained Thai input subsets, then refreshes a local copy of the Objective 3 decision-support app. It does not require the author's `P:` drive, Earth Engine credentials, a GitHub token, or access to the original workstation. The 25 scientific input files (approximately 45 MB) are included in this repository, with SHA-256 checksums. A normal Git clone is sufficient; Git LFS is not used.

## Quick start: Windows, macOS or Linux

Install Miniconda or Miniforge and Git, then run these commands from a terminal:

```sh
git clone https://github.com/pratikkhanal16/thailand-water-storage-dss.git
cd thailand-water-storage-dss/research
conda env create -f environment.yml
conda activate thailand-water-research
python run.py --mode check
python run.py --mode smoke
python run.py --mode full
```

The Python version used for verification was **3.11.15**. The environment selects Python 3.11 and installs the exact scientific package versions in `requirements.txt`. If using an existing Python 3.11 installation, a virtual environment with `python -m pip install -r requirements.txt` is an alternative. Run the environment creation command from the `research` directory so the requirements path resolves correctly.

`check` verifies every supplied input without importing scientific packages. `smoke` exercises the actual NetCDF files, basin geometry, weights, groundwater observations and a known-slope statistical check, and rebuilds the well indices. `full` recomputes the analysis, fits all 46 basin/storage ensembles, creates figures, refreshes the dashboard and compares computed tables against the frozen research release. The full run can take several minutes or longer depending on hardware; progress is printed and logged. Allow at least 2 GB of free disk space for the environment and generated files. These scripts use a single model-fitting worker to improve repeatability.

Outputs are written to **`research/work/`**, which Git ignores. Supplied inputs and frozen references are preserved. To choose another output location:

```sh
python run.py --mode full --work-dir /path/to/new-work-folder
python run.py --mode verify --work-dir /path/to/new-work-folder
```

On Windows use a path such as `C:\water-research-output`. Avoid putting outputs in the repository root. A repeated full run overwrites generated analysis outputs in the selected work folder; changed scientific inputs cause the run to stop rather than silently proceed.

## What runs

| Step | Script | Generated evidence |
|---|---|---|
| Input and method checks | `scripts/smoke_check.py` | File schemas, GLDAS balance, 511 wells, 22 basins, known Sen slope |
| Objective 1 | `scripts/01_storage_and_trends.py` | Full-compartment GWSA; all-basin/monthly and gridded Sen slopes, Mann–Kendall tests, FDR, bootstrap intervals, maps and NetCDF |
| Groundwater preparation | `scripts/00_groundwater_indices.py` | Signed heads, coordinate-group basin assignments and flagged/fixed-panel sensitivity indices |
| Objective 2 attribution | `scripts/06_naturalized_attribution.py` | Paired naturalized/historical-human components, residuals, trends, matched-compartment GLDAS benchmarks |
| Objective 2 climate emulators | `scripts/07_climate_emulators.py` | Ridge, ElasticNet, splines and Random Forest; chronological tuning and frozen ensembles; fitted model files |
| Independent evidence | `scripts/08_attribution_evidence.py` | Raw, climate-controlled, detrended and consecutive-year head consistency checks |
| Research synthesis | `scripts/09_research_release.py` | Additive OLS trend partition, publication figures, numerical summary and scientific QA |
| Objective 3 | `scripts/export_dashboard.py` | A locally runnable dashboard refreshed with recomputed scientific results |
| Reproduction verification | `scripts/validate_reproduction.py` | Physical identities, table comparisons and dashboard support checks |

The groundwater preparation code is the unchanged observation-index section of the original `03_groundwater_and_pressure.py`, separated so the revised method does not need legacy GRACE-trained models or an unrelated irrigation calculation. `research_common.py` accepts `TWSA_RESEARCH_ROOT`; `run.py` sets it automatically. These are packaging changes, not changes to the scientific algorithms or fitted models.

## Find the outputs

```text
work/
  Thailand_Objective1/analysis_v3/
    tables/    # basin series, trend tests and coverage
    netcdf/    # full storage balance and spatial trends
    figures/
  Thailand_Objective2/analysis_v3/tables/  # reconstructed well indices only
  Thailand_Objective2/analysis_v4/
    tables/    # attribution, verification, well checks and trend partition
    netcdf/
    models/    # fitted scikit-learn models; load only trusted local files
    figures/
    logs/
  dashboard/
  reports/reproduction_qa.json
  reports/final_research_results_v4.json
  run_logs/full_receipt.json
```

The original report and manuscript are in the repository's `downloads/` directory. The run regenerates numerical results and figures; it does not reformat the Word documents or regenerate the PowerPoint. Those document-layout operations used Microsoft Office and are separate from scientific reproducibility. Earlier GRACE-trained M0–M4 sensitivity experiments are retained as source snapshots in `../research_source/`; they are not the current climate baseline and are not part of this runner.

## Open the decision-support system locally

After a full run, from `research/`:

```sh
python -m http.server 8000 --directory work/dashboard
```

Open **http://localhost:8000**. Press Ctrl+C to stop. Alternatively, serve the repository root to inspect the already published application without rerunning models. The locally rebuilt dashboard refreshes storage series, trends, model scores and residual/head evidence; cartographic metadata and static irrigation context come from the published app. Final documents are copied as reference downloads. No publication, push or remote account operation occurs when the professor runs the pipeline.

## Verification and expected results

`reference/` contains the published scientific tables and numerical summary, used **only for comparison**. Analysis scripts never read reference tables as inputs. At the end of a full run, the checker compares generated tables with relative and absolute numeric tolerances of `1e-5`, checks storage/residual identities and verifies 46 region/target ensembles. Platform differences in libraries can affect last digits; substantive differences fail loudly and remain in the logs.

Expected national values include:

| Quantity | TWSA | GWSA |
|---|---:|---:|
| Full-record seasonal Sen slope (mm/year) | −7.4591 | −6.8234 |
| Naturalized-model emulator test NSE, 2016–2023 | 0.98088 | 0.96054 |
| Deseasonalized emulator test NSE | 0.88832 | 0.78087 |
| Annual observed-residual/head correlation | 0.14223 | 0.05432 |

Full TWSA ends September 2024. Derived GWSA ends September 2023. WaterGAP ends December 2023; no 2024 counterfactual is fabricated. Missing GRACE months remain missing. High emulator skill verifies reproduction of a hydrological model, **not** independent validation of real-world human depletion.

The equations are `GWSA = TWSA − soil − surface water − canopy − snow` and `O − C = (A − C) + (O − A)`, where O is observed storage, C is naturalized model storage and A is the paired historical-human model. Well heads check groundwater consistency; they cannot validate all human TWSA. Specific yield/storage coefficients are unavailable, so heads are not converted into water volumes. The weak head agreement and substantial observation/model discrepancy are retained as results.

## Data provenance and limitations

See [DATA_SOURCES.md](DATA_SOURCES.md), the source-specific notices beside the inputs and [LICENSES.md](LICENSES.md). The package starts from the supplied GRACE export, GLDAS regional conversion and authoritative basin weights. It does not claim to reproduce the upstream satellite retrieval, recover absent GRACE processing-centre/release metadata, or rerun WaterGAP globally. Historical acquisition helpers are included for provenance; they are not needed for the bundled-data run and can download large global intermediates if run manually.

The original GRACE metadata and filter compatibility need confirmation before journal submission. Small basins share coarse GRACE information. Reproducing the tables does not establish a causal human-depletion hypothesis.
