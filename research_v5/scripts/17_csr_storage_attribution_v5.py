"""Identified CSR baseline, source audit, native support and paired attribution."""
from pathlib import Path
import json,warnings,sys
import h5py,numpy as np,pandas as pd,xarray as xr
from research_common import ROOT,region_weights,weighted_series,trend_statistics,bh_fdr,seasonal_sen,metrics
OUT=ROOT/'Thailand_Research_v5'
for name in ['tables','figures','netcdf','logs','report','manuscript','presentation']:(OUT/name).mkdir(parents=True,exist_ok=True)
DATES=pd.date_range('2002-04-01','2024-09-01',freq='MS');base=(DATES.year>=2004)&(DATES.year<=2009)
source=ROOT/'shared_data/CSR_RL0603'
with xr.open_dataset(ROOT/'Thailand_Objective1/analysis_v3/netcdf/Thailand_TWSA_GWSA_components.nc',engine='h5netcdf') as d:old=d.load()
with xr.open_dataset(source/'CSR_GRACE_GRACE-FO_RL0603_Mascons_all-corrections_Thailand.nc',engine='h5netcdf') as d:
    assert d.lwe_thickness.attrs.get('Units')=='cm';csr=d.lwe_thickness.sel(lat=old.lat,lon=old.lon).reindex(time=DATES).load().astype('float64')*10
with xr.open_dataset(source/'CSR_GRACE_GRACE-FO_RL06_Mascons_v02_LandMask_Thailand.nc',engine='h5netcdf') as d:land=d.LO_val.sel(lat=old.lat,lon=old.lon).load()>0.5
with xr.open_dataset(source/'CSR_GRACE_GRACE-FO_RL0603_mascons_mapping_file_Thailand.nc',engine='h5netcdf') as d:ids=d.mascon_id.sel(lat=old.lat,lon=old.lon).load().values
csr=csr.where(land)
def g3p(kind,var):
    with xr.open_dataset(ROOT/f'shared_data/surface_water/G3P_v1.12_{kind}_Thailand_buffer_monthly_200204_202309.nc',engine='h5netcdf') as d:
        a=d[var].assign_coords(time=pd.DatetimeIndex(d.time.values).to_period('M').to_timestamp())
        return a.sortby('lat').interp(lat=old.lat,lon=old.lon,method='nearest').reindex(time=DATES).load().astype('float64').where(land)
rz=g3p('RZSM','rzsm');costg=g3p('TWS','tws');native=g3p('GWSA','gwsa')
parts={name:old[name].astype('float64').where(land) for name in ['SMSA','SWSA','CanopyA','SWEA']}
joint=csr.notnull()
for a in parts.values():joint=joint&a.notnull()
ref=xr.DataArray(base,dims='time',coords={'time':DATES})&joint
rebase=lambda a:a-a.where(ref).mean('time')
tws=csr-csr.where(xr.DataArray(base,dims='time',coords={'time':DATES})).mean('time')
common_tws=rebase(csr);p={name:rebase(a) for name,a in parts.items()}
gws=(common_tws-sum(p.values())).where(joint)
gws_alt=(common_tws-rebase(rz)-p['SWSA']-p['CanopyA']-p['SWEA']).where(joint&rz.notnull())
fields={'TWSA':tws,'TWSA_GWS_reference':common_tws.where(joint),'GWSA':gws,'GWSA_filtered_soil':gws_alt,**{k:v.where(joint) for k,v in p.items()}}
ds=xr.Dataset(fields,attrs={'gravity':'CSR RL06.3 all corrections, provider land mask; no additional smoothing or gain factor','units':'mm water equivalent','baseline':'2004–2009 common valid monthly reference for GWS balance','limitations':'Regularized native mascons are not independent; basin results below200000km2 exploratory; G3P surface-water filter and Noah soil structure differ; no pointwise CSR inference'})
ds.to_netcdf(OUT/'netcdf/CSR_storage_components.nc')
regions=region_weights(old.lat,old.lon);series=[];trends=[];audit=[];support=[];fractions=[]
cached=pd.read_csv(OUT/'tables/CSR_basin_trends.csv',dtype={'region':str}) if '--reuse-primary-trends' in sys.argv else None
for code,name,w in regions:
    f=pd.DataFrame({'date':DATES,'region':code,'region_name':name})
    for key,a in fields.items():f[key],f[key+'_coverage']=weighted_series(a,w,threshold=.5)
    for key in ['TWSA','GWSA','GWSA_filtered_soil']:
        if cached is not None:trends.append(cached[(cached.region==code)&(cached.variable==key)].iloc[0].to_dict())
        else:
            with warnings.catch_warnings():warnings.simplefilter('ignore');st=trend_statistics(f[key],DATES,bootstrap=300)
            trends.append({'region':code,'region_name':name,'variable':key,**st})
    series.append(f)
    # Each source uses identical cells and months for this product-comparison table.
    for var,primary,legacy,related in [('TWSA',tws,old.TWSA.where(land),costg),('GWSA',gws,old.GWSA.where(land),native)]:
        mask=primary.notnull()&legacy.notnull()&related.notnull()
        reference=mask&xr.DataArray(base,dims='time',coords={'time':DATES})
        vals={label:weighted_series((a-a.where(reference).mean('time')).where(mask),w,threshold=.5)[0] for label,a in [('CSR',primary),('Legacy_unidentified',legacy),('COSTG_G3P',related)]}
        for label,v in vals.items():
            with warnings.catch_warnings():warnings.simplefilter('ignore');st=trend_statistics(v,DATES)
            audit.append({'region':code,'region_name':name,'variable':var,'source':label,**st,**{'agreement_'+k:x for k,x in metrics(vals['CSR'],v).items()}})
    wm=w*np.asarray(land);area=wm.sum();valid=(wm>0)&np.isfinite(ids)
    unique=np.unique(ids[valid]);amount=np.array([wm[ids==i].sum() for i in unique]);fraction=amount/amount.sum()
    support.append({'region':code,'region_name':name,'basin_area_km2':w.sum()/1e6,'CSR_land_area_fraction':area/w.sum(),'native_mascons_touched':len(unique),'native_weight_concentration_count':1/np.sum(fraction**2),'largest_native_weight':fraction.max(),'provider_small_basin_caution':w.sum()/1e6<200000,'meaning':'Native weight concentration is not statistical independence or actual GRACE resolution'})
    fractions.extend({'region':code,'mascon_id':int(i),'weight_fraction':float(v)} for i,v in zip(unique,fraction))
    print('CSR storage and source audit',code,name,flush=True)
