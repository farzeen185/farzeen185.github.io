# Direct WaterGAP robustness revision

This revision uses naturalized WaterGAP directly. No residence-time reconstruction or emulator enters the residual. It adds gravity × soil × coastal-support sensitivity, larger reporting groups, baseline/structural comparisons, fixed groundwater panels, reservoir uncertainty/influence checks, daily CHIRPS concentration/dry-spell analysis, and a transparent evidence matrix.

Use Python 3.11 or newer in a clean environment:
```
python -m pip install -r research_v8/requirements-lock.txt
python research_v8/run.py --mode check
python research_v8/run.py --mode full --work-dir output/direct_reproduction --figures
```
The run verifies frozen input hashes, rebuilds all new numerical tables, checks them against references, and optionally regenerates vector/PNG figures. The receipt is output/direct_reproduction/run_logs_v8/receipt.json. No credentials or raw downloads are needed. Original source-input workflows remain in research/ and research_v5/; research_v6/ is the earlier ENSO extension.

Daily CHIRPS was extracted from the publisher at 0.05-degree native centres. Every 2003–2023 calendar day is retained. The incomplete NOAA mirror was rejected after time-axis audit. Inputs contain daily basin records, annual local concentration indices, exact URLs and hashes. Recomputing grid-cell concentration from raw global data requires the optional acquisition script, which is slower and separately documented.

LPJmL and MIROC remain structural diagnostics: the downloaded fields are not assumed to have groundwater accounting equivalent to WaterGAP. Only two WaterGAP forcing/experiment variants enter the full-TWS baseline evidence flags. These are not independent model truths. nowatermgt may retain historical land use and other human forcings.

Groundwater/reservoir comparisons are consistency evidence, not independent validation of a human-only residual. Fixed well panels still provide few paired years. Wild regression intervals are conditional, not complete satellite/model uncertainty. Rainfall analyses are exploratory and include multiple-test adjustment; a positive explanatory gain is not proof of causality. No Q1 acceptance claim is made.

ISIMIP exact file IDs/versions/licenses/terms are retained in the inventory. Please credit the original data providers; applicable terms encourage offering co-authorship. Acquisition does not contact authors or send messages.
