"""Physical, support, and reference-table regression checks."""
import os,json
from pathlib import Path
import h5py,numpy as np,pandas as pd,xarray as xr
from research_common import ROOT
P=Path(os.environ['TWSA_V5_PACKAGE']);O=ROOT/'Thailand_Research_v5';checks={}
with xr.open_dataset(O/'netcdf/CSR_storage_components.nc',engine='h5netcdf') as d:
    error=float(abs(d.GWSA-(d.TWSA_GWS_reference-d.SMSA-d.SWSA-d.CanopyA-d.SWEA)).max());assert error<1e-8
    assert d.GWSA.sel(time=slice('2023-10-01',None)).isnull().all();checks['storage_balance_max_error_mm']=error
f=pd.read_csv(O/'tables/CSR_naturalized_attribution.csv',dtype={'region':str});assert f.groupby(['region','variable']).ngroups==46
for e in [f.observed_mm-f.climate_mm-f.residual_mm,f.residual_mm-f.modeled_human_mm-f.discrepancy_mm]:assert np.nanmax(abs(e))<1e-8
t=pd.read_csv(O/'tables/CSR_basin_trends.csv',dtype={'region':str});assert len(t)==69
assert t[(t.region=='TH')&(t.variable=='TWSA')].n_months.iloc[0]==237
assert t[(t.region=='TH')&(t.variable=='GWSA')].n_months.iloc[0]==225
gw=pd.read_csv(O/'tables/CSR_groundwater_network_evidence.csv',dtype={'region':str});assert len(gw)==460
qa=json.loads((O/'logs/reservoir_evidence_qa.json').read_text());assert qa['inventory_reservoirs']==27 and qa['fixed_pre2004_reservoirs']==26
tables=[]
for source in sorted((P/'reference').glob('*.csv')):
    a=pd.read_csv(O/'tables'/source.name,dtype={'region':str});b=pd.read_csv(source,dtype={'region':str})
    pd.testing.assert_frame_equal(a,b,check_dtype=False,check_exact=False,rtol=1e-5,atol=1e-5);tables.append({'table':source.name,'rows':len(a)})
checks.update(passed=True,reference_tables=tables,basins=22,region_targets=46,reference_use='Comparison only; never substituted for recomputed outputs',interpretation='Numerical reproduction does not establish causal human depletion.')
figure_tables=[]
for source in sorted((P/'figure_revision_reference').glob('*.csv')):
    a=pd.read_csv(O/'figure_revision/tables'/source.name,dtype={'region':str});b=pd.read_csv(source,dtype={'region':str})
    pd.testing.assert_frame_equal(a,b,check_dtype=False,check_exact=False,rtol=1e-5,atol=1e-5);figure_tables.append({'table':source.name,'rows':len(a)})
checks['figure_revision_tables']=figure_tables
(O/'logs/reproduction_qa.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks,indent=2))
