"""Exploratory rainfall-concentration mechanism; no storage reconstruction."""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
from pathlib import Path
import numpy as np,pandas as pd,json
from scipy.stats import pearsonr
from research_common import bh_fdr
R=Path(os.environ.get('TWSA_RESEARCH_ROOT',Path(__file__).resolve().parents[1]));O=R/'Thailand_Direct_WaterGAP_Analysis/robustness_extension';I=O/'inputs';T=O/'tables';T.mkdir(exist_ok=True)
files=list(I.glob('CHIRPS_annual_indices_*.csv'));assert len(files)==21,'All 2003–2023 years must finish downloading first'
rain=pd.concat([pd.read_csv(f,dtype={'region':str}) for f in sorted(files)],ignore_index=True)
assert (rain.valid_days==rain.calendar_days).all();assert rain[['region','year']].duplicated().sum()==0;assert len(rain)==21*23
rain.to_csv(T/'rainfall_concentration_annual_indices.csv',index=False)
a=pd.read_csv(R/'Thailand_Publication_v6/tables/CSR_naturalized_attribution.csv',dtype={'region':str},parse_dates=['date'])
forcing=pd.read_csv(R/'Thailand_Publication_v6/tables/forcing_monthly_series_2003_2023.csv',dtype={'region':str},parse_dates=['date'])
forcing['year']=forcing.date.dt.year
pet=forcing.groupby(['region','year']).Native_PET.agg(['sum','count']).reset_index().rename(columns={'sum':'PET_annual_mm','count':'PET_months'});pet.loc[pet.PET_months<12,'PET_annual_mm']=np.nan
rows=[]
for (code,var),g in a[a.date.dt.year.between(2003,2023)].groupby(['region','variable']):
 g=g.dropna(subset=['observed_mm','climate_mm','residual_mm']).copy();ref=g[g.date.dt.year.between(2004,2009)]
 for c in ['observed_mm','climate_mm','residual_mm']:g[c+'_deseasonal']=g[c]-g.date.dt.month.map(ref.groupby(ref.date.dt.month)[c].mean())
 for year,q in g.groupby(g.date.dt.year):
  if len(q)<8:continue
  rows.append({'region':code,'variable':var,'year':year,'storage_months':len(q),**{c:q[c+'_deseasonal'].mean() for c in ['observed_mm','climate_mm','residual_mm']}})
annual=pd.DataFrame(rows).merge(rain,on=['region','year'],validate='many_to_one').merge(pet,on=['region','year'],validate='many_to_one').dropna(subset=['PET_annual_mm'])
annual.to_csv(T/'rainfall_storage_annual_paired.csv',index=False)
primary='area_mean_local_daily_Gini';predictors=[primary,'basin_mean_daily_Gini','area_mean_local_CDD_days'];results=[];predrows=[];rng=np.random.default_rng(922026)
def design(g,extra=None,mu=None,sd=None):
 raw=g[['P_annual_mm','PET_annual_mm','year']+([extra] if extra else [])].to_numpy(float)
 if mu is None:mu=raw.mean(axis=0);sd=raw.std(axis=0)
 sd=np.where(sd>0,sd,1);return np.column_stack([np.ones(len(g)),(raw-mu)/sd]),mu,sd
def coefse(X,y):
 pinv=np.linalg.pinv(X);b=pinv@y;e=y-X@b;lev=np.sum(X*pinv.T,axis=1);omega=(e/np.maximum(1-lev,.05))**2;cov=(pinv*omega)@pinv.T;return b,np.sqrt(np.maximum(np.diag(cov),0)),e
