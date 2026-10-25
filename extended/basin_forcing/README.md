# Basin performance tables and forcing atlas

The report now has 83 pages, 31 figures and 17 native tables. The simple 60-page main report is followed by Appendix C (11 all-basin tables) and Appendix D (10 forcing/context figures).

- Appendix C table guide: physical PDF page 61; tables C.1–C.11: pages 62–72.
- Appendix D guide: page 73; figures D.1–D.10: pages 74–83.
- Every new table and every temporal atlas includes all 22 basins. An unavailable score is not zero. Raw CSVs retain full precision and basin names.
- Climate ensemble: 2016–2023 held-out verification against naturalized WaterGAP. GLDAS: matching soil/canopy/snow only. Wells and reservoirs: consistency evidence, not human-only ground truth.
- Forcing maps and histories: 2003–2023, available observations, original gaps retained. Native P/PET are climate predictors; CHIRPS is alternative precipitation. GLEAM/MODIS actual ET, ESA CCI moisture and MODIS LST are supporting context, not newly fitted predictors.
- Precipitation/ET: mm/month; moisture: m³/m³; temperature: °C. Monthly means are not annual totals. Map trends are OLS with month effects, variable units/year, not significance tests.

Reproduce the numerical extension after the complete study run:

    python research_v5/run.py --mode appendix --work-dir PATH_TO_COMPLETED_WORK

The full mode also includes this extension automatically. Script 45 reads recomputed outputs, never the saved reference tables; validation compares all 13 new tables with the released reference outputs. For the report, set TWSA_RESEARCH_ROOT to that work directory and run document_source/46_append_basin_forcing_report.py using a Python environment with python-docx and Pillow. Then export using the supplied Word rendering script. The generator rebuilds the simple report first, so repeated runs do not append duplicate pages.
