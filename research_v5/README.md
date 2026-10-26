> Current report, manuscript and slides: [`../publication/downloads/`](../publication/downloads/). This folder retains the scientific workflow; older public documents were consolidated in the current release.

# Extended CSR storage and attribution study

Author: Farzeen Khan, MS Water Engineering and Management, AIT. Advisor: Dr. Natthachet Tangdamrongsub.

This is a separate extension of the original reproducible study in `../research`. It identifies CSR RL06.3 as the primary gravity source and adds common-support product comparisons, shared native-mascon diagnostics, climate-memory ablations, frozen-forcing stress tests, paired attribution uncertainty, balanced well panels, and an independent reservoir-component check. The methods are established; novelty is the integrated attribution-credibility assessment and its Thai basin evidence.

From the repository root, using Python 3.11:

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -r research_v5/requirements-lock.txt
python research_v5/run.py --mode check
python research_v5/run.py --mode full --work-dir research_v5/work
```

The full command first rebuilds and verifies the original study, then recomputes the extension. All compact inputs are supplied with SHA-256 manifests; no Earthdata login or download is needed. Reference CSVs are used only for regression comparison, not as scientific inputs. To extend a **successfully reproduced** existing work directory, use `--reuse-base --work-dir PATH`. To repeat checks only, use `--mode verify --work-dir PATH`.

The requested figure revision adds 18 spatial/temporal figure sets and eight independently recomputed plot tables. The full command includes this step. To regenerate the atlas after an already completed run, use `python research_v5/run.py --mode figures --work-dir PATH`. It verifies all 24 original extended reference tables plus eight figure-revision tables. The reports contain 21 and 22 figures respectively; see the [figure crosswalk](../extended/FIGURE_REQUIREMENTS.md). Display geometry is simplified only for rendering; numerical basin aggregation retains the original intersection weights.

The complete revised pipeline passed all **32 table comparisons** in [Linux run 40171034365](https://github.com/pratikkhanal16/thailand-water-storage-dss/actions/runs/40171034365). The Windows figure-only reproduction passed the same original-plus-figure comparisons. Updated receipts are in `verification/`.

Source-global CSR files are deliberately excluded; regional subsets, units, original attributes and the special-month audit are retained. The added climate cube and COST-G/G3P TWS record enable independent-forcing and source tests. MSEA-Res Level 1 contains screened scene estimates with gaps; Level 2 is provider-interpolated and smoothed. The fixed reservoir population is never replaced by a changing monthly sum. A reservoir comparison checks part of TWS, not total anthropogenic storage or groundwater mass.

The complete original-plus-extension pipeline passed on Linux in [GitHub Actions run 40166730919](https://github.com/pratikkhanal16/thailand-water-storage-dss/actions/runs/40166730919), as well as the Windows extension run. All 24 extended tables matched the retained references. `verification/` includes the tested scientific commit, run receipts and checks. Later documentation or interface commits do not change that numerical study.

All source-specific terms in `../research` apply. Additional inputs: CSR dataset DOI 10.15781/cgq9-nh24; G3P DOI 10.5880/G3P.2024.001; MSEA-Res DOI 10.5281/zenodo.14844580 and paper DOI 10.5194/essd-17-2693-2025 (CC BY 4.0). GROW groundwater terms include noncommercial/share-alike conditions. Input access does not imply that the author relicenses source data.

Scientific output is written under `WORK/Thailand_Research_v5`. The published thesis, manuscript and slides are under `../extended/`; Word pagination requires Microsoft Word and is separate from numerical reproduction. The supplied Beamer source compiles with XeLaTeX and Times New Roman. Negative residuals are not automatically pumping: R = observed − naturalized = modeled human perturbation + observation–historical-model discrepancy. Conditional bootstrap intervals are not total product uncertainty; all 22 basin estimates retain CSR small-support caution.


The latest report adds Appendix C (11 all-basin value/performance tables) and Appendix D (10 spatial/temporal forcing figures). It now has 83 pages, 31 figures and 17 native tables. The original simple methodology is retained. After a completed scientific run, use python research_v5/run.py --mode appendix --work-dir PATH to regenerate this extension; full mode includes it too. The portable Windows extension passed all 13 new table comparisons, alongside the existing 24 scientific and eight figure-table checks. The historical Linux receipts above concern the original 32 tables. The new atlas and values are under ../extended/basin_forcing/. Native P/PET are the primary model forcing; CHIRPS tests rainfall replacement; actual ET, moisture and LST remain supporting context.
