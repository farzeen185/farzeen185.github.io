"""Direct WaterGAP robustness extension: source support, baselines, wells and evidence."""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
from pathlib import Path
import json,warnings
import numpy as np,pandas as pd,xarray as xr
from scipy.ndimage import binary_erosion
from scipy.stats import pearsonr,spearmanr
from research_common import region_weights,weighted_series,seasonal_sen
R=Path(os.environ.get('TWSA_RESEARCH_ROOT',Path(__file__).resolve().parents[1]));O=R/'Thailand_Direct_WaterGAP_Analysis/robustness_extension';T=O/'tables';T.mkdir(exist_ok=True)
I=O/'inputs';S=R/'Thailand_Publication_v6/tables';rng=np.random.default_rng(262026)
read=lambda n:pd.read_csv(S/n,dtype={'region':str})
a=read('CSR_naturalized_attribution.csv');a.date=pd.to_datetime(a.date)
names=dict(zip(a.region,a.region_name))
macro={'M_CP':['06','07','08','09','10','11','12','13'],'M_MK':['02','03','04','05'],'M_S':['19','20','21','22'],'M_W':['01','14','15','16'],'M_E':['17','18']}
macro_names={'M_CP':'Chao Phraya reporting group','M_MK':'Thai Mekong reporting group','M_S':'Southern peninsula','M_W':'Western reporting group','M_E':'Eastern reporting group'}
def interval(g,key,B=499):
 q=g.dropna(subset=[key]);dt=pd.DatetimeIndex(q.date);y=q[key].to_numpy();t=(dt-dt[0]).days.to_numpy()/365.25;X=np.column_stack([np.ones(len(q)),t]+[(dt.month==m).astype(float) for m in range(2,13)]);pinv=np.linalg.pinv(X);b=pinv@y;e=y-X@b
 # Fixed-support calendar-block wild intervals, with two-year clusters.
 draws=[]
 for _ in range(B):
  offset=int(rng.integers(2));groups=(dt.year-dt.year.min()+offset)//2;sgn=rng.choice([-1.,1.],groups.max()+1)[groups];draws.append(b[1]+(pinv[1]*sgn)@e)
 return {'n':len(q),'seasonal_sen_mm_year':seasonal_sen(y,dt),'OLS_mm_year':b[1],'OLS_lo95':np.quantile(draws,.025),'OLS_hi95':np.quantile(draws,.975),'replicates':B,'uncertainty':f'{B} calendar two-year wild blocks, conditional on product/support'}

def spatial_audit():
 with xr.open_dataset(R/'Thailand_Research_v5/netcdf/CSR_storage_components.nc',engine='h5netcdf') as ds:ds=ds.load()
 dates=pd.DatetimeIndex(ds.time.values);base=xr.DataArray(dates.year.astype(int).astype(int)>=0,dims='time',coords={'time':dates});base[:]=dates.year.astype(int).astype(int)>=2004;base=base&(ds.time.dt.year<=2009)
 with xr.open_dataset(R/'shared_data/CSR_RL0603/CSR_GRACE_GRACE-FO_RL06_Mascons_v02_LandMask_Thailand.nc',engine='h5netcdf') as h:land=h.LO_val.sel(lat=ds.lat,lon=ds.lon).values>.5
 core=binary_erosion(land,structure=np.ones((3,3)),border_value=0)
 def loadg(kind,var):
  with xr.open_dataset(R/f'shared_data/surface_water/G3P_v1.12_{kind}_Thailand_buffer_monthly_200204_202309.nc',engine='h5netcdf') as f:
   q=f[var].assign_coords(time=pd.DatetimeIndex(f.time.values).to_period('M').to_timestamp()).sortby('lat').interp(lat=ds.lat,lon=ds.lon,method='nearest').reindex(time=dates).load().astype(float)
  return q.where(land)
 costg=loadg('TWS','tws');rz=loadg('RZSM','rzsm')
 def loadwg(var):
  with xr.open_dataset(R/f'shared_data/WaterGAP/WaterGAP22e_ERA5_natural_{var}_Thailand_1981_2023.nc',engine='h5netcdf') as f:return f[var].interp(lat=ds.lat,lon=ds.lon,method='nearest').reindex(time=dates).load().astype(float).where(land)
 wg=loadwg('tws');gw=loadwg('groundwstor')
 fields={'CSR_Noah':(ds.TWSA,ds.GWSA),'CSR_G3Psoil':(ds.TWSA,ds.TWSA_GWS_reference-rz-ds.SWSA-ds.CanopyA-ds.SWEA),'COSTG_Noah':(costg,costg-ds.SMSA-ds.SWSA-ds.CanopyA-ds.SWEA),'COSTG_G3Psoil':(costg,costg-rz-ds.SWSA-ds.CanopyA-ds.SWEA)}
 # Exact same grid/date support for every product and compartment variant.
 mask=ds.TWSA.notnull()&ds.GWSA.notnull()&costg.notnull()&rz.notnull()&wg.notnull()&gw.notnull()
 rebase=lambda z:(z-z.where(base&mask).mean('time')).where(mask)
 wg=rebase(wg);gw=rebase(gw)
 regs=region_weights(ds.lat,ds.lon);lookup={c:(n,w) for c,n,w in regs}
 regs+= [(c,macro_names[c],sum(lookup[x][1] for x in members)) for c,members in macro.items()]
 rows=[];ts=[];coastal=[]
 for code,name,weights in regs:
  for support,surface in [('provider_land',land),('interior_025deg_erosion',core)]:
   ww=weights*surface;frac=ww.sum()/(weights*land).sum();coastal.append({'region':code,'basin':name,'support':support,'retained_land_fraction':frac})
   if frac<.5:continue
   for chain,(tw,gg) in fields.items():
    for var,observed,climate in [('TWSA',tw,wg),('GWSA',gg,gw)]:
     # Soil variants give identical TWSA: retain one per gravity source.
     if var=='TWSA' and chain.endswith('G3Psoil'):continue
     yy,cov=weighted_series(rebase(observed),ww,threshold=.5);cc,_=weighted_series(climate,ww,threshold=.5)
     q=pd.DataFrame({'date':dates,'observed_mm':yy,'climate_mm':cc,'residual_mm':yy-cc});q=q.dropna()
     q['region']=code;q['region_name']=name;q['variable']=var;q['chain']=chain;q['support']=support
     ts.append(q)
     for component in ['observed_mm','residual_mm']:
      result=interval(q,component,B=199);rows.append({'region':code,'basin':name,'variable':var,'chain':chain,'support':support,'component':component,'retained_land_fraction':frac,**result})
  print('source/support audit',code,flush=True)
 pd.DataFrame(rows).to_csv(T/'factorial_product_component_support_trends.csv',index=False);pd.concat(ts).to_csv(T/'factorial_monthly_series.csv',index=False);pd.DataFrame(coastal).drop_duplicates().to_csv(T/'coastal_support_retention.csv',index=False)

