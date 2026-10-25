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

Source-global CSR files are deliberately excluded; regional subsets, units, original attributes and the special-month audit are retained. The added climate cube and COST-G/G3P TWS record enable independent-forcing and source tests. MSEA-Res Level 1 contains screened scene estimates with gaps; Level 2 is provider-interpolated and smoothed. The fixed reservoir population is never replaced by a changing monthly sum. A reservoir comparison checks part of TWS, not total anthropogenic storage or groundwater mass.

All source-specific terms in `../research` apply. Additional inputs: CSR dataset DOI 10.15781/cgq9-nh24; G3P DOI 10.5880/G3P.2024.001; MSEA-Res DOI 10.5281/zenodo.14844580 and paper DOI 10.5194/essd-17-2693-2025 (CC BY 4.0). GROW groundwater terms include noncommercial/share-alike conditions. Input access does not imply that the author relicenses source data.

Scientific output is written under `WORK/Thailand_Research_v5`. The published thesis, manuscript and slides are under `../extended/`; Word pagination requires Microsoft Word and is separate from numerical reproduction. The supplied Beamer source compiles with XeLaTeX and Times New Roman. Negative residuals are not automatically pumping: R = observed − naturalized = modeled human perturbation + observation–historical-model discrepancy. Conditional bootstrap intervals are not total product uncertainty; all 22 basin estimates retain CSR small-support caution.
