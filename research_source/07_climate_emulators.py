"""Train on naturalized storage only. Meteorological predictors never include GRACE."""
import json,warnings
import numpy as np,pandas as pd,joblib
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler,SplineTransformer
from sklearn.linear_model import Ridge,ElasticNet
from sklearn.ensemble import RandomForestRegressor
from research_common import ROOT,metrics
OUT=ROOT/'Thailand_Objective2/analysis_v4';d=pd.read_csv(OUT/'tables/naturalized_attribution_timeseries.csv',dtype={'region':str},parse_dates=['date'])
scores=[];predictions=[];weights=[]
def model(kind,v):
    if kind=='Ridge':return make_pipeline(StandardScaler(),Ridge(alpha=v))
    if kind=='ElasticNet':return make_pipeline(StandardScaler(),ElasticNet(alpha=v,l1_ratio=.5,max_iter=10000))
    if kind=='Splines':return make_pipeline(StandardScaler(),SplineTransformer(n_knots=3,degree=2,include_bias=False),Ridge(alpha=v))
    return RandomForestRegressor(n_estimators=80,min_samples_leaf=v,max_features=.8,n_jobs=1,random_state=842)
for (code,var),f in d.groupby(['region','variable'],sort=False):
    f=f.sort_values('date').reset_index(drop=True);dates=pd.DatetimeIndex(f.date);y=f.natural_continuous_mm.to_numpy();train=(dates.year>=1991)&(dates.year<=2009);val=(dates.year>=2010)&(dates.year<=2015);test=dates.year>=2016
    X=pd.DataFrame(index=f.index)
    for name in ['precipitation_mm_day','potential_ET_mm_day']:
        for lag in [0,1,2,3,6,12]:X[name+str(lag)]=f[name].shift(lag)
        for tau in [1,3,6,12,24]:X[name+'_memory'+str(tau)]=f[name].ewm(alpha=1-np.exp(-1/tau),adjust=True).mean()
    for harmonic in [1,2]:
        X['sin'+str(harmonic)]=np.sin(dates.month*2*np.pi/12*harmonic);X['cos'+str(harmonic)]=np.cos(dates.month*2*np.pi/12*harmonic)
    valid=np.isfinite(y)&X.notna().all(axis=1).to_numpy();train&=valid;val&=valid;test&=valid
    if train.sum()<100 or val.sum()<24:raise ValueError(f'Insufficient naturalized model support {code}/{var}')
    c=pd.Series(y[train],index=dates[train]).groupby(dates[train].month).mean();season=np.array([c.get(m,np.nan) for m in dates.month]);pred={'Climatology':season};tuned=[]
    folds=[((dates.year>=1991)&(dates.year<=2000),(dates.year>=2001)&(dates.year<=2004)),((dates.year>=1991)&(dates.year<=2004),(dates.year>=2005)&(dates.year<=2009))]
    for kind,grid in {'Ridge':[1,10,100],'ElasticNet':[.1,1,10],'Splines':[10,100,1000],'RandomForest':[3,8,16]}.items():
        loss=[]
        for v in grid:
            errors=[]
            for fit,evaluate in folds:
                fit&=valid;evaluate&=valid;m=model(kind,v)
                with warnings.catch_warnings():warnings.simplefilter('ignore');m.fit(X.loc[fit],y[fit])
                errors.extend((m.predict(X.loc[evaluate])-y[evaluate])**2)
            loss.append((np.mean(errors),v))
        v=min(loss)[1];m=model(kind,v)
        with warnings.catch_warnings():warnings.simplefilter('ignore');m.fit(X.loc[train],y[train])
        p=np.full(len(y),np.nan);p[valid]=m.predict(X.loc[valid]);p[dates.year<1991]=np.nan;pred[kind]=p
        joblib.dump(m,OUT/'models'/f'{code}_{var}_{kind}.joblib',compress=3)
    for key,p in pred.items():
        for period,mask in [('Train',train),('Validation',val),('Test',test)]:
            m=metrics(y[mask],p[mask]);anom=metrics((y-season)[mask],(p-season)[mask]);baseerror=np.sum((y[mask]-season[mask])**2)
            row={'region':code,'region_name':f.region_name.iloc[0],'variable':var,'model':key,'period':period,**m,'deseasonalized_NSE':anom['NSE'],'skill_vs_training_climatology':1-np.sum((y[mask]-p[mask])**2)/baseerror,'target':'Naturalized WaterGAP storage; emulator verification, not observational validation'};scores.append(row)
            if period=='Validation' and key!='Climatology':tuned.append(row)
    rank=pd.DataFrame(tuned);good=rank[(rank.skill_vs_training_climatology>0)&(rank.deseasonalized_NSE>0)].sort_values('RMSE_mm').head(3);credible=not good.empty
    if good.empty:good=rank.sort_values('RMSE_mm').head(1)
    weight=1/np.maximum(good.RMSE_mm.to_numpy()**2,1e-8);weight/=weight.sum();p=np.sum(np.stack([pred[k] for k in good.model])*weight[:,None],axis=0)
    for key,w in zip(good.model,weight):weights.append({'region':code,'variable':var,'model':key,'weight':w,'validation_support':credible})
    for period,mask in [('Train',train),('Validation',val),('Test',test)]:
        a=metrics(y[mask],p[mask]);b=metrics((y-season)[mask],(p-season)[mask]);scores.append({'region':code,'region_name':f.region_name.iloc[0],'variable':var,'model':'Ensemble','period':period,**a,'deseasonalized_NSE':b['NSE'],'skill_vs_training_climatology':1-np.sum((y[mask]-p[mask])**2)/np.sum((y[mask]-season[mask])**2),'validation_support':credible,'target':'Naturalized WaterGAP emulator verification'})
    predictions.append(pd.DataFrame({'date':dates,'region':code,'variable':var,'naturalized_target_mm':y,'emulator_mm':p,'climatology_mm':season}))
    print('Emulator',code,var,'test NSE',round(a['NSE'],3),'deseason',round(b['NSE'],3),flush=True)
pd.DataFrame(scores).to_csv(OUT/'tables/climate_emulator_validation.csv',index=False);pd.DataFrame(weights).to_csv(OUT/'tables/climate_emulator_weights.csv',index=False);pd.concat(predictions).to_csv(OUT/'tables/climate_emulator_timeseries.csv',index=False)
(OUT/'logs/emulator_method.json').write_text(json.dumps({'training':'1991–2009','warmup':'1981–1990','validation':'2010–2015','test':'2016–2023','target':'Naturalized WaterGAP; no GRACE/groundwater fitting','primary_attribution_baseline':'Published naturalized hydrological simulation; statistical emulators quantify ability to reproduce it, and do not replace it solely for high seasonal r','predictors':'Meteorological P/PET in mean mm/day; causal lags/memory and seasonal harmonics; no calendar-year trend or observed-storage lag'},indent=2),encoding='utf-8')