def model_baselines():
 with xr.open_dataset(R/'Thailand_Research_v5/netcdf/CSR_storage_components.nc',engine='h5netcdf') as f:obs=f.TWSA.sel(time=slice('2002','2021')).load()
 dates=pd.DatetimeIndex(obs.time.values)
 with xr.open_dataset(R/'shared_data/WaterGAP/WaterGAP22e_ERA5_natural_tws_Thailand_1981_2023.nc',engine='h5netcdf') as f:primary=f.tws.interp(lat=obs.lat,lon=obs.lon,method='nearest').reindex(time=dates).load()
 models={'WaterGAP_GSWP3_ERA5':primary}
 for model in ['lpjml5-7-10-fire','watergap2-2e','miroc-integ-land']:
  path=I/(model+'_no_water_management_Thailand.nc')
  if not path.exists():raise FileNotFoundError('Acquire model baseline first: '+str(path))
  with xr.open_dataset(path,engine='h5netcdf') as f:
   assert f.tws.attrs['units']=='kg m-2';models[model+'_20CRV3_ERA5']=f.tws.sortby('lat').interp(lat=obs.lat,lon=obs.lon,method='nearest').reindex(time=dates).load()
 mask=obs.notnull()
 for v in models.values():mask=mask&v.notnull()
 reference=(obs.time.dt.year>=2004)&(obs.time.dt.year<=2009)&mask
 obs=(obs-obs.where(reference).mean('time')).where(mask);models={k:(v-v.where(reference).mean('time')).where(mask) for k,v in models.items()}
 regs=region_weights(obs.lat,obs.lon);lookup={c:(n,w) for c,n,w in regs};regs += [(c,macro_names[c],sum(lookup[x][1] for x in members)) for c,members in macro.items()]
 rows=[];series=[]
 for code,name,w in regs:
  yy,_=weighted_series(obs,w,threshold=.5)
  for model,z in models.items():
   cc,cov=weighted_series(z,w,threshold=.5);q=pd.DataFrame({'date':dates,'observed_mm':yy,'climate_mm':cc,'residual_mm':yy-cc}).dropna();q['region']=code;q['region_name']=name;q['baseline']=model;series.append(q)
   for component in ['climate_mm','residual_mm']:rows.append({'region':code,'basin':name,'baseline':model,'component':component,**interval(q,component)})
 pd.concat(series).to_csv(T/'alternative_baseline_monthly.csv',index=False);pd.DataFrame(rows).to_csv(T/'alternative_baseline_trends.csv',index=False)

