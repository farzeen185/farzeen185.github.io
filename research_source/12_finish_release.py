import json,re,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];W=ROOT/'Thailand_Objective3/web_app';O=ROOT/'Thailand_Objective2/analysis_v4'
p=W/'app.js';s=p.read_text(encoding='utf-8');start=s.index('function downloadCSV()');end=s.index('\nfunction methods',start)
new="""function downloadCSV(){const s=series();const keys=[state.storage,state.storage+'_attribution_observed',state.storage+'_climate',state.storage+'_benchmark',state.storage+'_residual',state.storage+'_modeledhuman',state.storage+'_discrepancy'];let csv='date,basin,storage,observed_full_footprint_mm,observed_common_footprint_mm,naturalized_mm,historical_human_model_mm,observed_residual_mm,modeled_human_mm,model_discrepancy_mm\\n';data.meta.dates.forEach((d,i)=>{csv+=`${d},"${region().name.replaceAll('"','""')}",${state.storage},${keys.map(k=>Number.isFinite(s[k]?.[i])?s[k][i]:'').join(',')}\\n`;});const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download=`Thailand_${state.basin}_${state.storage}.csv`;a.click();URL.revokeObjectURL(url);}
"""
s=s[:start]+new+s[end:]
s=s.replace("state.metric=state.objective===1?'trend':state.objective===2?'residual':'wells';", "state.metric=state.objective===1?'trend':state.objective===2?'residual':'wells';if(state.objective===2){const valid=(series()[state.storage+'_residual']||[]).map((v,i)=>Number.isFinite(v)?i:-1).filter(i=>i>=0);state.month=valid.at(-1)??state.month;el('monthSlider').value=state.month;}")
s=s.replace("state.metric==='observed'?state.storage:","state.metric==='observed'?(state.objective===2?state.storage+'_attribution_observed':state.storage):")
p.write_text(s,encoding='utf-8')
p=W/'index.html';s=p.read_text(encoding='utf-8').replace('<th>Test NSE</th>','<th>Emulator NSE</th>')
anchor='<p><a href="downloads/Thailand_Three_Objectives_Research.pptx">'
links='<p><a href="downloads/Research_Manuscript_Farzeen_Khanal.docx">Research manuscript</a> · <a href="downloads/AIT_Research_Report_Farzeen_Khanal.docx">AIT research report</a></p>'
s=re.sub(r'<p><a href="downloads/Research_Manuscript_Farzeen_Khanal.docx">.*?</p>', '', s)
s=s.replace(anchor,links+anchor);p.write_text(s,encoding='utf-8')
for p in (ROOT/'deliverables').glob('*'):
    if p.is_file():shutil.copy2(p,W/'downloads'/p.name)
deck=ROOT/'deliverables/Thailand_Three_Objectives_Farzeen_Khanal.pptx'
if deck.exists():shutil.copy2(deck,W/'downloads/Thailand_Three_Objectives_Research.pptx')
for p in (ROOT/'scripts').glob('*.py'):
    if p.name.startswith(('06_','07_','08_','09_','10_','11_','12_')) or p.name in ['discover_watergap.py','acquire_watergap_subsets.py']:shutil.copy2(p,W/'research_source'/p.name)
