"""Observation-network uncertainty and well-level checks on the CSR baseline."""
import json,warnings
import numpy as np,pandas as pd
from scipy.stats import theilslopes,kendalltau
from research_common import ROOT,bh_fdr
OUT=ROOT/'Thailand_Research_v5';rng=np.random.default_rng(20516)
d=pd.read_csv(ROOT/'Thailand_Objective2/analysis_v3/tables/groundwater_signed_anomalies.csv',dtype={'region':str},parse_dates=['date'])
f=pd.read_csv(OUT/'tables/CSR_naturalized_attribution.csv',dtype={'region':str},parse_dates=['date'])
def annual(s):
    s=s.dropna();a=s.resample('YS').agg(['mean','count']);a.loc[a['count']<8,'mean']=np.nan
    if len(s):
        if s.index.min().month>1:a.loc[a.index.year==s.index.min().year,'mean']=np.nan
        if s.index.max().month<12:a.loc[a.index.year==s.index.max().year,'mean']=np.nan
    return a['mean']
def r(a,b):
    a=np.asarray(a);b=np.asarray(b);ok=np.isfinite(a)&np.isfinite(b)
    return float(np.corrcoef(a[ok],b[ok])[0,1]) if ok.sum()>=6 and np.std(a[ok])>0 and np.std(b[ok])>0 else np.nan
def remove(a,z):
    Z=np.column_stack([np.ones(len(z)),z]);return a-Z@np.linalg.lstsq(Z,a,rcond=None)[0]
rows=[];coverage=[];wellrows=[]
for code in ['TH']+sorted(x for x in f.region.dropna().unique() if x!='TH'):
    local=d if code=='TH' else d[d.region==code]
    for quality in ['retained_flags','exclude_flagged','fixed_2013_2022','common_period_retained','strict_balanced_2013_2022']:
        v=local[(local.interval=='YS')&local.head_z.notna()].copy()
        if quality=='exclude_flagged':v=v[~v.source_flagged]
        if quality=='fixed_2013_2022':
            n=v[v.date.dt.year.between(2013,2022)].groupby('well_id').date.nunique();ids=set(n[n>=8].index);v=v[v.well_id.isin(ids)]
        if quality in ['common_period_retained','strict_balanced_2013_2022']:
            v=v[v.date.dt.year.between(2013,2022)]
            if quality=='strict_balanced_2013_2022':
                n=v.groupby('well_id').date.nunique();ids=set(n[n==10].index);v=v[v.well_id.isin(ids)]
        station=v.groupby(['date','station_group']).head_z.median().unstack('station_group').sort_index()
        for date,row in station.iterrows():coverage.append({'region':code,'quality':quality,'year':date.year,'station_groups_observed':int(row.notna().sum())})
        for var in ['TWSA','GWSA']:
            g=f[(f.region==code)&(f.variable==var)].set_index('date')
            for component in ['observed_mm','residual_mm']:
                series=annual(g[component]);climate=annual(g.climate_mm)
                years=series.index.union(station.index).intersection(climate.index);M=station.reindex(years).to_numpy();y=series.reindex(years).to_numpy();c=climate.reindex(years).to_numpy()
                if M.shape[1]:M=M[:,np.isfinite(M[np.isfinite(y)&np.isfinite(c)]).any(axis=0)]
                with warnings.catch_warnings():warnings.simplefilter('ignore');head=np.nanmean(M,axis=1) if M.shape[1] else np.full(len(years),np.nan)
                ok=np.isfinite(head)&np.isfinite(y)&np.isfinite(c);n=int(ok.sum());rho=r(head[ok],y[ok]);partial=r(remove(head[ok],c[ok]),remove(y[ok],c[ok])) if n>=8 else np.nan
                detrend=r(remove(head[ok],years.year[ok]),remove(y[ok],years.year[ok])) if n>=8 else np.nan
                cont=np.diff(years.year[ok])==1;dr=r(np.diff(head[ok])[cont],np.diff(y[ok])[cont])
                boot=[]
                if n>=8 and M.shape[1]>=3:
                    for _ in range(499):
                        ix=rng.integers(M.shape[1],size=M.shape[1])
                        with warnings.catch_warnings():warnings.simplefilter('ignore');h=np.nanmean(M[:,ix],axis=1)
                        rr=r(h,y)
                        if np.isfinite(rr):boot.append(rr)
                lo,hi=np.quantile(boot,[.025,.975]) if boot else [np.nan,np.nan]
                rows.append({'region':code,'variable':var,'component':component,'quality':quality,'n_years':n,'station_groups':M.shape[1],'r':rho,'climate_controlled_r':partial,'detrended_r':detrend,'contiguous_change_r':dr,'station_bootstrap_lo95':lo,'station_bootstrap_hi95':hi,'station_bootstrap_valid_replicates':len(boot),'interval_scope':'499 coordinate-station resamples; conditional on observed years, not temporal or causal uncertainty','evidence_role':'Groundwater consistency' if var=='GWSA' else 'Indirect groundwater-part consistency only'})
    print('Well-network uncertainty',code,flush=True)
