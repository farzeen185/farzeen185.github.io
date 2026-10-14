"""Objective 2: blocked climate reconstruction for TWSA/GWSA in all22basins.
Outputs distinguish climate predictions and candidate-human/unexplained residuals.
"""
import json,warnings,platform
import numpy as np
import pandas as pd
import xarray as xr
import joblib
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler,SplineTransformer
from sklearn.linear_model import ElasticNet,Ridge
from sklearn.ensemble import RandomForestRegressor
from research_common import ROOT,OBJ1,OBJ2,output,region_weights,weighted_series,metrics,trend_statistics,bh_fdr

dates=pd.date_range('2003-01-01','2024-09-01',freq='MS');T=len(dates)
with xr.open_dataset(ROOT/'Thailand_Objective2/outputs_advanced/Step_06_Final_Harmonized_Cube/netcdf/Climate_Inputs_2003_2024.nc') as d:
    cube=d.sortby('lat',ascending=False).sortby('lon').reindex(time=dates).load()
regions=region_weights(cube.lat,cube.lon)
storage=pd.read_csv(OBJ1/'tables/basin_storage_timeseries.csv',dtype={'region':str},parse_dates=['date'])
train=(dates.year<=2015)&(np.arange(T)>=24);val=(dates.year>=2016)&(dates.year<=2019);test=dates.year>=2020
folds=[((dates.year<=2010)&train,(dates.year>=2011)&(dates.year<=2013)),((dates.year<=2013)&train,(dates.year>=2014)&(dates.year<=2015))]
groups={'M0':['CHIRPS_P'],'M1':['CHIRPS_P','ET'],'M2':['CHIRPS_P','ET','ESA_CCI_SSM'],'M3':['CHIRPS_P','ET','ESA_CCI_RZSM'],'M4':['CHIRPS_P','ET','ESA_CCI_SSM','ESA_CCI_RZSM','MODIS_LST']}
def features(f,group,et):
    values={}
    for n in groups[group]:
        n=et if n=='ET' else n
        for lag in [0,1,2,3,6]:values[n+f'_lag{lag}']=f[n].shift(lag)
    return pd.DataFrame(values,index=dates)
def fit_model(kind,value):
    if kind=='ElasticNet':return make_pipeline(StandardScaler(),ElasticNet(alpha=value,l1_ratio=.5,max_iter=12000,tol=.001,random_state=731))
    if kind=='AdditiveSplines':return make_pipeline(StandardScaler(),SplineTransformer(n_knots=3,degree=2,include_bias=False,extrapolation='linear'),Ridge(alpha=value))
    return RandomForestRegressor(n_estimators=60,min_samples_leaf=value,max_features=.7,n_jobs=1,random_state=731)
parameters={'ElasticNet':[.1,1,10],'AdditiveSplines':[10,100,1000],'RandomForest':[5,12,24]}
def deseason(y):
    s=pd.Series(y,index=dates);ref=s[train];c=ref.groupby(ref.index.month).mean();return (s-pd.Series(dates.month,index=dates).map(c)).to_numpy()
