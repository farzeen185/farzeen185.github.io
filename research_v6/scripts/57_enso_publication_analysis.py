"""Frozen-input ENSO diagnostics and original Thailand publication figures.

No GRACE gaps are filled. Circular whole-year shifts provide a finite phase-
randomization diagnostic, not causal inference. All candidate lags are retained.
"""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
os.environ['MKL_NUM_THREADS']='1'
from pathlib import Path
import json, hashlib, re, io, shutil, textwrap, gc
from datetime import datetime, timezone
import requests
import numpy as np
import pandas as pd
from scipy.stats import pearsonr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import geopandas as gpd

R=Path(os.environ.get('TWSA_RESEARCH_ROOT',Path(__file__).resolve().parents[1])).resolve()
O=R/'Thailand_Research_v5'; V=R/'Thailand_Publication_v6'; T=V/'tables'; F=V/'figures'; I=V/'inputs'
for d in [T,F,I,V/'qa']:d.mkdir(parents=True,exist_ok=True)
sources={
 'oni.txt':'https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt',
 'roni_v5.html':'https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/v5/',
 'dmi.txt':'https://psl.noaa.gov/data/timeseries/month/data/dmi.had.long.data'}
manifest=[]
for fn,url in sources.items():
 p=I/fn
 if not p.exists():
  q=requests.get(url,timeout=90);q.raise_for_status();p.write_bytes(q.content)
 manifest.append({'file':fn,'url':url,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
if not (I/'manifest.json').exists():
 (I/'manifest.json').write_text(json.dumps({'frozen_utc':datetime.now(timezone.utc).isoformat(),'sources':manifest},indent=2),encoding='utf-8')
oni=pd.read_csv(I/'oni.txt',sep=r'\s+')
months={'DJF':1,'JFM':2,'FMA':3,'MAM':4,'AMJ':5,'MJJ':6,'JJA':7,'JAS':8,'ASO':9,'SON':10,'OND':11,'NDJ':12}
oni['date']=pd.to_datetime(dict(year=oni.YR,month=oni.SEAS.map(months),day=1))
oni=oni.set_index('date').ANOM.rename('ONI')
# The HTML table freezes the provider's rounded historical RONI v5 values.
html=(I/'roni_v5.html').read_text(); rows=[]
for row in re.findall(r'<tr\b[^>]*>(.*?)</tr>',html,re.S|re.I):
 cells=[re.sub('<[^>]+>','',c).strip().replace('&nbsp;','') for c in re.findall(r'<t[dh]\b[^>]*>(.*?)</t[dh]>',row,re.S|re.I)]
 if len(cells)>=13 and re.fullmatch(r'(19|20)\d{2}',cells[0]):
  for m,s in enumerate(cells[1:13],1):
   try:rows.append((pd.Timestamp(int(cells[0]),m,1),float(s)))
   except ValueError:pass
assert len(rows)>800, f'RONI table parse failed: {len(rows)}'
roni=pd.Series(dict(rows),name='RONI_v5')
rows=[]
for line in (I/'dmi.txt').read_text().splitlines():
 c=line.split()
 if len(c)==13 and c[0].isdigit() and 1800<int(c[0])<2100:
  for m,s in enumerate(c[1:],1):
   x=float(s)
   rows.append((pd.Timestamp(int(c[0]),m,1),x if x>-90 else np.nan))
dmi=pd.Series(dict(rows),name='DMI')
idx=pd.concat([oni,roni,dmi],axis=1,sort=True).sort_index()
def phases(s):
 # NOAA episode rule on values rounded to the public table's 0.1 C precision.
 x=s.round(1); z=pd.Series('Neutral',index=x.index); eid=pd.Series('',index=x.index)
 for sign,name in [(1,'El Nino'),(-1,'La Nina')]:
  flag=(x*sign>=.5); groups=flag.ne(flag.shift()).cumsum()
  for _,g in flag.groupby(groups):
   if g.iloc[0] and len(g)>=5:
    z.loc[g.index]=name;eid.loc[g.index]=f'{name}_{g.index[0]:%Y-%m}'
 return z,eid
idx['phase'],idx['episode']=phases(idx.ONI)
idx['RONI_phase'],_=phases(idx.RONI_v5)
idx.index.name='date';idx.to_csv(T/'climate_indices_monthly.csv')
read=lambda p:pd.read_csv(p,dtype={'region':str})
at=read(O/'tables/CSR_naturalized_attribution.csv');at['date']=pd.to_datetime(at.date)
pred=read(R/'Thailand_Objective2/analysis_v4/tables/climate_emulator_timeseries.csv');pred['date']=pd.to_datetime(pred.date)
aux=read(O/'basin_forcing_appendix/tables/forcing_monthly_series_2003_2023.csv');aux['date']=pd.to_datetime(aux.date)
land=read(O/'figure_revision/tables/GLDAS_matched_land_timeseries.csv');land['date']=pd.to_datetime(land.date)
names=dict(zip(at.region,at.region_name));codes=sorted(c for c in names if c!='TH');grid=pd.date_range('2003-01-01','2023-12-01',freq='MS')
assert len(codes)==22
series=[]
for (code,var),g in at.groupby(['region','variable']):
 g=g.set_index('date').reindex(grid)
 for col,label in [('observed_mm','Observed'),('climate_mm','Climate'),('residual_mm','Residual')]:
  for date,value in g[col].items():series.append((date,code,var,label,value))
for code,g in aux.groupby('region'):
 g=g.set_index('date').reindex(grid)
 for col in ['Native_P','Native_PET','CHIRPS_P']:
  for date,value in g[col].items():series.append((date,code,'Forcing',col,value))
ss=pd.DataFrame(series,columns=['date','region','variable','component','value'])
# Residualize each series against calendar month, linear trend and contemporaneous DMI.
# For each lag, lagged ENSO is residualized against the same nuisance design on exact paired dates.
def residualize(y,X):return y-X@np.linalg.lstsq(X,y,rcond=None)[0]
def association(y, enso, lag, dmi_values):
 x=enso.shift(lag);ok=np.isfinite(y)&np.isfinite(x)&np.isfinite(dmi_values)
 if ok.sum()<60:return np.nan,np.nan,int(ok.sum())
 dates=grid[ok]; nuisance=np.column_stack([np.ones(ok.sum()),np.arange(len(grid))[ok]/12,pd.get_dummies(dates.month,drop_first=True,dtype=float),dmi_values[ok]])
 a=residualize(y[ok],nuisance);b=residualize(x[ok].to_numpy(),nuisance)
 r=float(np.corrcoef(a,b)[0,1]);null=[]
 # Exhaust all nonzero circular whole-year rotations on the 21-year common calendar.
 # Shift the ENSO predictor, leave the observed missing-month pattern fixed, and refit nuisances.
 for years in range(1,21):
  shifted=pd.Series(np.roll(enso.to_numpy(),12*years),index=grid).shift(lag)
  good=np.isfinite(y)&np.isfinite(shifted)&np.isfinite(dmi_values)
  dates2=grid[good];X=np.column_stack([np.ones(good.sum()),np.arange(len(grid))[good]/12,pd.get_dummies(dates2.month,drop_first=True,dtype=float),dmi_values[good]])
  aa=residualize(y[good],X);bb=residualize(shifted[good].to_numpy(),X)
  null.append(float(np.corrcoef(aa,bb)[0,1]))
 return r,(1+np.sum(np.abs(null)>=abs(r)))/21,int(ok.sum())
rows=[]; ens=idx.reindex(grid)
for (code,var,comp),g in ss.groupby(['region','variable','component']):
 y=g.set_index('date').reindex(grid).value.to_numpy(dtype=float)
 for index in ['ONI','RONI_v5']:
  for lag in [0,3,6,9,12]:
   r,p,n=association(y,ens[index],lag,ens.DMI.to_numpy())
   rows.append({'region':code,'basin':names[code],'variable':var,'component':comp,'index':index,'lag_months':lag,'partial_r':r,'rotation_p':p,'n_months':n})
results=pd.DataFrame(rows)
def bh(p):
 p=np.asarray(p);out=np.full(len(p),np.nan);valid=np.isfinite(p);a=p[valid];order=np.argsort(a);q=np.minimum.accumulate((a[order]*len(a)/np.arange(1,len(a)+1))[::-1])[::-1];tmp=np.empty(len(a));tmp[order]=np.minimum(q,1);out[valid]=tmp;return out
# One preregistered-like analysis plan fixed before this execution; exploratory, not a registered study.
# FDR family = both indices x all candidate lags x all 22 basins x all 9 storage/forcing series.
mask=results.region!='TH';results.loc[mask,'FDR_q']=bh(results.loc[mask,'rotation_p'])
results.loc[~mask,'FDR_q']=bh(results.loc[~mask,'rotation_p'])
results.to_csv(T/'ENSO_lagged_associations.csv',index=False)
print('ENSO associations complete',len(results),flush=True)
# Composite means after removing calendar season and linear trend, without removing DMI:
# these are observed joint ENSO/IOD phase conditions, not unique ENSO effects.
composites=[]
for (code,var,comp),g in ss.groupby(['region','variable','component']):
 y=g.set_index('date').reindex(grid).value.to_numpy(dtype=float);ok=np.isfinite(y)
 X=np.column_stack([np.ones(ok.sum()),np.arange(len(grid))[ok]/12,pd.get_dummies(grid[ok].month,drop_first=True,dtype=float)])
 z=pd.Series(np.nan,index=grid);z.loc[ok]=residualize(y[ok],X)
 for phase in ['El Nino','Neutral','La Nina']:
  use=ens.phase==phase;vals=z[use].dropna();episode=ens.loc[vals.index,'episode'];eventmeans=vals.groupby(episode).mean() if phase!='Neutral' else pd.Series(dtype=float)
  eventmeans=eventmeans[eventmeans.index!=''];rng=np.random.default_rng(20261025);lo=hi=np.nan
  if len(eventmeans)>=3:
   draws=rng.choice(eventmeans.to_numpy(),(1999,len(eventmeans)),replace=True).mean(axis=1);lo,hi=np.quantile(draws,[.025,.975])
  composites.append({'region':code,'variable':var,'component':comp,'phase':phase,'n_months':len(vals),'episodes':len(eventmeans),'monthly_mean':vals.mean(),'episode_equal_mean':eventmeans.mean(),'episode_boot_lo':lo,'episode_boot_hi':hi})
pd.DataFrame(composites).to_csv(T/'ENSO_phase_composites.csv',index=False)
# Held-out reconstruction evaluated separately by ENSO phase.
perf=[]
def metrics(y,p):
 ok=np.isfinite(y)&np.isfinite(p);y=np.asarray(y)[ok];p=np.asarray(p)[ok]
 return {'n':len(y),'r':float(np.corrcoef(y,p)[0,1]) if len(y)>2 else np.nan,'RMSE_mm':float(np.sqrt(np.mean((y-p)**2))) if len(y) else np.nan,'NSE':float(1-np.sum((y-p)**2)/np.sum((y-y.mean())**2)) if len(y)>2 and np.std(y)>0 else np.nan}
for (code,var),g in pred[pred.date.dt.year.between(2016,2023)].groupby(['region','variable']):
 g=g.merge(idx[['phase']],left_on='date',right_index=True,validate='many_to_one')
 for phase,z in g.groupby('phase'):perf.append({'region':code,'variable':var,'phase':phase,**metrics(z.naturalized_target_mm,z.emulator_mm)})
pd.DataFrame(perf).to_csv(T/'climate_skill_by_ENSO_phase.csv',index=False)
# Variability ratios use mean absolute deviation about the series mean (not median deviation).
madrows=[]
for (code,var),g in at[at.date.dt.year.between(2003,2023)].groupby(['region','variable']):
 for year,z in g.groupby(g.date.dt.year):
  z=z.dropna(subset=['observed_mm','climate_mm','residual_mm'])
  if len(z)<8:continue
  mad=lambda c:np.mean(np.abs(z[c]-z[c].mean()))
  denom=mad('observed_mm')
  if denom<=0:continue
  madrows.append({'region':code,'variable':var,'year':year,'n':len(z),'climate_MAD_ratio':mad('climate_mm')/denom,'residual_MAD_ratio':mad('residual_mm')/denom})
madtable=pd.DataFrame(madrows);madtable.to_csv(T/'annual_variability_ratios.csv',index=False)

plt.rcParams.update({'font.family':'DejaVu Serif','font.size':11,'axes.labelsize':11,'axes.titlesize':11,'axes.spines.top':True,'axes.spines.right':True,'savefig.facecolor':'white'})
inventory=[]
def save(fig,stem,title,caption):
 fig.tight_layout()
 for ext in ['png','pdf']:fig.savefig(F/(stem+'.'+ext),dpi=220,bbox_inches='tight')
 plt.close(fig);gc.collect();inventory.append({'id':len(inventory)+1,'stem':stem,'title':title,'caption':caption});print('Saved',stem,flush=True)
def panels():
 fig,axes=plt.subplots(6,4,figsize=(14,17))
 for ax in axes.ravel()[22:]:ax.set_visible(False)
 return fig,axes.ravel()
def scatteratlas(var):
 fig,axes=panels()
 for i,code in enumerate(codes):
  ax=axes[i];z=pred[(pred.region==code)&(pred.variable==var)&pred.date.dt.year.between(2016,2023)].dropna(subset=['emulator_mm','naturalized_target_mm']);x=z.emulator_mm.to_numpy();y=z.naturalized_target_mm.to_numpy();m=metrics(y,x)
  ax.scatter(x,y,s=9,c='#26c6df',alpha=.65,edgecolors='none');xx=np.linspace(min(x.min(),y.min()),max(x.max(),y.max()),100);coef=np.polyfit(x,y,1);ax.plot(xx,np.polyval(coef,xx),c='#d85e87',lw=1.4);ax.plot(xx,xx,c='#666',lw=.7,ls='--')
  rng=np.random.default_rng(712+i);years=z.date.dt.year.unique();fits=[]
  for _ in range(399):
   sample=np.concatenate([np.flatnonzero(z.date.dt.year.to_numpy()==k) for k in rng.choice(years,len(years),replace=True)])
   fits.append(np.polyval(np.polyfit(x[sample],y[sample],1),xx))
  lo,hi=np.quantile(fits,[.025,.975],axis=0);ax.fill_between(xx,lo,hi,color='#d85e87',alpha=.15)
  ax.text(.96,.05,f'R {m["r"]:.2f}\nRMSE {m["RMSE_mm"]:.1f} mm\nNSE {m["NSE"]:.2f}\nn = {m["n"]}',transform=ax.transAxes,ha='right',va='bottom',fontsize=8,bbox={'fc':'white','ec':'#999','lw':.5,'alpha':.9});ax.set_title(code+' '+names[code][:21],loc='left',fontweight='bold');ax.grid(alpha=.22);ax.tick_params(labelsize=8)
  if i%4==0:ax.set_ylabel('Naturalized parent (mm)')
  if i>=18:ax.set_xlabel('Climate reconstruction (mm)')
 save(fig,'P01_climate_TWSA_scatter' if var=='TWSA' else 'P02_climate_GWSA_scatter',var+' reconstruction in all basins','Held-out 2016–2023 only. Cyan monthly pairs; pink OLS descriptive fit and calendar-year bootstrap 95% band (399 replicates); grey identity. R, RMSE and NSE evaluate predictions directly, not the fitted line. The target is a naturalized model, not independent observed storage.')
scatteratlas('TWSA');scatteratlas('GWSA')
fig,axes=panels()
for i,code in enumerate(codes):
 ax=axes[i];z=land[land.region==code].dropna(subset=['GLDAS_land_mm','naturalized_land_mm']);x=z.naturalized_land_mm;y=z.GLDAS_land_mm;m=metrics(y,x);xx=np.linspace(min(x.min(),y.min()),max(x.max(),y.max()),80)
 ax.scatter(x,y,s=8,c='#26c6df',alpha=.55,edgecolors='none');ax.plot(xx,np.polyval(np.polyfit(x,y,1),xx),c='#d85e87',lw=1.2);ax.plot(xx,xx,c='#777',ls='--',lw=.7);ax.text(.96,.05,f'R {m["r"]:.2f}\nRMSE {m["RMSE_mm"]:.1f}\nNSE {m["NSE"]:.2f}',transform=ax.transAxes,ha='right',fontsize=8,bbox={'fc':'white','ec':'#aaa','lw':.5});ax.set_title(code+' '+names[code][:21],loc='left',fontweight='bold');ax.grid(alpha=.22);ax.tick_params(labelsize=8)
 if i%4==0:ax.set_ylabel('GLDAS land (mm)')
 if i>=18:ax.set_xlabel('WaterGAP matching land (mm)')
save(fig,'P03_GLDAS_scatter','Matched land storage benchmark','Soil, canopy and snow only, April 2002–December 2023 available pairs. GLDAS excludes groundwater and open surface water. Cross-model agreement is not human-component validation; shared climate inputs and the GWS subtraction create dependence. Regression is descriptive.')
fig,axes=panels()
for i,code in enumerate(codes):
 ax=axes[i];p=aux[aux.region==code];g=at[(at.region==code)&(at.variable=='TWSA')&at.date.dt.year.between(2003,2023)].dropna(subset=['observed_mm'])
 boxes=[p[p.date.dt.month==m].Native_P.dropna() for m in range(1,13)];b=ax.boxplot(boxes,positions=range(1,13),widths=.5,patch_artist=True,showfliers=False,manage_ticks=False)
 for box in b['boxes']:box.set(facecolor='#cdebf2',edgecolor='#38a3c5')
 for med in b['medians']:med.set(color='#d85e87')
 a=ax.twinx();stats=g.groupby(g.date.dt.month).observed_mm.agg(['mean',lambda s:s.quantile(.25),lambda s:s.quantile(.75)]);a.plot(stats.index,stats['mean'],color='#c95b82',lw=1.3);a.fill_between(stats.index,stats.iloc[:,1],stats.iloc[:,2],color='#d85e87',alpha=.16);a.tick_params(labelsize=7,colors='#b54d73');ax.set_xticks([1,4,7,10]);ax.tick_params(labelsize=8);ax.set_title(code+' '+names[code][:21],loc='left',fontweight='bold')
 if i%4==0:ax.set_ylabel('P (mm/month)')
 if i%4==3:a.set_ylabel('TWSA (mm)',color='#b54d73')
save(fig,'P04_monthly_seasonality','Rainfall and storage seasonality','Native precipitation distributions by calendar month, 2003–2023 (boxes: quartiles; whiskers: 1.5 IQR; outliers suppressed). Pink mean observed TWSA and interannual interquartile band on right axis. Distribution spread is not confidence in the mean. Missing GRACE months are retained.')
fig,axes=panels()
for i,code in enumerate(codes):
 ax=axes[i];z=madtable[(madtable.region==code)&(madtable.variable=='TWSA')];ax.plot(z.year,z.climate_MAD_ratio,'o-',ms=2.8,lw=1,c='#c38b36',label='Climate');ax.plot(z.year,z.residual_MAD_ratio,'o-',ms=2.8,lw=1,c='#2a9c88',label='Residual');ax.axhline(1,c='#999',ls='--',lw=.6);ax.set_title(code+' '+names[code][:21],loc='left',fontweight='bold');ax.set_xticks([2005,2013,2021]);ax.tick_params(labelsize=8);ax.grid(alpha=.15)
fig.legend(*axes[0].get_legend_handles_labels(),loc='lower right',bbox_to_anchor=(.97,.1),frameon=False);fig.supylabel('Component mean absolute deviation / observed mean absolute deviation')
save(fig,'P05_variability_ratios','Annual climate and residual variability','Matched available months within each year; minimum eight. Mean absolute deviation is centred on the corresponding series mean. Ratios do not add to one and may exceed one because components covary. These are variability diagnostics, not causal climate/human percentages; monthly samples are not uncertainty replicates.')
# Three target-specific RMSE histories by periods, retaining distinct labels.
periods=[(2003,2009),(2010,2015),(2016,2023)];rows=[]
for code in ['TH',*codes]:
 for start,end in periods:
  for key,frame,y,p in [('Climate / GRACE',at[at.variable=='TWSA'],'observed_mm','climate_mm'),('Land / GLDAS',land,'GLDAS_land_mm','naturalized_land_mm'),('Emulator / parent',pred[pred.variable=='TWSA'],'naturalized_target_mm','emulator_mm')]:
   z=frame[(frame.region==code)&frame.date.dt.year.between(start,end)];rows.append({'region':code,'period':f'{start}–{end}','target':key,**metrics(z[y],z[p])})
period=pd.DataFrame(rows);period.to_csv(T/'period_RMSE.csv',index=False)
fig,axes=plt.subplots(2,1,figsize=(11,7));z=at[(at.region=='TH')&(at.variable=='TWSA')].set_index('date').reindex(grid)
axes[0].plot(grid,z.observed_mm,c='#d2a354',label='GRACE observed TWSA',lw=1);axes[0].plot(grid,z.climate_mm,c='#d85e87',label='Naturalized TWSA',lw=1);l=land[land.region=='TH'].set_index('date').reindex(grid);axes[0].plot(grid,l.GLDAS_land_mm,c='#389cc5',label='GLDAS partial land storage',lw=.9);axes[0].set_ylabel('Anomaly (mm)');axes[0].legend(ncol=3,fontsize=9,frameon=False)
for j,(key,color) in enumerate([('Climate / GRACE','#d85e87'),('Land / GLDAS','#389cc5'),('Emulator / parent','#2a9c88')]):
 q=period[(period.region=='TH')&(period.target==key)];axes[1].bar(np.arange(3)+(j-1)*.24,q.RMSE_mm,.23,label=key,color=color)
axes[1].set_xticks(range(3),[f'{a}–{b}' for a,b in periods]);axes[1].set_ylabel('RMSE (mm)');axes[1].legend(ncol=3,fontsize=9,frameon=False);save(fig,'P06_period_benchmarks','Storage histories and period benchmarks','National overview. GLDAS is partial land storage, not total TWSA. RMSE bars use distinct explicit targets, so their heights do not rank competing models. Emulator periods 2003–2009, 2010–2015 and 2016–2023 respectively overlap training, validation and held-out testing; only the final period is a test.')
geo=gpd.read_file(R/'Thailand_Objective2/data/BASINS/MainBasin_ONWR_Law_WGS84.shp').to_crs(4326);geo['region']=geo.MB_CODE.astype(str).str.split('-').str[0].str.zfill(2);geo=geo.dissolve(by='region',as_index=False,aggfunc='first');geo.geometry=geo.geometry.simplify(.006,preserve_topology=True)
def corrmap(ax,table,title):
 g=geo.merge(table[['region','partial_r','FDR_q']],on='region',how='left');g.plot(column='partial_r',ax=ax,cmap='RdBu_r',vmin=-1,vmax=1,edgecolor='#777',linewidth=.4,missing_kwds={'color':'#ddd'});ax.set_title(title);ax.set_xlabel('Longitude');ax.set_ylabel('Latitude');cb=plt.colorbar(plt.cm.ScalarMappable(norm=Normalize(-1,1),cmap='RdBu_r'),ax=ax,fraction=.035);cb.set_label('Partial r')
 for _,row in g.iterrows():
  if row.FDR_q<.05:xy=row.geometry.representative_point();ax.plot(xy.x,xy.y,'k.',ms=4)
fig,axes=plt.subplots(1,3,figsize=(12,6))
for ax,comp in zip(axes,['Observed','Climate','Residual']):corrmap(ax,results[(results.variable=='TWSA')&(results.component==comp)&(results['index']=='ONI')&(results.lag_months==6)],comp+' TWSA / ONI, lead 6 months')
save(fig,'P07_ENSO_spatial_TWSA','ENSO associations across Thailand','Prespecified six-month ENSO lead. Partial Pearson correlations remove calendar month, linear trend and contemporaneous DMI on paired months, 2003–2023. Dots indicate FDR q<0.05 from whole-year circular rotations. All five candidate lags and both ENSO indices are retained in CSV; no best-lag significance claim. Basins share GRACE support.')
fig,axes=plt.subplots(1,3,figsize=(12,6))
for ax,comp in zip(axes,['Observed','Climate','Residual']):corrmap(ax,results[(results.variable=='GWSA')&(results.component==comp)&(results['index']=='ONI')&(results.lag_months==6)],comp+' GWSA / ONI, lead 6 months')
save(fig,'P08_ENSO_spatial_GWSA','ENSO and derived groundwater storage','As the TWSA spatial diagnostic, with derived GWSA. Association can reflect recharge, compartment errors and management responses; it does not identify groundwater pumping. The finite rotation p value has resolution 1/21; this conservative screen has low power after multiple comparisons.')
fig,axes=plt.subplots(3,2,figsize=(11,9),sharex=True,sharey=True)
for j,var in enumerate(['TWSA','GWSA']):
 for i,comp in enumerate(['Observed','Climate','Residual']):
  ax=axes[i,j]
  for index,color in [('ONI','#d85e87'),('RONI_v5','#389cc5')]:
   z=results[(results.region=='TH')&(results.variable==var)&(results.component==comp)&(results['index']==index)];ax.plot(z.lag_months,z.partial_r,'o-',ms=4,color=color,label=index)
  ax.axhline(0,c='#aaa',lw=.6);ax.set_title(var+' '+comp);ax.set_ylim(-1,1);ax.set_xticks([0,3,6,9,12]);ax.grid(alpha=.2)
axes[0,0].legend(frameon=False);fig.supxlabel('ENSO index lead (months)');fig.supylabel('Partial correlation');save(fig,'P09_ENSO_lag_sensitivity','National lag and index sensitivity','Calendar season, trend and DMI controlled. ONI and historical RONI v5 are frozen at acquisition; RONI v6 is operational in 2026, whereas v5 is deliberately retained here for index-version comparability. The five candidate lags are reported together. Correlation is association, not climate causation or evidence of human-only residuals.')
com=pd.DataFrame(composites);fig,axes=plt.subplots(2,3,figsize=(12,6))
for i,var in enumerate(['TWSA','GWSA']):
 for j,comp in enumerate(['Observed','Climate','Residual']):
  ax=axes[i,j];z=com[(com.region=='TH')&(com.variable==var)&(com.component==comp)].set_index('phase').reindex(['El Nino','Neutral','La Nina']);ax.bar(range(3),z.monthly_mean,color=['#d85e87','#aaa','#389cc5'],alpha=.8);ax.set_xticks(range(3),['El Niño','Neutral','La Niña']);ax.axhline(0,c='#666',lw=.6);ax.set_title(var+' '+comp);ax.set_ylabel('Adjusted anomaly (mm)')
  for k,(_,row) in enumerate(z.iterrows()):ax.text(k,.98,f'n={int(row.n_months)}',transform=ax.get_xaxis_transform(),ha='center',va='top',fontsize=8)
save(fig,'P10_ENSO_composites','Storage during ENSO phases','Monthly means after calendar-season and linear-trend removal, 2003–2023. ONI episodes require five consecutive overlapping seasons at ±0.5 C, classified on provider-table 0.1 C precision. Numbers are available months, not independent events. Equal-episode estimates and episode-bootstrap intervals are supplied separately in CSV; phase bars are descriptive and do not remove IOD.')
fig,axes=plt.subplots(1,2,figsize=(10,4))
perf=pd.DataFrame(perf)
for ax,var in zip(axes,['TWSA','GWSA']):
 z=perf[(perf.region=='TH')&(perf.variable==var)].set_index('phase').reindex(['El Nino','Neutral','La Nina']);ax.bar(range(3),z.RMSE_mm,color=['#d85e87','#aaa','#389cc5']);ax.set_xticks(range(3),['El Niño','Neutral','La Niña']);ax.set_ylabel('Held-out RMSE (mm)');ax.set_title(var+' reconstruction')
 for k,(_,row) in enumerate(z.iterrows()):ax.text(k,row.RMSE_mm+.5,f'n={int(row.n)}',ha='center',fontsize=9)
save(fig,'P11_ENSO_model_skill','Climate reconstruction by ENSO phase','Frozen climate ensemble evaluated in 2016–2023, with the naturalized parent as target. Phase subsets differ in sample size and target variance; do not compare phase NSE without these counts. No phase-specific refitting or ENSO predictor was introduced after examining test performance.')
(V/'figure_inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2),encoding='utf-8')
national=results[(results.region=='TH')&(results['index']=='ONI')&(results.lag_months==6)]
summary={'n_basins':22,'analysis_months':252,'association_rows':len(results),'rotation_count':20,'min_rotation_p':1/21,'basin_FDR_significant':int((results.loc[mask,'FDR_q']<.05).sum()),'national_six_month_ONI':national.to_dict('records'),'phase_skill':perf[perf.region=='TH'].to_dict('records'),'interpretation':'Exploratory climate-leakage and phase diagnostics; residual is not observed pumping.'}
(V/'analysis_summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False))
(V/'qa/analysis_checks.json').write_text(json.dumps({'passed':True,'basins':len(codes),'indices_finite_2003_2023':bool(ens[['ONI','RONI_v5','DMI']].notna().all().all()),'all_lags_retained':True,'phase_counts':ens.phase.value_counts().to_dict(),'figures':len(inventory)},indent=2))
print(json.dumps(summary,indent=2),flush=True)