for p in (O/'logs').glob('*.json'):shutil.copy2(p,W/'provenance'/p.name)
shutil.copy2(ROOT/'shared_data/WaterGAP/publisher_inventory.json',W/'provenance/WaterGAP_publisher_inventory.json')
summary='''# Thailand three objective research release

Author: Farzeen Khanal. Advisor: Dr. Natthachet Tangdamrongsub. MS in Water Engineering and Management, Asian Institute of Technology. Release: 24 October 2026.

Objective 1 is complete for 22 principal basins plus national context: TWSA/GWSA time series, seasonal Sen trends, original/seasonal Mann–Kendall tests, FDR, coverage and bootstrap uncertainty. Original national slopes: TWSA −7.46 mm/year (through September 2024); GWSA −6.82 mm/year (through September 2023).

Objective 2 now uses matched naturalized and historical-human WaterGAP22e GSWP3–ERA5 simulations, not GRACE-trained predictions relabelled natural. Climate emulators use meteorological P/PET, causal memory and seasonal harmonics. Train 1991–2009, validation 2010–2015 and untouched test 2016–2023 follow ten warm-up years. National model-emulation test NSE: TWSA 0.981, GWSA 0.961; anomaly NSE 0.888 and 0.781. These are verification against a parent model, not independent groundwater validation. GLDAS Noah benchmarks matching land compartments only (national NSE 0.738).

The exact decomposition is residual = observed − naturalized = modeled human effect + observation–historical-model discrepancy. Most national residual decline is not reproduced by the paired modeled-human effect. Raw annual residual/head correlations are TWSA 0.142 (18 years) and GWSA 0.054 (17 years); controlling naturalized climate gives 0.131 and 0.029. Validation does not confirm interpreting the entire residual as human depletion.

Groundwater heads can assess the groundwater component's consistency; they cannot directly validate human TWSA, which includes soil and surface water. Heads themselves contain climate and human effects. Storage volumes require aquifer yield/storativity, which are unavailable and have not been invented. Source-flag, fixed-eligibility, climate-controlled, detrended and consecutive-year checks are retained.

Objective 3 is the hosted decision-support app: https://pratikkhanal16.github.io/thailand-water-storage-dss/ . CSV exports distinguish full-footprint observations, common-footprint observations, naturalized storage, historical-human model, residual, modeled human effect and discrepancy.

Authoritative outputs: Objective 1 `Thailand_Objective1/analysis_v3`; revised Objective 2 `Thailand_Objective2/analysis_v4`; app `Thailand_Objective3/web_app`; report/manuscript/slides `deliverables/`. Earlier Objective 2 `analysis_v3` is an empirical sensitivity, not the current attribution baseline.

The supplied GRACE file identifies units and grid but not processing centre, product release or leakage correction. That provenance must be recovered before definitive publication. Magnitudes also depend on compartment choice and filtering. A completed research draft is not an externally approved thesis or causal pumping validation. Original inputs and downloaded Thai source subsets are retained; previous redundant intermediates were removed with an audit.
'''
(ROOT/'reports/RESEARCH_RESULTS.md').write_text(summary,encoding='utf-8');(ROOT/'reports/FINAL_RELEASE.md').write_text(summary,encoding='utf-8');(W/'provenance/RESEARCH_RESULTS.md').write_text(summary,encoding='utf-8')
readme=W/'README.md';readme.write_text(summary+'\n## Reproducibility and licenses\n\nThe full local project is rooted at P:/twsa. Run analysis scripts 06–09 with conda environment thailand-sm after acquiring the documented WaterGAP subsets. Scripts 10–12 package the app and documents. The research_source snapshot requires the full project input layout; this static website itself needs only a web server, with no API key or build step.\n\nWaterGAP outputs are CC BY 4.0; GROW observation derivatives retain CC BY-NC-SA 4.0 package terms and Thai source metadata CC BY 4.0. This is a noncommercial research release. Original G3P, NASA, FAO, CHIRPS, GLEAM, ESA CCI and ONWR source terms remain applicable; no universal license is asserted. Vendored Leaflet and ECharts retain their included licenses.\n',encoding='utf-8')
p=ROOT/'README.md';s=p.read_text(encoding='utf-8').replace('Thailand_Objective2/analysis_v3','Thailand_Objective2/analysis_v4').replace('Thailand_Objective3/outputs/Thailand_Three_Objectives_Research.pptx','deliverables/Thailand_Three_Objectives_Farzeen_Khanal.pptx');p.write_text(s,encoding='utf-8')
print('Final scientific source, documents and web release packaged.')