rows=[];forecasts=[];parameterrows=[];ensembleweights=[];summary=[];coverage=[];residualtrends=[]
for regionno,(code,name,w) in enumerate(regions):
    f=pd.DataFrame(index=dates)
    for n in ['CHIRPS_P','GLEAM_ET','MODIS_ET','ESA_CCI_SSM','ESA_CCI_RZSM','MODIS_LST']:
        v,c=weighted_series(cube[n],w,threshold=.3 if n.startswith('ESA') else .5)
        f[n]=v;coverage.append({'region':code,'region_name':name,'variable':n,'finite_area_mean':float(np.mean(c)),'minimum_area_threshold':.3 if n.startswith('ESA') else .5,'strict70percent_months':int(np.sum(c>=.7))})
    f=f.join(storage[storage.region==code].set_index('date')[['TWSA','GWSA','GWSA_filtered_soil_sensitivity','G3P_GWSA_benchmark','GLDAS_land_storage_anomaly']])
    matrices={(et,g):features(f,g,et) for et in ['GLEAM_ET','MODIS_ET'] for g in groups}
    complete=matrices[('GLEAM_ET','M4')].notna().all(axis=1).to_numpy()&matrices[('MODIS_ET','M4')].notna().all(axis=1).to_numpy();complete[:24]=False
    for variable in ['TWSA','GWSA']:
        y=f[variable].to_numpy();common=complete&np.isfinite(y);fit=common&train;predictions={};rank=[]
        if fit.sum()<48:
            summary.append({'region':code,'region_name':name,'variable':variable,'status':'insufficient complete-case training support','n_train':int(fit.sum())});continue
        # Direct GRACE/GWS target includes any human influences during training; no natural-counterfactual claim.
        for et in ['GLEAM_ET','MODIS_ET']:
            flux=(f.CHIRPS_P-f[et]).to_numpy();candidates=[]
            for tau in np.geomspace(.5,120 if variable=='GWSA' else 60,64):
                decay=np.exp(-1/tau);state=0.;s=np.full(T,np.nan)
                for i,v in enumerate(flux):
                    if not np.isfinite(v):state=np.nan;continue
                    if not np.isfinite(state):continue
                    state=decay*state+tau*(1-decay)*v;s[i]=state
                ok=fit&np.isfinite(s)
                if ok.sum()<48:continue
                sm,ym=s[ok].mean(),y[ok].mean();beta=max(0.,float(np.dot(s[ok]-sm,y[ok]-ym)/np.dot(s[ok]-sm,s[ok]-sm)));intercept=ym-beta*sm;p=beta*s+intercept;p[:24]=np.nan
                candidates.append((np.mean((y[ok]-p[ok])**2),tau,beta,intercept,p))
            if candidates:
                _,tau,beta,offset,p=min(candidates,key=lambda x:x[0]);key='Physical_'+et;predictions[key]=p;parameterrows.append({'region':code,'variable':variable,'model':key,'parameter':tau,'beta':beta,'intercept_mm':offset})
        # Seasonal climatology supplies a meaningful independent-period baseline.
        c=f.loc[fit].groupby(f.loc[fit].index.month)[variable].mean();p=pd.Series(dates.month,index=dates).map(c).to_numpy(copy=True);p[:24]=np.nan;predictions['Seasonal_climatology']=p
        for et in ['GLEAM_ET','MODIS_ET']:
            for group in groups:
                if group=='M0' and et=='MODIS_ET':continue  # Identical P-only model is not duplicated.
                X=matrices[(et,group)];valid=X.notna().all(axis=1).to_numpy()
                for kind,values in parameters.items():
                    tuning=[]
                    for value in values:
                        errors=[]
                        for tr,va in folds:
                            tr=tr&common;va=va&common
                            if tr.sum()<30 or va.sum()<10:continue
                            m=fit_model(kind,value)
                            with warnings.catch_warnings():warnings.simplefilter('ignore');m.fit(X.loc[tr],y[tr])
                            errors.extend((y[va]-m.predict(X.loc[va]))**2)
                        if errors:tuning.append((float(np.mean(errors)),value))
                    if not tuning:continue
                    _,value=min(tuning);m=fit_model(kind,value)
                    with warnings.catch_warnings():warnings.simplefilter('ignore');m.fit(X.loc[fit],y[fit])
                    p=np.full(T,np.nan);p[valid]=m.predict(X.loc[valid]);p[:24]=np.nan;key=f'{kind}_{group}_{et}';predictions[key]=p
                    parameterrows.append({'region':code,'variable':variable,'model':key,'parameter':value,'n_train':int(fit.sum())});joblib.dump(m,output(OBJ2,'models',f'{code}_{variable}_{key}.joblib'),compress=3)
        for key,p in predictions.items():
            for period,mask in [('Train',train),('Validation',val),('Test',test)]:
                ok=mask&common;row={'region':code,'region_name':name,'variable':variable,'model':key,'period':period,'reference':'target_storage',**metrics(y[ok],p[ok])};rows.append(row)
                if period=='Validation':rank.append(row)
                if variable=='TWSA':rows.append({'region':code,'region_name':name,'variable':variable,'model':key,'period':period,'reference':'GLDAS_land_storage_benchmark',**metrics(f.GLDAS_land_storage_anomaly.to_numpy()[ok],p[ok])})
                else:rows.append({'region':code,'region_name':name,'variable':variable,'model':key,'period':period,'reference':'G3P_related_GWS_product',**metrics(f.G3P_GWSA_benchmark.to_numpy()[ok],p[ok])})
        ranking=pd.DataFrame(rank).set_index('model');threshold=ranking.loc['Seasonal_climatology','NSE']
        pool=ranking[(ranking.index!='Seasonal_climatology')&(ranking.n>=10)&(ranking.NSE>max(0,threshold))].sort_values('RMSE_mm').head(5);credible=True
        if pool.empty:pool=ranking[(ranking.index!='Seasonal_climatology')&(ranking.n>=10)].sort_values('RMSE_mm').head(1);credible=False
        if pool.empty:
            summary.append({'region':code,'region_name':name,'variable':variable,'status':'no independent validation support','n_train':int(fit.sum())});continue
        weights=1/np.maximum(pool.RMSE_mm.to_numpy()**2,1e-6);weights/=weights.sum();members=list(pool.index);stack=np.stack([predictions[k] for k in members]);p=np.sum(stack*weights[:,None],axis=0);spread=np.sqrt(np.sum((stack-p)**2*weights[:,None],axis=0))
        # Publish reconstruction only through the last observed target, not unlabelled projections.
        last_observed=np.flatnonzero(np.isfinite(y))[-1];p[last_observed+1:]=np.nan;spread[last_observed+1:]=np.nan
        vmask=val&common&np.isfinite(p);q=float(np.nanquantile(abs(y[vmask]-p[vmask]),.9))
        for key,weight in zip(members,weights):ensembleweights.append({'region':code,'variable':variable,'model':key,'weight':weight,'credible_validation':credible})
        out=pd.DataFrame({'date':dates,'region':code,'region_name':name,'variable':variable,'observed_mm':y,'climate_mm':p,'unexplained_residual_mm':y-p,'candidate_human_residual_mm':y-p,'structural_sd_mm':spread,'empirical_lower_mm':p-q,'empirical_upper_mm':p+q,'common_support':common})
        if variable=='TWSA':out['benchmark_mm']=f.GLDAS_land_storage_anomaly.to_numpy();out['benchmark_name']='GLDAS Noah land storage (not full TWS truth)'
        else:out['benchmark_mm']=f.G3P_GWSA_benchmark.to_numpy();out['benchmark_name']='G3P related GWS product (not independent)';out['soil_product_sensitivity_mm']=np.abs(f.GWSA-f.GWSA_filtered_soil_sensitivity).to_numpy()
        forecasts.append(out)
        for period,mask in [('Train',train),('Validation',val),('Test',test)]:
            ok=mask&common;scores=metrics(y[ok],p[ok]);deseason_scores=metrics(deseason(y)[ok],deseason(p)[ok]);bscore=metrics(out.benchmark_mm.to_numpy()[ok],p[ok]);cover=float(np.mean(abs(y[ok]-p[ok])<=q)) if ok.any() else np.nan
            summary.append({'region':code,'region_name':name,'variable':variable,'period':period,'status':'estimated','credible_validation':credible,'benchmark_name':out.benchmark_name.iloc[0],**scores,'deseasonalized_NSE':deseason_scores['NSE'],'deseasonalized_r':deseason_scores['r'],'benchmark_NSE':bscore['NSE'],'benchmark_r':bscore['r'],'empirical_band_coverage':cover,'validation_error_q90_mm':q,'n_train':int(fit.sum())})
        for component,values in [('climate',np.where(np.isfinite(y),p,np.nan)),('unexplained_residual',y-p)]:
            with warnings.catch_warnings():warnings.simplefilter('ignore');st=trend_statistics(values,dates,bootstrap=200)
            residualtrends.append({'region':code,'region_name':name,'variable':variable,'component':component,**st})
        print(f'Models {regionno+1}/23 {name} {variable}: {len(predictions)} configurations; train/validation/test {sum(common&train)}/{sum(common&val)}/{sum(common&test)}; ensemble {len(members)}',flush=True)
