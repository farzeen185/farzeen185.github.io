"""Exercise real inputs and statistical utilities without fitting all models."""
import importlib.metadata as md,json,sys
from pathlib import Path
import numpy as np,pandas as pd,xarray as xr,geopandas as gpd
from research_common import ROOT,region_weights,trend_statistics,weighted_series

versions={p:md.version(p) for p in ['numpy','pandas','xarray','netCDF4','h5netcdf','h5py','cftime','scipy','scikit-learn','joblib','geopandas','rasterio','pyproj','shapely','pymannkendall','matplotlib','requests']}
with xr.open_dataset(ROOT/'Thailand_Objective2/data/GRACE_TWSA_Monthly_2002_2024.nc') as d:
    a=d.twsa.sortby('lat',ascending=False).sortby('lon').load()
    assert a.attrs['units']=='cm' and a.shape[1:]==(62,36)
    regions=region_weights(a.lat,a.lon);assert len(regions)==23
    values,coverage=weighted_series(a,regions[0][2]);assert np.isfinite(values).sum()==235
with xr.open_dataset(ROOT/'shared_data/GLDAS/GLDAS_NOAH_monthly_storage_200204_202409_Thailand.nc',engine='h5netcdf') as d:
    soil=sum(d[n] for n in d if n.startswith('SoilMoi'))
    assert float(abs(soil+d.CanopInt_inst+d.SWE_inst-d.NOAH_TWS).max())<.05
for path in sorted((ROOT/'shared_data/WaterGAP').glob('*.nc')):
    with xr.open_dataset(path,engine='h5netcdf') as d:
        assert d.sizes['time']==516
        assert str(d.time.values[0])[:10]=='1981-01-01' and str(d.time.values[-1])[:10]=='2023-12-01'
w=pd.read_csv(ROOT/'shared_data/groundwater/GROW/GROW_Thailand_observations.csv')
assert len(w)==5484 and w.well_id.nunique()==511
assert not w.duplicated(['well_id','date','interval']).any()
g=gpd.read_file(ROOT/'Thailand_Objective2/data/BASINS/MainBasin_ONWR_Law_WGS84.shp')
assert g.MB_CODE.str.split('-').str[0].nunique()==22
dates=pd.date_range('2000-01-01',periods=120,freq='MS');y=np.asarray(2*(dates.year-2000)+np.sin(dates.month*2*np.pi/12),dtype=float);y[30:35]=np.nan
assert np.isclose(trend_statistics(y,dates)['sen_slope_mm_year'],2)
report={'passed':True,'python':sys.version,'versions':versions,'inputs_exercised':['GRACE','GLDAS balance','ten WaterGAP monthly subsets','511 wells','22 basin geometries','fractional weights'],'known_sen_slope_test':2}
(ROOT/'reports/smoke_qa.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
