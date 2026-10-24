"""Actual-head consistency checks; no groundwater-head to storage coefficient is invented."""
import json,warnings
import numpy as np,pandas as pd
from scipy.stats import pearsonr
from research_common import ROOT,metrics
OUT=ROOT/'Thailand_Objective2/analysis_v4';old=ROOT/'Thailand_Objective2/analysis_v3'
f=pd.read_csv(OUT/'tables/naturalized_attribution_timeseries.csv',dtype={'region':str},parse_dates=['date'])
indices=pd.read_csv(old/'tables/basin_groundwater_observation_indices.csv',dtype={'region':str},parse_dates=['date'])
rng=np.random.default_rng(412);rows=[]
def annual(s):
    s=s.dropna();a=s.resample('YS').agg(['mean','count']);a.loc[a['count']<8,'mean']=np.nan
    if len(s):
        if s.index.min().month>1:a.loc[a.index.year==s.index.min().year,'mean']=np.nan
        if s.index.max().month<12:a.loc[a.index.year==s.index.max().year,'mean']=np.nan
    return a['mean']
def correlation(a,b):
    if len(a)<6 or np.std(a)==0 or np.std(b)==0:return np.nan
    return float(np.corrcoef(a,b)[0,1])
def regress_out(x,z):
    Z=np.column_stack([np.ones(len(z)),z]);return x-Z@np.linalg.lstsq(Z,x,rcond=None)[0]
for (code,var),g in f.groupby(['region','variable']):
    g=g.set_index('date')
    for component in ['observed_mm','residual_mm']:
        for quality in ['retained_flags','exclude_flagged_sensitivity','fixed_2013_2022_panel']:
            q=indices[(indices.region==code)&(indices.interval=='YS')&(indices.quality==quality)].set_index('date').well_head_z
            z=pd.concat([q.rename('head'),annual(g[component]).rename('storage'),annual(g.climate_mm).rename('climate')],axis=1,sort=True).dropna();n=len(z)
            r=correlation(z['head'],z.storage);partial=correlation(regress_out(z['head'],z.climate),regress_out(z.storage,z.climate)) if n>=8 else np.nan
            years=z.index.year.to_numpy();detrended=correlation(regress_out(z['head'],years),regress_out(z.storage,years)) if n>=8 else np.nan
            differences=z.diff().loc[np.r_[False,np.diff(years)==1]] if n else z.copy();diff_r=correlation(differences['head'],differences.storage)
            boot=[]
            if np.isfinite(r):
                values=z[['head','storage']].to_numpy()
                for _ in range(250):
                    starts=rng.integers(0,n,int(np.ceil(n/2)));ix=((starts[:,None]+[0,1])%n).ravel()[:n];b=values[ix];v=correlation(b[:,0],b[:,1])
                    if np.isfinite(v):boot.append(v)
            lo,hi=np.quantile(boot,[.025,.975]) if boot else [np.nan,np.nan]
            rows.append({'region':code,'variable':var,'component':component,'quality':quality,'interval':'YS','scope':'all_overlap','n':n,'r':r,'r_lo95':lo,'r_hi95':hi,'partial_r_controlling_natural_climate':partial,'detrended_r':detrended,'contiguous_annual_change_r':diff_r,'n_contiguous_changes':len(differences),'evidence_role':'Groundwater consistency' if var=='GWSA' else 'Indirect groundwater-part consistency only; cannot validate total human TWS','interpretation':'Descriptive association; mixed aquifers, sparse sampling and model error preclude causal pumping validation'})
pd.DataFrame(rows).to_csv(OUT/'tables/groundwater_attribution_evidence.csv',index=False)
associations=[]
for (code,var),g in f.groupby(['region','variable']):
    z=g[['residual_mm','modeled_human_mm','discrepancy_mm']].dropna()
    associations.append({'region':code,'variable':var,'n_months':len(z),'residual_vs_modeled_human_r':correlation(z.residual_mm,z.modeled_human_mm),'residual_sd_mm':z.residual_mm.std(),'discrepancy_sd_mm':z.discrepancy_mm.std(),'role':'Paired model experiment supports interpretation, not independent measured pumping'})
pd.DataFrame(associations).to_csv(OUT/'tables/paired_model_evidence.csv',index=False)
status={'passed':True,'groundwater_checks':len(rows),'minimum_annual_pairs':6,'partial_correlation_minimum_pairs':8,'annual_endpoint_policy':'At least eight storage months; incomplete calendar endpoint years excluded','human_TWS_validation':'Well heads assess only groundwater consistency and cannot directly validate full human TWSA','human_GWS_validation':'Climate-controlled, detrended and contiguous-change associations supplement raw agreement; no storage coefficient or causal pumping proof','reference_period':'Human-model difference represents change relative to 2004–2009, not cumulative pre-GRACE depletion'}
(OUT/'logs/evidence_status.json').write_text(json.dumps(status,indent=2),encoding='utf-8');print(json.dumps(status,indent=2))
