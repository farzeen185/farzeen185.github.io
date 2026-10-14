"""Publish only genuine, aggregated research outputs in a buildless dashboard."""
import json, shutil
import numpy as np
import pandas as pd
import geopandas as gpd
from research_common import ROOT, OBJ1, OBJ2

WEB=ROOT/'Thailand_Objective3/web_app'; (WEB/'data').mkdir(exist_ok=True)
def read(path): return pd.read_csv(path,dtype={'region':str})
def clean(value):
    if isinstance(value,dict):return {str(k):clean(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [clean(v) for v in value]
    if isinstance(value,(np.bool_,)):return bool(value)
    # Preserve very small p-values; decimal rounding would turn them into false zeros.
    if isinstance(value,(float,np.floating)):return float(value) if np.isfinite(value) else None
    if isinstance(value,(np.integer,)):return int(value)
    return value
storage=read(OBJ1/'tables/basin_storage_timeseries.csv')
trends=read(OBJ1/'tables/basin_TWSA_GWSA_Sen_MannKendall.csv')
forecast=read(OBJ2/'tables/basin_climate_residual_timeseries.csv')
models=read(OBJ2/'tables/ensemble_validation.csv')
coverage=read(OBJ2/'tables/predictor_coverage.csv')
pressure=read(OBJ2/'tables/basin_irrigation_pressure.csv')
wells=read(OBJ2/'tables/groundwater_well_basin_assignment.csv')
indices=read(OBJ2/'tables/basin_groundwater_observation_indices.csv')
correlations=read(OBJ2/'tables/groundwater_storage_residual_agreement.csv')
dates=sorted(storage.date.unique());regions=[];series={};evidence={}
for code,g in storage.groupby('region',sort=False):
    g=g.set_index('date').reindex(dates)
    region={'code':code,'name':g.region_name.dropna().iloc[0],'trends':{},'models':{}}
    series[code]={}
    for variable in ['TWSA','GWSA']:
        region['trends'][variable]=trends[(trends.region==code)&(trends.variable==variable)].iloc[0].to_dict()
        m=models[(models.region==code)&(models.variable==variable)&(models.period=='Test')]
        region['models'][variable]=m.iloc[0].to_dict() if len(m) else {}
        series[code][variable]=g[variable].tolist()
        f=forecast[(forecast.region==code)&(forecast.variable==variable)].set_index('date').reindex(dates)
        # Do not display projections beyond the last observed target as reconstructions.
        last=g[variable].last_valid_index()
        for suffix,field in [('climate','climate_mm'),('residual','unexplained_residual_mm'),('benchmark','benchmark_mm')]:
            values=f[field].copy()
            if last is not None:values.loc[values.index>last]=np.nan
            series[code][variable+'_'+suffix]=values.tolist()
    w=wells if code=='TH' else wells[wells.region==code]
    region.update(groundwater_wells=int(w.well_id.nunique()),monthly_wells=int(w[w.interval=='MS'].well_id.nunique()))
    p=pressure[pressure.region==code];region['pressure']=p.iloc[0].to_dict() if len(p) else {}
    c=coverage[(coverage.region==code)&(~coverage.variable.str.startswith('ESA'))]
    region['minimum_forcing_coverage']=float(c.finite_area_mean.min())
    regions.append(region)
    i=indices[(indices.region==code)&(indices.quality=='retained_flags')]
    evidence[code]={'annual':[{'date':x.date[:4],'value':x.well_head_z,'count':x.n_station_groups} for x in i[i.interval=='YS'].itertuples()],
                    'monthly':[{'date':x.date[:10],'value':x.well_head_z,'count':x.n_station_groups} for x in i[i.interval=='MS'].itertuples()],
                    'correlations':correlations[(correlations.region==code)&(correlations.quality=='retained_flags')&(correlations.interval=='YS')].to_dict('records'),
                    'fixed_panel_correlations':correlations[(correlations.region==code)&(correlations.quality=='fixed_2013_2022_panel')&(correlations.interval=='YS')].to_dict('records')}
sources=[
 {'name':'G3P v1.12 storage compartments','url':'https://doi.org/10.5880/G3P.2024.001','note':'LISFLOOD surface water and related GWS benchmark; April 2002–September 2023.'},
 {'name':'GLDAS Noah','url':'https://ldas.gsfc.nasa.gov/gldas','note':'Four soil layers, canopy and snow. Noah does not contain groundwater storage.'},
 {'name':'GROW observational groundwater database','url':'https://doi.org/10.5281/zenodo.15149480','note':'511 Thai wells; 5,484 observed aggregates. Package CC BY-NC-SA 4.0; Thai source metadata CC BY 4.0.'},
 {'name':'FAO Global Map of Irrigation Areas v5','url':'https://www.fao.org/aquastat/en/geospatial-information/global-maps-irrigated-areas/latest-version/','note':'Static equipped-area and inferred groundwater-irrigation proxies; not pumping measurements.'},
 {'name':'GRACE and GRACE-FO','url':'https://grace.jpl.nasa.gov/data/get-data/','note':'Local monthly TWSA input; nominal 0.25° sampling is not independent spatial resolution.'},
 {'name':'CHIRPS','url':'https://www.chc.ucsb.edu/data/chirps','note':'Monthly precipitation input.'},
 {'name':'GLEAM','url':'https://www.gleam.eu/','note':'Monthly evapotranspiration, conservatively aggregated.'},
 {'name':'ESA CCI Soil Moisture','url':'https://climate.esa.int/en/projects/soil-moisture/','note':'Surface and 0–1 m root-zone predictor anomalies.'}]
payload=clean({'meta':{'dates':dates,'release_date':'2026-10-14','sources':sources,'baseline':'2004–2009','interpretation':'Candidate human residual includes model and observation error; it is not proven causal abstraction.'},'regions':regions,'series':series,'evidence':evidence})
assert len(regions)==23 and len(set(x['code'] for x in regions))==23
for values in series.values():
    assert all(len(v)==270 for v in values.values())
for code in series:
    for variable in ['TWSA','GWSA']:
        s=series[code];a=np.array(s[variable]);c=np.array(s[variable+'_climate']);r=np.array(s[variable+'_residual'])
        assert np.nanmax(abs(a-c-r))<1e-8
(WEB/'data/analysis.json').write_text(json.dumps(payload,ensure_ascii=False,allow_nan=False,separators=(',',':')),encoding='utf-8')
geo=gpd.read_file(ROOT/'Thailand_Objective2/data/BASINS/MainBasin_ONWR_Law_WGS84.shp').to_crs(4326)
geo['code']=geo.MB_CODE.str.split('-').str[0].str.zfill(2)
geo=geo.dissolve(by='code',as_index=False,aggfunc='first').rename(columns={'MBASIN_E':'name','AREA_SQKM':'area_km2'})
geo.geometry=geo.geometry.simplify(.003,preserve_topology=True)
geo[['code','name','geometry']].to_file(WEB/'data/basins.geojson',driver='GeoJSON')
assert len(geo)==22
(WEB/'.nojekyll').touch()
(WEB/'downloads').mkdir(exist_ok=True)
for folder in [OBJ1/'tables',OBJ2/'tables']:
    for name in ['basin_TWSA_GWSA_Sen_MannKendall.csv','ensemble_validation.csv','climate_residual_Sen_MannKendall.csv','groundwater_storage_residual_agreement.csv','residual_irrigation_spatial_association.csv']:
        if (folder/name).exists():shutil.copy2(folder/name,WEB/'downloads'/name)
print('Dashboard packaged: 22 basins + national, genuine observations, 270 monthly dates.')
