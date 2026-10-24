"""Objective 2 revision: paired naturalized/human hydrology, without GRACE fitting."""
import json,warnings
import numpy as np,pandas as pd,xarray as xr
from research_common import ROOT,OBJ1,region_weights,weighted_series,trend_statistics,bh_fdr,metrics
OUT=ROOT/'Thailand_Objective2/analysis_v4'
for name in ['tables','netcdf','figures','models','logs']:(OUT/name).mkdir(parents=True,exist_ok=True)
source=ROOT/'shared_data/WaterGAP';dates=pd.date_range('1981-01-01','2023-12-01',freq='MS')
print('Loading observed components',flush=True)
with xr.open_dataset(OBJ1/'netcdf/Thailand_TWSA_GWSA_components.nc',engine='h5netcdf') as f:obs=f.reindex(time=dates).load()
print('Observed components loaded',flush=True)
def load(scenario,var):
    p=source/f'WaterGAP22e_ERA5_{scenario}_{var}_Thailand_1981_2023.nc'
    print('Loading',scenario,var,flush=True)
    with xr.open_dataset(p,engine='h5netcdf') as f:
        a=f[var].reindex(time=dates).interp(lat=obs.lat,lon=obs.lon,method='nearest').load()
    return a.astype('float64')
nat={v:load('natural',v) for v in ['tws','groundwstor','soilmoist','canopystor','swe','precmon','potevap']}
human={v:load('human',v) for v in ['tws','groundwstor','anag']}
regions=region_weights(obs.lat,obs.lon);arrays={};frames=[];trendrows=[];benchmarkrows=[]
baseline=(obs.time.dt.year>=2004)&(obs.time.dt.year<=2009)
for target,var in [('TWSA','tws'),('GWSA','groundwstor')]:
    joint=np.isfinite(nat[var])&np.isfinite(human[var]);ref=baseline&joint&obs[target].notnull()
    n=nat[var]-nat[var].where(ref).mean('time');h=human[var]-human[var].where(ref).mean('time')
    observed=obs[target].where(joint);n=n.where(joint);h=h.where(joint)
    arrays.update({target+'_natural':n,target+'_historical_human':h,target+'_modeled_human':h-n,target+'_observed':observed,target+'_residual':observed-n,target+'_discrepancy':observed-h})
    for code,name,w in regions:
        frame=pd.DataFrame({'date':dates,'region':code,'region_name':name,'variable':target})
        # Use identical observation-valid support for every attribution term.
        for key,a in [('observed_mm',observed),('climate_mm',n),('historical_human_mm',h),('modeled_human_mm',h-n),('residual_mm',observed-n),('discrepancy_mm',observed-h)]:
            if key in ['climate_mm','historical_human_mm','modeled_human_mm']:a=a.where(observed.notnull())
            values,coverage=weighted_series(a,w,threshold=.5);frame[key]=values
            if key=='observed_mm':frame['valid_area_fraction']=coverage
        # Continuous model-only records support verification before GRACE existed.
        for key,a in [('natural_continuous_mm',n),('human_continuous_mm',h),('precipitation_mm_day',nat['precmon']*86400),('potential_ET_mm_day',nat['potevap']*86400),('net_groundwater_abstraction_mm_day',human['anag']*86400)]:frame[key]=weighted_series(a,w,threshold=.5)[0]
        if target=='GWSA':frame['alternative_soil_observed_mm']=weighted_series(obs.GWSA_filtered_soil_sensitivity.where(joint),w,threshold=.5)[0]
        frames.append(frame)
        for component in ['observed_mm','climate_mm','historical_human_mm','modeled_human_mm','residual_mm','discrepancy_mm']:
            values=frame[component].to_numpy();valid=np.flatnonzero(np.isfinite(values));i=slice(valid[0],valid[-1]+1) if len(valid) else slice(0,0)
            with warnings.catch_warnings():warnings.simplefilter('ignore');st=trend_statistics(values[i],dates[i],bootstrap=100)
            trendrows.append({'region':code,'region_name':name,'variable':target,'component':component,**st})
        for label,field in [('Naturalized model','climate_mm'),('Historical human model','historical_human_mm')]:
            ok=dates.year>=2003;benchmarkrows.append({'region':code,'region_name':name,'variable':target,'comparison':label+' versus observations',**metrics(frame.observed_mm[ok],frame[field][ok]),'role':'Observation consistency, not model selection or independent pumping proof'})
        print('Naturalized decomposition',code,target,flush=True)
# Noah comparison must match land compartments rather than total/groundwater storage.
land=nat['soilmoist']+nat['canopystor']+nat['swe']
noah=obs.GLDAS_land_storage_anomaly
common=land.notnull()&noah.notnull();reference=baseline&common
land=land-land.where(reference).mean('time');noah=noah-noah.where(reference).mean('time')
for code,name,w in regions:
    a=weighted_series(land.where(common),w,threshold=.5)[0];b=weighted_series(noah.where(common),w,threshold=.5)[0]
    benchmarkrows.append({'region':code,'region_name':name,'variable':'land_storage','comparison':'Naturalized WaterGAP soil canopy snow versus GLDAS Noah soil canopy snow',**metrics(b,a),'role':'Cross-model matched-compartment benchmark; shared climatic drivers, not independent observations'})
f=pd.concat(frames,ignore_index=True);f.to_csv(OUT/'tables/naturalized_attribution_timeseries.csv',index=False)
tr=pd.DataFrame(trendrows)
for (var,component),g in tr.groupby(['variable','component']):
    ix=g[g.region!='TH'].index;tr.loc[ix,'mk_seasonal_q_FDR']=bh_fdr(tr.loc[ix,'mk_seasonal_p'])
tr.to_csv(OUT/'tables/naturalized_component_trends.csv',index=False);pd.DataFrame(benchmarkrows).to_csv(OUT/'tables/hydrological_benchmarks.csv',index=False)
d=xr.Dataset(arrays,attrs={'method':'Paired WaterGAP22e GSWP3-ERA5 naturalized and historical-human simulations; no GRACE calibration','reference':'2004–2009 common observed reference months','time_policy':'Publisher 360-day monthly year/month identities mapped to month starts without interpolation','interpretation':'Modeled direct-human perturbation relative to reference; observed residual also contains model and observation error','spatial':'Aligned 0.5-degree parent cells replicated at original 0.25-degree sampling; no additional independent resolution','license':'WaterGAP CC BY 4.0'})
for v in d:d[v].attrs['units']='mm'
d.to_netcdf(OUT/'netcdf/naturalized_human_decomposition.nc')
errors={'residual_identity_mm':float(np.nanmax(abs(f.residual_mm-f.modeled_human_mm-f.discrepancy_mm))),'storage_identity_mm':float(np.nanmax(abs(f.observed_mm-f.climate_mm-f.residual_mm)))}
assert max(errors.values())<1e-8
(OUT/'logs/decomposition_qa.json').write_text(json.dumps({'passed':True,'target_region_combinations':46,'period':'1981–2023 model verification; observed attribution 2002–2023 where available','errors':errors},indent=2),encoding='utf-8')
