# Thailand Water Storage Observatory

Author: **Farzeen Khan**, MS Water Engineering and Management, Asian Institute of Technology. Advisor: Dr. Natthachet Tangdamrongsub.

**Website:** https://pratikkhanal16.github.io/thailand-water-storage-dss/

The current release provides a 50-page report, separate manuscript, 32-slide academic Beamer/PowerPoint deck, 29 readable chart files, full basin tables and portable analysis. Download the final documents from [`publication/downloads`](publication/downloads). Superseded public documents and galleries were archived locally before removal; scientific input packages are retained.

## Run the science

- [`research_v6/README.md`](research_v6/README.md): frozen-input ENSO/IOD extension, 11 new figures and six exact reference-table comparisons.
- [`research_v5/README.md`](research_v5/README.md): complete CSR storage, climate, groundwater, reservoir and forcing analysis, including the original source-input workflow.
- [`research/README.md`](research/README.md): original naturalized/historical hydrological analysis.

The primary national records show storage decline. The naturalized model and its weather emulator are separate quantities. GLDAS is a matched land-component benchmark. The residual R=O−C=H+E contains represented human effects and unresolved discrepancy; it is not observed pumping. ENSO diagnostics and monitoring-network sensitivity qualify attribution.

Serve this static website with `python -m http.server 8000` and open http://localhost:8000 . Local ECharts and Leaflet assets allow charts and basin maps without external map tiles. The page needs HTTP serving to load its JSON, rather than opening index.html as a file.