pd.DataFrame(rows).to_csv(output(OBJ2,'tables','all_model_validation.csv'),index=False)
pd.DataFrame(parameterrows).to_csv(output(OBJ2,'tables','model_parameters.csv'),index=False)
pd.DataFrame(ensembleweights).to_csv(output(OBJ2,'tables','ensemble_weights.csv'),index=False)
summary=pd.DataFrame(summary);summary.to_csv(output(OBJ2,'tables','ensemble_validation.csv'),index=False)
forecast=pd.concat(forecasts,ignore_index=True);forecast.to_csv(output(OBJ2,'tables','basin_climate_residual_timeseries.csv'),index=False)
trends=pd.DataFrame(residualtrends)
for (variable,component),g in trends.groupby(['variable','component']):
    i=g[g.region!='TH'].index;trends.loc[i,'mk_seasonal_q_FDR']=bh_fdr(trends.loc[i,'mk_seasonal_p'])
trends.to_csv(output(OBJ2,'tables','climate_residual_Sen_MannKendall.csv'),index=False)
pd.DataFrame(coverage).to_csv(output(OBJ2,'tables','predictor_coverage.csv'),index=False)
variables=['TWSA','GWSA'];codes=[c for c,n,w in regions];fields=['observed_mm','climate_mm','unexplained_residual_mm','structural_sd_mm','empirical_lower_mm','empirical_upper_mm']
arrays={}
for field in fields:
    z=np.full((2,len(codes),T),np.nan)
    for a,var in enumerate(variables):
        for b,code in enumerate(codes):
            g=forecast[(forecast.variable==var)&(forecast.region==code)]
            if len(g)==T:z[a,b]=g[field].values
    arrays[field]=( ('variable','region','time'),z)
