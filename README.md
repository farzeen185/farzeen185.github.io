# Thailand Water Storage Observatory

Author: **Farzeen Khan**, MS Water Engineering and Management, Asian Institute of Technology. Advisor: Dr. Natthachet Tangdamrongsub.

**Website:** https://farzeen185.github.io/

The latest direct-method revision uses naturalized WaterGAP directly, without a residence-time reconstruction or emulator in the residual. It adds processing/support sensitivity, baseline/structural comparisons, fixed groundwater panels, reservoir uncertainty/influence checks, daily rainfall concentration and a basin evidence matrix. Read the [interactive research revision](publication/direct/index.html), [14-page manuscript draft](publication/direct/Direct_WaterGAP_Manuscript.pdf), [19-page research addendum](publication/direct/Direct_WaterGAP_Research_Addendum.pdf), and [12-figure atlas](publication/direct/Robustness_and_Process_Figures.pdf). The main figure library contains 39 direct-method figures and one retained ENSO lag diagnostic.

The earlier 50-page report and 32-slide Beamer/PowerPoint deck are retained under [`publication/downloads`](publication/downloads) as previous reconstruction-based documents. They have not been relabelled as this revision. Scientific inputs and prior source workflows are preserved.

## Run the science

- [`research_v8/README.md`](research_v8/README.md): latest direct-method robustness/process revision; 84 hashed processed inputs, 15 numerical reference-table comparisons, pinned requirements and an optional raw-data acquisition script.
- [`research_v6/README.md`](research_v6/README.md): frozen-input ENSO/IOD extension, 11 new figures and six exact reference-table comparisons.
- [`research_v5/README.md`](research_v5/README.md): complete CSR storage, climate, groundwater, reservoir and forcing analysis, including the original source-input workflow.
- [`research/README.md`](research/README.md): original naturalized/historical hydrological analysis.

The primary national records show storage decline. Negative residual slopes persist across tested processing variants in 20 of 22 basins for both TWSA and GWSA, but magnitude and independent support vary. Rainfall concentration did not improve the national observed/residual explanatory comparison. GLDAS is a matched land-component benchmark. The residual R=O−C=H+E contains represented human effects and unresolved discrepancy; it is not observed pumping. LPJmL/MIROC remain structural diagnostics rather than verified equivalent full-TWS baseline references. No Q1 acceptance claim is made.

Serve this static website with `python -m http.server 8000` and open http://localhost:8000 . Local ECharts and Leaflet assets allow charts and basin maps without external map tiles. The page needs HTTP serving to load its JSON, rather than opening index.html as a file.
