"""Check physical identities and compare recomputed tables with frozen results."""
import json,os
from pathlib import Path
import numpy as np,pandas as pd,xarray as xr
from research_common import ROOT,OBJ1

package=Path(os.environ['TWSA_PACKAGE_ROOT']);O=ROOT/'Thailand_Objective2/analysis_v4';checks={}
with xr.open_dataset(OBJ1/'netcdf/Thailand_TWSA_GWSA_components.nc') as d:
    error=float(abs(d.GWSA-(d.TWSA_GWS_reference-d.SMSA-d.SWSA-d.CanopyA-d.SWEA)).max())
    assert error<1e-8;assert d.GWSA.sel(time=slice('2023-10-01',None)).isnull().all()
    checks['grid_groundwater_balance_max_error_mm']=error
f=pd.read_csv(O/'tables/naturalized_attribution_timeseries.csv',dtype={'region':str})
assert f.groupby(['region','variable']).ngroups==46
for identity in [f.observed_mm-f.climate_mm-f.residual_mm,f.residual_mm-f.modeled_human_mm-f.discrepancy_mm]:assert np.nanmax(abs(identity))<1e-8
p=pd.read_csv(O/'tables/additive_linear_trend_partition.csv')
assert np.max(abs(p.observed_mm-p.climate_mm-p.residual_mm))<1e-8
assert np.max(abs(p.residual_mm-p.modeled_human_mm-p.discrepancy_mm))<1e-8
weights=pd.read_csv(O/'tables/climate_emulator_weights.csv');assert np.allclose(weights.groupby(['region','variable']).weight.sum(),1)
e=pd.read_csv(O/'tables/groundwater_attribution_evidence.csv');assert len(e)==276
comparisons=[]
for expected in sorted((package/'reference').rglob('*.csv')):
    relative=expected.relative_to(package/'reference');actual=ROOT/relative
    if not actual.is_file():raise AssertionError('Missing recomputed output: '+str(relative))
    a=pd.read_csv(actual,dtype={'region':str});b=pd.read_csv(expected,dtype={'region':str})
    pd.testing.assert_frame_equal(a,b,check_dtype=False,check_exact=False,rtol=1e-5,atol=1e-5)
    comparisons.append({'table':relative.as_posix(),'rows':len(a),'numeric_tolerance':'rtol=1e-5, atol=1e-5'})
d=json.loads((ROOT/'dashboard/data/analysis.json').read_text(encoding='utf-8'))
assert len(d['regions'])==23 and len(d['meta']['dates'])==270
for code,series in d['series'].items():
    assert all(len(values)==270 for values in series.values())
    for var in ['TWSA','GWSA']:
        a=np.array(series[var+'_attribution_observed'],dtype=float);c=np.array(series[var+'_climate'],dtype=float);r=np.array(series[var+'_residual'],dtype=float)
        assert np.nanmax(abs(a-c-r))<1e-8
checks.update(passed=True,table_comparisons=comparisons,region_target_pairs=46,well_evidence_rows=276,package_inputs_only=True,reference_files_used_for='Comparison only; never substituted for computed scientific outputs',scientific_caveat='Reproduction does not establish causal human depletion or repair missing original GRACE metadata.')
(ROOT/'reports/reproduction_qa.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
print(json.dumps(checks,indent=2))
