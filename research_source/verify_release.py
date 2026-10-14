"""Meaningful cross-product checks before publishing research outputs."""
import json
import numpy as np
import pandas as pd
import xarray as xr
from research_common import ROOT,OBJ1,OBJ2
checks={}
with xr.open_dataset(OBJ1/'netcdf/Thailand_TWSA_GWSA_components.nc') as d:
    error=d.GWSA-(d.TWSA_GWS_reference-d.SMSA-d.SWSA-d.CanopyA-d.SWEA)
    checks['groundwater_balance_max_error_mm']=float(abs(error).max())
    assert checks['groundwater_balance_max_error_mm']<1e-8
    assert d.GWSA.sel(time=slice('2023-10-01',None)).isnull().all()
    assert d.TWSA.time.size==270
read=lambda p:pd.read_csv(p,dtype={'region':str})
trends=read(OBJ1/'tables/basin_TWSA_GWSA_Sen_MannKendall.csv')
balance=read(OBJ1/'tables/basin_storage_timeseries.csv')
checks['basin_groundwater_balance_max_error_mm']=float(abs(balance.GWSA-(balance.TWSA_GWS_reference-balance.SMSA-balance.SWSA-balance.CanopyA-balance.SWEA)).max())
assert checks['basin_groundwater_balance_max_error_mm']<1e-4 # Float32 component arithmetic.
for variable in ['TWSA','GWSA']:
    g=trends[trends.variable==variable];assert g.region.nunique()==23 and g.sen_slope_mm_year.notna().all()
forecast=read(OBJ2/'tables/basin_climate_residual_timeseries.csv')
checks['climate_ensembles']=forecast.groupby(['region','variable']).ngroups;assert checks['climate_ensembles']==46
assert np.nanmax(abs(forecast.observed_mm-forecast.climate_mm-forecast.unexplained_residual_mm))<1e-8
weights=read(OBJ2/'tables/ensemble_weights.csv');assert np.allclose(weights.groupby(['region','variable']).weight.sum(),1)
metrics=read(OBJ2/'tables/all_model_validation.csv');checks['model_configurations']=metrics.groupby(['region','variable','model']).ngroups;assert checks['model_configurations']==1380
gw=pd.read_csv(ROOT/'shared_data/groundwater/GROW/GROW_Thailand_observations.csv');assert len(gw)==5484 and gw.well_id.nunique()==511
assert not gw.duplicated(['well_id','date','interval']).any()
assert gw.depth_to_water_m.notna().all() and gw.value_status.str.startswith('observed').all()
signed=read(OBJ2/'tables/groundwater_signed_anomalies.csv');assert np.allclose(signed.head_m,-signed.depth_to_water_m)
wells=read(OBJ2/'tables/groundwater_well_basin_assignment.csv');assert wells.region.notna().all() and wells.well_id.nunique()==511
pressure=read(OBJ2/'tables/basin_irrigation_pressure.csv');assert len(pressure)==22 and pressure.region.nunique()==22
assert pressure.irrigation_equipped_pct.between(0,100).all();assert pressure.groundwater_equipped_pct_total_area.between(0,100).all()
dashboard=json.loads((ROOT/'Thailand_Objective3/web_app/data/analysis.json').read_text(encoding='utf-8'))
assert len(dashboard['regions'])==23 and len(dashboard['meta']['dates'])==270
for r in dashboard['regions']:
    for variable in ['TWSA','GWSA']:
        original=trends[(trends.region==r['code'])&(trends.variable==variable)].iloc[0]
        assert r['trends'][variable]['mk_seasonal_p']==original.mk_seasonal_p
        assert np.isclose(r['trends'][variable]['sen_slope_mm_year'],original.sen_slope_mm_year)
checks.update(passed=True,basins=22,national=True,actual_wells=511,actual_observation_aggregates=5484,missing_dates_preserved=True,ensemble_weights_normalized=True,groundwater_sign_correct=True,p_values_preserved=True)
(ROOT/'reports/scientific_qa.json').write_text(json.dumps(checks,indent=2),encoding='utf-8');print(json.dumps(checks,indent=2))