ds=xr.Dataset(arrays,coords={'variable':variables,'region':codes,'time':dates},attrs={'interpretation':'Climate-associated reconstruction, not proven natural counterfactual. Residual is candidate human-related plus unresolved error.','training':'2005–2015 after2003–2004spinup','validation':'2016–2019','test':'2020–2024 forTWS;2020–2023 forGWS','coverage':'Core forcing minimum50%basinarea; soil30%; coastal basins exploratory','GLDAS':'Noah has no groundwater storage; only TWS reconstruction benchmarked to its land compartments','uncertainty':'Empirical validation-error bands and structural spread; no complete observational error propagation'})
for field in ds:ds[field].attrs={'units':'mm'}
ds.to_netcdf(output(OBJ2,'netcdf','basin_climate_human_candidate_components.nc'))
status={'targets':variables,'regions_attempted':len(regions),'target_region_ensembles':int(forecast.groupby(['region','variable']).ngroups),'model_configurations':int(pd.DataFrame(rows).groupby(['region','variable','model']).ngroups),'models':'constant-memory physical; ElasticNet; additive quadratic splines; RandomForest','human_component':'candidate human-associated/unexplained residual, pending groundwater + irrigation association evidence; not causal proof','GLDAS_GWS_validation':'unavailable in Noah; use actual groundwater levels, not fake Noah GWS','software':{'python':platform.python_version()}}
output(OBJ2,'logs','objective2_status.json').write_text(json.dumps(status,indent=2),encoding='utf-8');print(json.dumps(status,indent=2),flush=True)
