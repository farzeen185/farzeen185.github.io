"""Refresh computed series and scores in a local copy of the published DSS."""
import json,os,shutil
from pathlib import Path
import numpy as np,pandas as pd
from research_common import ROOT,OBJ1

package=Path(os.environ['TWSA_PACKAGE_ROOT']);site=package.parent;out=ROOT/'dashboard';out.mkdir(exist_ok=True)
for name in ['index.html','app.js','styles.css']:
    shutil.copy2(site/name,out/name)
shutil.copytree(site/'vendor',out/'vendor',dirs_exist_ok=True)
(out/'data').mkdir(exist_ok=True);shutil.copy2(site/'data/basins.geojson',out/'data/basins.geojson')
d=json.loads((site/'data/analysis.json').read_text(encoding='utf-8'));dates=d['meta']['dates']
O=ROOT/'Thailand_Objective2/analysis_v4'
read=lambda path:pd.read_csv(path,dtype={'region':str})
observed=read(OBJ1/'tables/basin_storage_timeseries.csv');trends=read(OBJ1/'tables/basin_TWSA_GWSA_Sen_MannKendall.csv')
f=read(O/'tables/naturalized_attribution_timeseries.csv');m=read(O/'tables/climate_emulator_validation.csv');b=read(O/'tables/hydrological_benchmarks.csv');e=read(O/'tables/groundwater_attribution_evidence.csv')
indices=read(ROOT/'Thailand_Objective2/analysis_v3/tables/basin_groundwater_observation_indices.csv')
assignment=read(ROOT/'Thailand_Objective2/analysis_v3/tables/groundwater_well_basin_assignment.csv')
for r in d['regions']:
    code=r['code'];obs=observed[observed.region==code].set_index('date').reindex(dates)
    wells=assignment if code=='TH' else assignment[assignment.region==code]
    r['groundwater_wells']=int(wells.well_id.nunique());r['monthly_wells']=int(wells[wells.interval=='MS'].well_id.nunique())
    for interval,key,fmt in [('YS','annual','%Y'),('MS','monthly','%Y-%m')]:
        q=indices[(indices.region==code)&(indices.quality=='retained_flags')&(indices.interval==interval)].sort_values('date')
        d['evidence'][code][key]=[{'date':pd.Timestamp(x.date).strftime(fmt),'value':x.well_head_z,'count':int(x.n_station_groups)} for x in q.itertuples()]
    for var in ['TWSA','GWSA']:
        d['series'][code][var]=obs[var].tolist()
        r['trends'][var]=trends[(trends.region==code)&(trends.variable==var)].iloc[0].to_dict()
        z=f[(f.region==code)&(f.variable==var)].set_index('date').reindex(dates)
        for suffix,col in [('attribution_observed','observed_mm'),('climate','natural_continuous_mm'),('residual','residual_mm'),('benchmark','human_continuous_mm'),('modeledhuman','modeled_human_mm'),('discrepancy','discrepancy_mm')]:d['series'][code][var+'_'+suffix]=z[col].tolist()
        row=m[(m.region==code)&(m.variable==var)&(m.model=='Ensemble')&(m.period=='Test')].iloc[0].to_dict();row['credible_validation']=row['validation_support']
        score=b[(b.region==code)&(b.variable==var)&b.comparison.str.startswith('Historical')].iloc[0];row.update(benchmark_NSE=score.NSE,benchmark_r=score.r,noah_land_NSE=b[(b.region==code)&(b.variable=='land_storage')].iloc[0].NSE)
        r['models'][var]=row
    d['evidence'][code]['correlations']=e[(e.region==code)&(e.quality=='retained_flags')&(e.component=='residual_mm')].assign(component='unexplained_residual').to_dict('records')
def safe(v):
    if isinstance(v,dict):return {str(k):safe(x) for k,x in v.items()}
    if isinstance(v,list):return [safe(x) for x in v]
    if isinstance(v,(float,np.floating)):return float(v) if np.isfinite(v) else None
    if isinstance(v,np.integer):return int(v)
    if isinstance(v,np.bool_):return bool(v)
    return v
d['meta']['reproduction_note']='Storage, attribution, emulator scores, well displays and residual/head evidence recomputed locally; cartographic metadata and static irrigation context retained from the published release.'
(out/'data/analysis.json').write_text(json.dumps(safe(d),ensure_ascii=False,allow_nan=False,separators=(',',':')),encoding='utf-8')
downloads=out/'downloads';downloads.mkdir(exist_ok=True)
for folder in [OBJ1/'tables',O/'tables']:
    for file in folder.glob('*.csv'):shutil.copy2(file,downloads/file.name)
for file in (site/'downloads').iterdir():
    if file.suffix in {'.docx','.pdf','.pptx','.md'}:shutil.copy2(file,downloads/file.name)
print('Dashboard refreshed. Serve using: python -m http.server 8000 --directory "'+str(out)+'"')