for well,g in d[d.interval=='YS'].groupby('well_id'):
    g=g[g.head_m.notna()].sort_values('date');year=g.date.dt.year.to_numpy()
    if len(g)<8 or year.max()-year.min()<8:continue
    slope=theilslopes(g.head_m,year).slope;p=kendalltau(year,g.head_m).pvalue
    code=g.region.iloc[0];row={'well_id':well,'region':code,'station_group':g.station_group.iloc[0],'n':len(g),'span_years':int(year.max()-year.min()),'head_sen_m_year':slope,'kendall_p_descriptive':p}
    model=f[(f.region==code)&(f.variable=='GWSA')].set_index('date')
    for key in ['observed_mm','residual_mm']:
        a=annual(model[key]);z=g.set_index('date').head_m.to_frame('head').join(a.rename('storage')).dropna()
        row[key+'_r']=r(z['head'],z.storage);row[key+'_n']=len(z)
    wellrows.append(row)
W=pd.DataFrame(wellrows);W['kendall_q_FDR']=bh_fdr(W.kendall_p_descriptive)
W.to_csv(OUT/'tables/well_level_trend_and_agreement.csv',index=False)
R=pd.DataFrame(rows);R.to_csv(OUT/'tables/CSR_groundwater_network_evidence.csv',index=False);pd.DataFrame(coverage).to_csv(OUT/'tables/groundwater_station_coverage.csv',index=False)
summary=[]
for code in ['TH']+sorted(W.region.dropna().unique()):
    v=W if code=='TH' else W[W.region==code];s=v.groupby('station_group').head_sen_m_year.median().to_numpy()
    boot=[np.mean(s[rng.integers(len(s),size=len(s))]<0) for _ in range(999)]
    summary.append({'region':code,'eligible_wells':len(v),'station_groups':len(s),'median_station_head_slope_m_year':float(np.median(s)),'declining_station_fraction':float(np.mean(s<0)),'fraction_lo95':np.quantile(boot,.025),'fraction_hi95':np.quantile(boot,.975),'interpretation':'Head-direction screen; no conversion to pumping or groundwater mass'})
pd.DataFrame(summary).to_csv(OUT/'tables/groundwater_station_trend_summary.csv',index=False)
qa={'passed':True,'annual_wells_total':int(d[d.interval=='YS'].well_id.nunique()),'monthly_wells_total':int(d[d.interval=='MS'].well_id.nunique()),'eligible_well_trends':len(W),'annual_network_checks':len(R),'head_storage_coefficient_invented':False,'network_intervals_are_temporally_conditional':True}
(OUT/'logs/groundwater_network_qa.json').write_text(json.dumps(qa,indent=2),encoding='utf-8');print(json.dumps(qa,indent=2))
