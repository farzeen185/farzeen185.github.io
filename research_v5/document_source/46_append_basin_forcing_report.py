"""Append readable basin tables and forcing figures to the simple report."""
from pathlib import Path
import os,json,shutil,runpy,math
from docx import Document
ROOT=Path(os.environ.get('TWSA_RESEARCH_ROOT',Path(__file__).resolve().parents[1])).resolve()
OUT=ROOT/'Thailand_Research_v5';APP=OUT/'basin_forcing_appendix'
archive=OUT/'archive/before_basin_forcing_appendix';archive.mkdir(parents=True,exist_ok=True)
for suffix in ['docx','pdf']:
    f=OUT/f'report/AIT_Extended_Thesis_Farzeen_Khan.{suffix}'
    if f.exists() and not (archive/f.name).exists():shutil.copy2(f,archive/f.name)
# Rebuild the stable 60-page main report, so running this twice never duplicates
# the appendices. Script 43 uses the existing verified scientific figures.
scope=runpy.run_path(str(Path(__file__).with_name('43_simplify_report.py')))
M=scope['M'];w=M.Writer();w.d=Document(OUT/'report/AIT_Extended_Thesis_Farzeen_Khan.docx');w.bookmark=5000
for p in w.d.paragraphs:
    if p.text=='LIST OF FIGURES':p.runs[0].text='LIST OF MAIN TEXT FIGURES'
    elif p.text=='LIST OF TABLES':p.runs[0].text='LIST OF MAIN TEXT TABLES'
    elif 'The report presents the results through 21 figures' in p.text:
        for run in p.runs:run.text=run.text.replace('through 21 figures','through 31 figures')
# New appendices have their own short local lists to preserve a readable front
# matter layout and avoid crowding its main-text figure/table lists.
tables=json.loads((APP/'table_inventory.json').read_text(encoding='utf-8'))
figures=json.loads((APP/'figure_inventory.json').read_text(encoding='utf-8'))
w.page(61,'APPENDIX C\nBASIN PERFORMANCE AND VALUES',toc=True)
w.para('This appendix gives the values behind the basin figures. Every table contains all 22 basin codes; full basin names are in Appendix A. An em dash means that the comparison is unavailable or cannot be estimated. It does not mean zero change or zero effect.')
for x in tables:w.para(f"Table C.{x['id']}  {x['title']}",size=11,spacing=1.1,after=5)
w.para('Read model scores against their stated targets. The climate model reconstructs naturalized WaterGAP. GLDAS checks matching land compartments. Wells and reservoirs provide observation consistency checks. Their scores cannot be combined into one measure of human-impact accuracy.',size=11)
import csv
def number(value,col):
    if col=='region':return value
    if value is None or value=='':return '—'
    try:v=float(value)
    except (ValueError,TypeError):return value
    if not math.isfinite(v):return '—'
    if col.endswith('_n') or col in ['n','n_months','reservoir_count'] or col.endswith('_years'):return str(int(v))
    if col.endswith('_q'):return '<0.001' if v<.001 else f'{v:.3f}'
    return f'{v:.3f}' if 'r'==col or col.endswith('_r') or 'NSE' in col or col in ['TWS_Native','TWS_CHIRPS','GWS_Native','GWS_CHIRPS','ESA_CCI_SSM','ESA_CCI_RZSM'] else f'{v:.2f}'
for x in tables:
    w.page(61+x['id'],x['title'],toc=False)
    rows=list(csv.DictReader((APP/'tables'/x['file']).open(encoding='utf-8')))
    cols=x['columns'];vals=[[number(row.get(c),c) for c in cols] for row in rows]
    width=[.62]+[(6.15-.62)/(len(cols)-1)]*(len(cols)-1)
    w.table(f"Table C.{x['id']}",x['title'],x['headers'],vals,widths=width)
    w.para(x['note'],size=11,spacing=1.15,after=6)
    w.para('Machine-readable values: '+x['file'],size=10.5,spacing=1.1)
w.page(73,'APPENDIX D\nFORCING AND SUPPORTING DATA',toc=True)
w.para('The figures cover January 2003–December 2023, the shared calendar window for the native forcing and supporting products. Available-month means and trends keep each product’s actual gaps. A spatial map reports a basin average, not a new high-resolution climate field.')
w.para('Native precipitation and potential evapotranspiration are the actual meteorological inputs to the climate reconstruction. CHIRPS precipitation is used in the rainfall replacement test. GLEAM and MODIS actual evapotranspiration, ESA CCI surface and root-zone moisture, and MODIS land surface temperature describe the surrounding hydroclimatic conditions. They were not added to the primary model as predictors.')
for x in figures:w.para(f"Figure D.{x['id']}  {x['title']}",size=11,spacing=1.1,after=5)
w.para('Monthly precipitation and ET use mm/month; soil moisture uses m³/m³; temperature uses °C. Native daily-rate precipitation and potential ET are multiplied by the number of days in the month. Trend-map units are the displayed variable per year. Product sample counts, coverage and physical units are available in the accompanying CSV tables.',size=11,spacing=1.15)
for x in figures:
    for suffix in ['png','pdf']:shutil.copy2(APP/'figures'/Path(x['file']).with_suffix('.'+suffix),OUT/'figures'/Path(x['file']).with_suffix('.'+suffix))
    w.page(73+x['id'],x['title'],toc=False)
    w.fig(f"Figure D.{x['id']}",x['title'],x['file'],height=x['height'])
    w.para(x['note'],size=11,spacing=1.15)
w.save(OUT/'report/AIT_Extended_Thesis_Farzeen_Khan.docx')
(APP/'logs/report_contract.json').write_text(json.dumps({'expected_pages':83,'main_report_pages':60,'new_appendix_pages':23,'figures':31,'native_tables':17,'new_basin_tables':11,'new_forcing_figures':10,'basins_per_table':22,'methodology_unchanged':True},indent=2))
print('Report extended: 31 figures, 17 tables; native pagination verification required.')
