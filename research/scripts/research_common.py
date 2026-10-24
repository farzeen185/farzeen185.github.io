"""Shared, unit-explicit utilities for the three-objective research workflow."""
from pathlib import Path
import os
import numpy as np
import pandas as pd
import xarray as xr
from scipy.stats import theilslopes
import pymannkendall as mk

ROOT=Path(os.environ.get('TWSA_RESEARCH_ROOT',Path(__file__).resolve().parents[1])).resolve()
OBJ1=ROOT/'Thailand_Objective1/analysis_v3';OBJ2=ROOT/'Thailand_Objective2/analysis_v3'
def output(root,kind,name):
    p=root/kind/name;p.parent.mkdir(parents=True,exist_ok=True);return p
def region_weights(lat,lon):
    base=ROOT/'Thailand_Objective1/outputs/tables'
    n=pd.read_csv(base/'Thailand_National_GRACE_Fractional_Weights.csv')
    b=pd.read_csv(base/'Thailand_22_Basins_GRACE_Fractional_Weights.csv',dtype={'BASIN_CODE':str})
    regions=[]
    for code,name,g in [('TH','Thailand',n)]+[(code,g.BASIN_NAME.iloc[0],g) for code,g in b.groupby('BASIN_CODE')]:
        w=np.zeros((len(lat),len(lon)));w[g.row.astype(int),g.col.astype(int)]=g.intersection_area_m2
        regions.append((code,name,w))
    return regions
def weighted_series(a,w,threshold=.3):
    z=a.values if isinstance(a,xr.DataArray) else np.asarray(a)
    good=np.isfinite(z);area=np.sum(good*w,axis=(1,2));num=np.sum(np.where(good,z,0)*w,axis=(1,2))
    v=np.divide(num,area,out=np.full(len(z),np.nan),where=area>0);coverage=area/w.sum();v[coverage<threshold]=np.nan
    return v,coverage
def metrics(y,p):
    y=np.asarray(y,float);p=np.asarray(p,float);good=np.isfinite(y)&np.isfinite(p);a,b=y[good],p[good]
    base={'n':int(good.sum())}
    if len(a)<8 or np.std(a)==0:return {**base,**{n:np.nan for n in ['r','NSE','RMSE_mm','MAE_mm','bias_mm','amplitude_ratio']}}
    return {**base,'r':float(np.corrcoef(a,b)[0,1]),'NSE':float(1-np.sum((a-b)**2)/np.sum((a-a.mean())**2)),'RMSE_mm':float(np.sqrt(np.mean((a-b)**2))),'MAE_mm':float(np.mean(abs(a-b))),'bias_mm':float(np.mean(b-a)),'amplitude_ratio':float(np.std(b)/np.std(a))}
def bh_fdr(p):
    p=np.asarray(p,float);out=np.full(p.shape,np.nan);good=np.isfinite(p);z=p[good];order=np.argsort(z);q=np.minimum.accumulate((z[order]*len(z)/np.arange(1,len(z)+1))[::-1])[::-1];back=np.empty(len(z));back[order]=np.minimum(q,1);out[good]=back;return out
def seasonal_sen(y,dates):
    y=np.asarray(y,float);dates=pd.DatetimeIndex(dates);slopes=[]
    for month in range(1,13):
        ix=np.flatnonzero((dates.month==month)&np.isfinite(y))
        if len(ix)>1:
            i,j=np.triu_indices(len(ix),1);slopes.extend(((y[ix[j]]-y[ix[i]])/(dates.year[ix[j]]-dates.year[ix[i]])).tolist())
    return float(np.median(slopes)) if slopes else np.nan
def trend_statistics(y,dates,bootstrap=0,seed=731):
    y=np.asarray(y,float);dates=pd.DatetimeIndex(dates);good=np.isfinite(y);n=int(good.sum());base={'n_months':n}
    if n<24:return {**base,'sen_slope_mm_year':np.nan,'mk_original_p':np.nan,'mk_seasonal_p':np.nan,'status':'insufficient observations'}
    beta=seasonal_sen(y,dates);t=(dates-dates[0]).days.to_numpy()/365.25
    raw=theilslopes(y[good],t[good]);original=mk.original_test(y)
    full=pd.Series(y,index=dates).reindex(pd.date_range(f'{dates.year.min()}-01-01',f'{dates.year.max()}-12-01',freq='MS'))
    seasonal=mk.seasonal_test(full.to_numpy(),period=12)
    annual=pd.Series(y,index=dates).resample('YS').agg(['mean','count']);annual.loc[annual['count']<8,'mean']=np.nan
    annualgood=annual['mean'].notna()
    ap=mk.original_test(annual.loc[annualgood,'mean'].values).p if annualgood.sum()>=8 else np.nan
    hr=np.nan
    # Never silently compress missing calendar years for the serial-correlation test.
    if annualgood.any():
        sub=annual.loc[annualgood.index[annualgood][0]:annualgood.index[annualgood][-1]]
        if sub['mean'].notna().all() and len(sub)>=8:
            hr=mk.hamed_rao_modification_test(sub['mean'].values,lag=min(3,len(sub)-2)).p
    result={**base,'start':str(dates[good][0].date()),'end':str(dates[good][-1].date()),'sen_slope_mm_year':beta,'raw_sen_slope_mm_year':float(raw.slope),'mk_original_p':float(original.p),'mk_seasonal_p':float(seasonal.p),'mk_seasonal_tau':float(seasonal.Tau),'annual_mk_p':float(ap),'annual_hamed_rao_p':float(hr),'n_annual':int(annualgood.sum()),'direction':'increasing' if beta>0 else 'decreasing' if beta<0 else 'flat','status':'estimated','significance_note':'Seasonal MK is unadjusted for serial dependence; bootstrap slope intervals and FDR are supplied separately.'}
    if bootstrap:
        # Calendar-year block bootstrap of deseasonalized, detrended residuals.
        residual=pd.Series(y-beta*t,index=dates);clim=residual.groupby(residual.index.month).mean();residual=residual-pd.Series(dates.month,index=dates).map(clim)
        padded=residual.reindex(full.index).values.reshape(-1,12);rng=np.random.default_rng(seed);slopes=[]
        start=full.index[0];indices=full.index.get_indexer(dates)
        for _ in range(bootstrap):
            chosen=rng.integers(0,len(padded),len(padded));e=padded[chosen].ravel()[indices]
            reconstructed=beta*t+pd.Series(dates.month).map(clim).to_numpy()+e
            slopes.append(seasonal_sen(reconstructed,dates))
        lo,hi=np.nanpercentile(slopes,[2.5,97.5]);result.update(sen_lo95_mm_year=float(lo),sen_hi95_mm_year=float(hi),bootstrap_replicates=bootstrap)
    return result