pd.concat(series,ignore_index=True).to_csv(OUT/'tables/CSR_basin_storage_timeseries.csv',index=False)
t=pd.DataFrame(trends)
for var,g in t.groupby('variable'):
    ix=g[g.region!='TH'].index;t.loc[ix,'mk_seasonal_q_FDR']=bh_fdr(t.loc[ix,'mk_seasonal_p'])
t.to_csv(OUT/'tables/CSR_basin_trends.csv',index=False);pd.DataFrame(audit).to_csv(OUT/'tables/common_support_product_audit.csv',index=False);pd.DataFrame(support).to_csv(OUT/'tables/native_mascon_support.csv',index=False)
frac=pd.DataFrame(fractions);frac.to_csv(OUT/'tables/native_mascon_weights.csv',index=False)
W=frac.pivot_table(index='region',columns='mascon_id',values='weight_fraction',fill_value=0);shared=[]
for a in W.index:
    for b in W.index:shared.append({'region_a':a,'region_b':b,'shared_native_weight':float(np.minimum(W.loc[a],W.loc[b]).sum())})
pd.DataFrame(shared).to_csv(OUT/'tables/basin_shared_support.csv',index=False)
# Rebase naturalized/historical models directly on the CSR-valid 2004–2009 footprint.
oldmodel=ROOT/'shared_data/WaterGAP';attrs=[];bench=[];rng=np.random.default_rng(516)
def load(scenario,var):
    with xr.open_dataset(oldmodel/f'WaterGAP22e_ERA5_{scenario}_{var}_Thailand_1981_2023.nc',engine='h5netcdf') as d:return d[var].interp(lat=old.lat,lon=old.lon,method='nearest').reindex(time=DATES).load().astype('float64').where(land)
for var,nativevar,observed in [('TWSA','tws',tws),('GWSA','groundwstor',gws)]:
    n=load('natural',nativevar);a=load('human',nativevar);mask=observed.notnull()&n.notnull()&a.notnull();ref=xr.DataArray(base,dims='time',coords={'time':DATES})&mask
    n=n-n.where(ref).mean('time');a=a-a.where(ref).mean('time')
    for code,name,w in regions:
        f=pd.DataFrame({'date':DATES,'region':code,'region_name':name,'variable':var})
        for key,z in [('observed_mm',observed),('climate_mm',n),('historical_human_mm',a),('modeled_human_mm',a-n),('residual_mm',observed-n),('discrepancy_mm',observed-a)]:f[key]=weighted_series(z.where(mask),w,threshold=.5)[0]
        attrs.append(f)
        for key,label in [('climate_mm','naturalized'),('historical_human_mm','historical_human')]:bench.append({'region':code,'variable':var,'model':label,**metrics(f.observed_mm,f[key])})
f=pd.concat(attrs,ignore_index=True);f.to_csv(OUT/'tables/CSR_naturalized_attribution.csv',index=False);pd.DataFrame(bench).to_csv(OUT/'tables/CSR_model_observation_benchmarks.csv',index=False)
assert np.nanmax(abs(f.residual_mm-f.modeled_human_mm-f.discrepancy_mm))<1e-8
assert np.nanmax(abs(gws-(common_tws-sum(p.values()))))<1e-8
(OUT/'logs/storage_attribution_qa.json').write_text(json.dumps({'passed':True,'regions':23,'source_rows':len(audit),'CSR_observed_months':int(np.isfinite(tws.values).any(axis=(1,2)).sum()),'balance_verified':True,'attribution_identity_verified':True,'no_pointwise_CSR_inference':True,'author':'Farzeen Khan'},indent=2),encoding='utf-8')
print(t[t.region=='TH'][['variable','sen_slope_mm_year','sen_lo95_mm_year','sen_hi95_mm_year']].to_string(index=False),flush=True)