for (code,var),g in annual.groupby(['region','variable']):
 g=g.sort_values('year');n=len(g)
 if n<12:continue
 for component in ['observed_mm','climate_mm','residual_mm']:
  y=g[component].to_numpy();X0,_,_=design(g);b0,se0,e0=coefse(X0,y)
  for feature in predictors:
   X,mu,sd=design(g,feature);b,se,e=coefse(X,y);tobs=b[-1]/se[-1] if se[-1]>0 else 0;boots=[];null=[]
   for _ in range(999):
    off=int(rng.integers(2));clusters=(g.year.to_numpy()-g.year.min()+off)//2;signs=rng.choice([-1.,1.],clusters.max()+1)[clusters]
    bb,ss,_=coefse(X,X@b+e*signs);boots.append(bb[-1])
    bb,ss,_=coefse(X,X0@b0+e0*signs);null.append(bb[-1]/ss[-1] if ss[-1]>0 else 0)
   p=(1+np.sum(np.abs(null)>=abs(tobs)))/1000
   base_pred=[];full_pred=[]
   for j in range(n):
    train=g.iloc[np.arange(n)!=j];test=g.iloc[[j]]
    for extra,dest in [(None,base_pred),(feature,full_pred)]:
     xx,mm,ss=design(train,extra);xt,_,_=design(test,extra,mm,ss);dest.append(float((xt@np.linalg.lstsq(xx,np.delete(y,j),rcond=None)[0])[0]))
   rb=np.sqrt(np.mean((y-base_pred)**2));rf=np.sqrt(np.mean((y-full_pred)**2))
   ex=g[feature].to_numpy()-X0@np.linalg.lstsq(X0,g[feature].to_numpy(),rcond=None)[0];ey=y-X0@b0
   results.append({'region':code,'variable':var,'component':component,'rain_metric':feature,'primary_metric':feature==primary,'n_years':n,'coefficient_mm_per_metric_SD':b[-1],'wild_lo95':np.quantile(boots,.025),'wild_hi95':np.quantile(boots,.975),'partial_r':pearsonr(ex,ey).statistic,'wild_null_p':p,'LOYO_base_RMSE_mm':rb,'LOYO_with_metric_RMSE_mm':rf,'LOYO_RMSE_gain_mm':rb-rf,'interpretation':'Exploratory association controlling annual rain, PET and linear time; LOYO explanatory test, not operational forecasting or causal identification'})
   if feature==primary:
    for year,yy,pb,pf in zip(g.year,y,base_pred,full_pred):predrows.append({'region':code,'variable':var,'component':component,'year':year,'annual_deseasonalized_mm':yy,'base_LOYO_mm':pb,'with_Gini_LOYO_mm':pf})
 print('rainfall mechanism',code,var,n,flush=True)
out=pd.DataFrame(results)
# Full fixed families: 22 basins × 2 storage variables × 3 responses × 3 rain metrics; national separate.
for mask in [out.region!='TH',out.region=='TH']:out.loc[mask,'FDR_q']=bh_fdr(out.loc[mask,'wild_null_p'])
out.to_csv(T/'rainfall_concentration_mechanism.csv',index=False);pd.DataFrame(predrows).to_csv(T/'rainfall_concentration_LOYO.csv',index=False)
# Independent processing check: native daily basin sums versus existing monthly CHIRPS.
daily=pd.concat([pd.read_csv(f,dtype={'region':str},parse_dates=['date']) for f in sorted(I.glob('CHIRPS_daily_basins_*.csv'))],ignore_index=True);daily['date']=daily.date.dt.to_period('M').dt.to_timestamp();monthly=daily.groupby(['region','date']).precip_mm_day.sum(min_count=28).reset_index(name='native_daily_sum_mm');q=monthly.merge(forcing[['region','date','CHIRPS_P']],on=['region','date']).dropna();qc=[]
for code,g in q.groupby('region'):qc.append({'region':code,'n_months':len(g),'r':pearsonr(g.native_daily_sum_mm,g.CHIRPS_P).statistic,'RMSE_mm':np.sqrt(np.mean((g.native_daily_sum_mm-g.CHIRPS_P)**2)),'note':'Different raster aggregation: native 0.05-degree cell centres versus preprocessed monthly grid; diagnostic, not exact identity'})
pd.DataFrame(qc).to_csv(T/'daily_monthly_CHIRPS_crosscheck.csv',index=False)
print(out[(out.region=='TH')&out.primary_metric][['variable','component','n_years','partial_r','wild_lo95','wild_hi95','FDR_q','LOYO_RMSE_gain_mm']].to_string(index=False))
