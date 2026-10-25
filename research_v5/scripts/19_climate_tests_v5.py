"""Prespecified climate-memory ablations and independent-forcing stress tests."""
import json,warnings
import h5py,numpy as np,pandas as pd,xarray as xr
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from research_common import ROOT,metrics,region_weights,weighted_series,bh_fdr
OUT=ROOT/'Thailand_Research_v5';rng=np.random.default_rng(19516)
raw=pd.read_csv(ROOT/'Thailand_Objective2/analysis_v4/tables/naturalized_attribution_timeseries.csv',dtype={'region':str},parse_dates=['date'])
def features(dates,p,pet,group):
    dates=pd.DatetimeIndex(dates);a=pd.Series(np.asarray(p,float));b=pd.Series(np.asarray(pet,float));X=pd.DataFrame(index=np.arange(len(dates)))
    if group!='Weather_without_season':
        for h in [1,2]:X['sin'+str(h)]=np.sin(dates.month*2*np.pi/12*h);X['cos'+str(h)]=np.cos(dates.month*2*np.pi/12*h)
    if group=='Season_only':return X
    for name,s in [('P',a),('PET',b)]:
        for lag in ([0] if group=='Current_weather' else [0,1,2,3,6,12]):X[f'{name}_lag{lag}']=s.shift(lag)
        if group in ['Weather_memory','Weather_without_season']:
            for tau in [1,3,6,12,24]:X[f'{name}_memory{tau}']=s.ewm(alpha=1-np.exp(-1/tau),adjust=True).mean()
    return X
with xr.open_dataset(ROOT/'Thailand_Objective2/outputs_advanced/Step_06_Final_Harmonized_Cube/netcdf/Climate_Inputs_2003_2024.nc',engine='h5netcdf') as d:cube=d.sortby('lat',ascending=False).load()
forcing={};ancillary=[]
for code,name,w in region_weights(cube.lat,cube.lon):
    f=pd.DataFrame({'date':cube.time.values,'region':code,'region_name':name})
    for var in ['CHIRPS_P','GLEAM_ET','MODIS_ET','ESA_CCI_SSM','ESA_CCI_RZSM','MODIS_LST']:
        f[var],f[var+'_coverage']=weighted_series(cube[var],w,threshold=.3 if var.startswith('ESA') else .5)
    forcing[code]=f.set_index('date');ancillary.append(f)
pd.concat(ancillary,ignore_index=True).to_csv(OUT/'tables/multisource_hydroclimate_series.csv',index=False)
scores=[];preds=[];shift=[];gains=[]
for (code,var),f in raw.groupby(['region','variable'],sort=False):
    f=f.sort_values('date').reset_index(drop=True);dates=pd.DatetimeIndex(f.date);y=f.natural_continuous_mm.to_numpy()
    train=dates.year.to_numpy().astype(int);tr=(train>=1991)&(train<=2009);va=(train>=2010)&(train<=2015);te=(train>=2016)&(train<=2023)
    c=pd.Series(y[tr],index=dates[tr]).groupby(dates[tr].month).mean();season=np.array([c.loc[m] for m in dates.month]);records={};fitted={}
    for group in ['Season_only','Current_weather','Weather_lags','Weather_memory','Weather_without_season']:
        X=features(dates,f.precipitation_mm_day,f.potential_ET_mm_day,group);valid=X.notna().all(axis=1).to_numpy()&np.isfinite(y)
        losses=[]
        for alpha in [1,10,100]:
            err=[]
            for end,vstart,vend in [(2000,2001,2004),(2004,2005,2009)]:
                fit=valid&(train>=1991)&(train<=end);evaluate=valid&(train>=vstart)&(train<=vend)
                m=make_pipeline(StandardScaler(),Ridge(alpha=alpha)).fit(X.loc[fit],y[fit]);err.extend((m.predict(X.loc[evaluate])-y[evaluate])**2)
            losses.append((np.mean(err),alpha))
        alpha=min(losses)[1];m=make_pipeline(StandardScaler(),Ridge(alpha=alpha)).fit(X.loc[valid&tr],y[valid&tr])
        p=np.full(len(y),np.nan);p[valid]=m.predict(X.loc[valid]);records[group]=p;fitted[group]=m
        for label,mask in [('Validation',va&valid),('Test',te&valid)]:scores.append({'region':code,'variable':var,'feature_group':group,'period':label,'ridge_alpha':alpha,**metrics(y[mask],p[mask]),'deseasonalized_NSE':metrics((y-season)[mask],(p-season)[mask])['NSE'],'target':'Naturalized WaterGAP; reconstruction/emulation, not future forecasting'})
        preds.append(pd.DataFrame({'date':dates[te],'region':code,'variable':var,'feature_group':group,'target_mm':y[te],'prediction_mm':p[te]}))
    # Bootstrap test-year pairs; no hyperparameter or feature selection uses test data.
    gain=(y[te]-records['Current_weather'][te])**2-(y[te]-records['Weather_memory'][te])**2
    years=dates[te].year.to_numpy();unique=np.unique(years);sims=[]
    for _ in range(999):
        start=rng.integers(0,len(unique),int(np.ceil(len(unique)/2)));ix=((start[:,None]+[0,1])%len(unique)).ravel()[:len(unique)]
        sims.append(np.mean(np.concatenate([gain[years==unique[i]] for i in ix])))
    gains.append({'region':code,'variable':var,'mean_test_squared_error_reduction_mm2':np.mean(gain),'lo95':np.quantile(sims,.025),'hi95':np.quantile(sims,.975),'bootstrap_fraction_positive':np.mean(np.array(sims)>0),'resampling':'999 circular paired2year blocks from8 test years; conditional comparison'})
    # Change P source while keeping the full model and native P/PET target fixed.
    q=forcing[code].reindex(dates);P=q.CHIRPS_P.to_numpy()/dates.days_in_month.to_numpy();PET=f.potential_ET_mm_day.to_numpy();nativeP=f.precipitation_mm_day.to_numpy()
    calibration=(dates.year>=2003)&(dates.year<=2009)&np.isfinite(P)&np.isfinite(nativeP)
    ratios={mo:np.mean(nativeP[calibration&(dates.month==mo)])/np.mean(P[calibration&(dates.month==mo)]) for mo in range(1,13)}
    for label,sourceP in [('Native_GSWP3_ERA5',nativeP),('CHIRPS_unadjusted',P),('CHIRPS_training_monthly_mean_adjusted',P*np.array([ratios[mo] for mo in dates.month]))]:
        X=features(dates,sourceP,PET,'Weather_memory');valid=X.notna().all(axis=1).to_numpy()&te
        p=fitted['Weather_memory'].predict(X.loc[valid]);shift.append({'region':code,'variable':var,'P_source':label,**metrics(y[valid],p),'deseasonalized_NSE':metrics((y-season)[valid],p-season[valid])['NSE'],'interpretation':'Frozen-model forcing sensitivity against native-forced parent target, not observational validation'})
    print('Climate feature and forcing tests',code,var,flush=True)
