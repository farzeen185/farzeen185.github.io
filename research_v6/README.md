# Reproduce the Thailand publication extension

Author: Farzeen Khan, Water Engineering and Management, Asian Institute of Technology.

This folder rebuilds the new ENSO/IOD diagnostics and 11 original publication figures from frozen, verified derived hydrological inputs. It does not claim to independently rebuild WaterGAP or to observe a human-only counterfactual. The original and extended scientific packages remain in `research/` and `research_v5/` for the complete source-input analysis.

## Quick independent run

Use Python 3.11. From the repository root:

```sh
python -m venv .venv
# Windows: .venv/Scripts/activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -r research_v6/requirements-lock.txt
python research_v6/run.py --mode check
python research_v6/run.py --mode full --work-dir output/publication_reproduction
```

No credentials or new downloads are needed. Input SHA-256 checks run first. The full command recreates the new tables and figures and compares six tables with the released references, including all 2,070 index/lag/region associations. Success is recorded in `output/publication_reproduction/run_logs_v6/receipt.json`. Missing data stay missing. Numerical tolerances allow floating-point platform differences.

## Complete source-input hydrological rebuild

```sh
python research_v5/run.py --mode full --work-dir output/complete_reproduction
python research_v6/run.py --mode full --work-dir output/complete_reproduction
```

The first command rebuilds the base and extended CSR analyses, climate evaluation, groundwater and reservoir evidence, spatial/temporal figures and basin forcing summaries. The second verifies that overlapping derived inputs match the released extension before adding ENSO. If recomputed input hashes differ only because of CSV serialization/platform precision, run the extension in a separate work directory and compare its six reference tables, then inspect the complete-work reference verification. No mismatched file is silently replaced.

## Methods and limitations

Analysis window: 2003–2023. ENSO leads: 0, 3, 6, 9 and 12 months. Nuisance regressions use calendar months, trend and contemporaneous DMI. All 20 nonzero whole-year circular shifts are retained; minimum rotation p is 1/21, so this is a low-power sensitivity diagnostic. FDR spans all 22 basins, both indices and the complete lag/series family; national tests are separate. ONI episodes use five consecutive overlapping seasons at ±0.5 C with the public table's 0.1 C precision. RONI v5 is explicitly frozen; current operational RONI uses v6. Download URLs and hashes are in the frozen index manifest.

The residual is R=O−C=H+E. Groundwater head is not converted to storage without aquifer properties. GLDAS comparisons match soil, canopy and snow. Annual MAD ratios are not complementary causal percentages. No basin ENSO result passed the full conservative FDR screen.

## Documents and presentation source

The final downloads are in `publication/downloads/`. The figures/tables ZIP contains vector originals, numerical tables and source provenance. Editorial generation scripts are supplied in that ZIP; Word PDF rendering and the editable PowerPoint authoring runtime are environment-specific, while the numerical Python workflow above is portable. The Beamer ZIP includes a standalone `.tex` file, all required vector figures and compilation instructions (`xelatex` twice).