def fixed_wells():
 d=pd.read_csv(R/'Thailand_Objective2/analysis_v3/tables/groundwater_signed_anomalies.csv',dtype={'region':str},parse_dates=['date']);d=d[(d.interval=='YS')&d.date.dt.year.between(2013,2022)&d.head_z.notna()]
 rows=[];series=[]
 for code in ['TH']+sorted(x for x in names if x!='TH'):
  local=d if code=='TH' else d[d.region==code]
  station=local.groupby(['date','station_group']).head_z.median().unstack('station_group').reindex(pd.date_range('2013','2022',freq='YS'))
  for panel in ['changing_network','strict_balanced']:
   mat=station if panel=='changing_network' else station.loc[:,station.notna().all()]
   if not mat.shape[1]:continue
   for var in ['TWSA','GWSA']:
    g=a[(a.region==code)&(a.variable==var)].set_index('date');annual=g[['observed_mm','climate_mm','residual_mm']].resample('YS').agg(['mean','count']);out=pd.DataFrame(index=station.index);out['head_index']=mat.mean(axis=1)
    for component in ['observed_mm','climate_mm','residual_mm']:out[component]=annual[component]['mean'].where(annual[component]['count']>=8)
    paired=out.dropna();n=len(paired)
    for component in ['observed_mm','residual_mm']:
     rho=pearsonr(paired.head_index,paired[component]).statistic if n>=6 else np.nan;boot=[]
     if n>=8 and mat.shape[1]>=3:
      M=mat.reindex(paired.index).to_numpy()
      for _ in range(499):
       pick=rng.integers(M.shape[1],size=M.shape[1])
       with warnings.catch_warnings():warnings.simplefilter('ignore');bh=np.nanmean(M[:,pick],axis=1)
       if np.isfinite(bh).all() and np.std(bh)>0:boot.append(pearsonr(bh,paired[component]).statistic)
     rows.append({'region':code,'variable':var,'component':component,'panel':panel,'n_years':n,'station_groups':mat.shape[1],'r':rho,'station_boot_lo95':np.quantile(boot,.025) if boot else np.nan,'station_boot_hi95':np.quantile(boot,.975) if boot else np.nan,'interval_scope':'station resampling conditional on observed years; not temporal or causal uncertainty'})
    out['region']=code;out['variable']=var;out['panel']=panel;out['station_groups']=mat.shape[1];series.append(out.reset_index(names='date'))
 pd.DataFrame(rows).to_csv(T/'fixed_network_comparison.csv',index=False);pd.concat(series).to_csv(T/'fixed_network_monthly_annual_support.csv',index=False)

def reservoir_checks():
 w=pd.read_csv(S/'independent_reservoir_timeseries.csv',dtype={'region':str},parse_dates=['date']);rows=[]
 for (code,var),g in a[a.variable=='TWSA'].groupby(['region','variable']):
  q=g.merge(w[(w.region==code)&(w.level==1)][['date','SWSA_reservoir_mm']],on='date').dropna(subset=['residual_mm','SWSA_reservoir_mm']);n=len(q)
  if n<24:continue
  dt=pd.DatetimeIndex(q.date);tt=(dt-dt[0]).days.to_numpy()/365.25;X=np.column_stack([np.ones(n),tt]+[(dt.month==m).astype(float) for m in range(2,13)]);x=q.SWSA_reservoir_mm.to_numpy();y=q.residual_mm.to_numpy();ex=x-X@np.linalg.lstsq(X,x,rcond=None)[0];ey=y-X@np.linalg.lstsq(X,y,rcond=None)[0];r=pearsonr(ex,ey).statistic;years=np.unique(dt.year);boot=[];leave=[]
  for _ in range(999):
   pick=rng.choice(years,len(years),replace=True);ii=np.concatenate([np.where(dt.year==yr)[0] for yr in pick]);boot.append(pearsonr(ex[ii],ey[ii]).statistic)
  for yr in years:
   keep=dt.year!=yr
   if keep.sum()>=24:leave.append(pearsonr(ex[keep],ey[keep]).statistic)
  rows.append({'region':code,'basin':names[code],'n_months':n,'n_years':len(years),'r_raw':pearsonr(x,y).statistic,'r_season_trend_removed':r,'year_cluster_lo95':np.quantile(boot,.025),'year_cluster_hi95':np.quantile(boot,.975),'leave_one_year_min_r':min(leave) if leave else np.nan,'leave_one_year_max_r':max(leave) if leave else np.nan,'scope':'Level1 fixed reservoirs; residualized whole-year bootstrap; consistency, not causal validation'})
 pd.DataFrame(rows).to_csv(T/'reservoir_cluster_and_influence.csv',index=False)

if __name__=='__main__':
 import sys
 for step in sys.argv[1:] or ['audit','models','wells','reservoir']:
  {'audit':spatial_audit,'models':model_baselines,'wells':fixed_wells,'reservoir':reservoir_checks}[step]()