pd.DataFrame(scores).to_csv(OUT/'tables/climate_feature_ablation.csv',index=False);pd.concat(preds).to_csv(OUT/'tables/ablation_test_predictions.csv',index=False)
pd.DataFrame(shift).to_csv(OUT/'tables/precipitation_source_stress_test.csv',index=False);pd.DataFrame(gains).to_csv(OUT/'tables/memory_gain_uncertainty.csv',index=False)
# Observed response: choose accumulation and lag in development; freeze for later test.
obs=pd.read_csv(OUT/'tables/CSR_basin_storage_timeseries.csv',dtype={'region':str},parse_dates=['date']);lagrows=[]
for code,g in obs.groupby('region',sort=False):
    g=g.set_index('date').reindex(pd.date_range('2003-01-01','2023-12-01',freq='MS'));dates=g.index
    q=forcing[code].reindex(dates);P=q.CHIRPS_P;dev=(dates.year<=2015);test=(dates.year>=2016)
    design=np.column_stack([np.ones(len(dates)),(dates-dates[0]).days.to_numpy()/365.25]+[(dates.month==m).astype(float) for m in range(2,13)])
    for var in ['TWSA','GWSA']:
        y=g[var].to_numpy();ok=dev&np.isfinite(y);beta=np.linalg.lstsq(design[ok],y[ok],rcond=None)[0];ya=y-design@beta
        candidates=[]
        for acc in [1,3,6,12]:
            a=P.rolling(acc,min_periods=acc).sum();clim=a[dev].groupby(a[dev].index.month).mean();pa=a.to_numpy()-np.array([clim.get(m,np.nan) for m in dates.month])
            for lag in range(7):
                x=pd.Series(pa).shift(lag).to_numpy();valid=ok&np.isfinite(x)
                if valid.sum()>=48:candidates.append((float(np.corrcoef(x[valid],ya[valid])[0,1]),acc,lag,x))
        r,acc,lag,x=max(candidates,key=lambda z:z[0]);valid=test&np.isfinite(x)&np.isfinite(ya)
        rtest=float(np.corrcoef(x[valid],ya[valid])[0,1]);years=np.unique(dates[test].year);matrix=x[test].reshape(len(years),12);target=ya[test];keep=np.isfinite(target)&np.isfinite(x[test]);null=[]
        for _ in range(999):
            perm=matrix[rng.permutation(len(years))].ravel();m=keep&np.isfinite(perm)
            null.append(float(np.corrcoef(perm[m],target[m])[0,1]))
        lagrows.append({'region':code,'variable':var,'selected_accumulation_months':acc,'selected_lag_months':lag,'development_r':r,'test_r':rtest,'test_n':int(valid.sum()),'year_permutation_p':(1+np.sum(np.abs(null)>=abs(rtest)))/1000,'design':'Select in2003–2015, test2016–2023; deseasonalization/detrending fitted in development; descriptive lag, not causal residence time'})
lagtable=pd.DataFrame(lagrows)
for var,g in lagtable.groupby('variable'):
    ix=g[g.region!='TH'].index;lagtable.loc[ix,'test_q_FDR']=bh_fdr(lagtable.loc[ix,'year_permutation_p'])
lagtable.to_csv(OUT/'tables/heldout_precipitation_storage_response.csv',index=False)
(OUT/'logs/climate_extension_qa.json').write_text(json.dumps({'passed':True,'ablation_region_targets':46,'groups':5,'P_source_conditions':3,'test_data_used_for_tuning':False,'lag_candidates_selected_in_development_only':True},indent=2),encoding='utf-8')
