"""Reproducible basin-wide spatial and temporal figure atlas for the revised study."""
import h5py
from pathlib import Path
import json,warnings,gc,textwrap
import numpy as np,pandas as pd,xarray as xr,geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm,Normalize
from matplotlib.ticker import MaxNLocator
import matplotlib.dates as mdates
from research_common import ROOT,region_weights,weighted_series,metrics
O=ROOT/'Thailand_Research_v5';A=O/'figure_revision';F=A/'figures';T=A/'tables'
for p in [F,T,A/'logs']:p.mkdir(parents=True,exist_ok=True)
read=lambda n:pd.read_csv(O/'tables'/n,dtype={'region':str},parse_dates=['date'] if n in ['CSR_basin_storage_timeseries.csv','CSR_naturalized_attribution.csv','independent_reservoir_timeseries.csv'] else None)
obs=read('CSR_basin_storage_timeseries.csv');at=read('CSR_naturalized_attribution.csv');tr=read('CSR_basin_trends.csv');ci=read('attribution_wild_block_intervals.csv');well=read('CSR_groundwater_network_evidence.csv');res=read('independent_reservoir_evidence.csv');rst=read('independent_reservoir_timeseries.csv')
E=ROOT/'Thailand_Objective2/analysis_v4/tables'
pred=pd.read_csv(E/'climate_emulator_timeseries.csv',dtype={'region':str},parse_dates=['date']);ev=pd.read_csv(E/'climate_emulator_validation.csv',dtype={'region':str});ev=ev[(ev.model=='Ensemble')&(ev.period=='Test')]
geo=gpd.read_file(ROOT/'Thailand_Objective2/data/BASINS/MainBasin_ONWR_Law_WGS84.shp').to_crs(4326);geo['region']=geo.MB_CODE.astype(str).str.split('-').str[0].str.zfill(2);geo=geo.dissolve(by='region',as_index=False,aggfunc='first');codes=sorted(geo.region)
# Display geometry only; all scientific aggregation uses the retained intersection weights.
geo.geometry=geo.geometry.simplify(.006,preserve_topology=True)
names=dict(zip(obs.region,obs.region_name));plt.rcParams.update({'font.family':'DejaVu Sans','font.size':14,'axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'white'})
inventory=[]
def save(fig,n,title,caption,category):
    name=f'A{n:02d}_'+category
    gc.collect();fig.savefig(F/(name+'.pdf'),bbox_inches='tight');fig.savefig(F/(name+'.png'),dpi=150,bbox_inches='tight');plt.close(fig);fig.clear();gc.collect()
    print('Saved',name,flush=True)
    inventory.append({'id':n,'file':name+'.png','title':title,'caption':caption,'category':category,'pdf':name+'.pdf'})
def maps(values,titles,labels,limits=None,cmaps=None,ncols=2):
    gc.collect()
    n=len(values);nr=int(np.ceil(n/ncols));fig,axes=plt.subplots(nr,ncols,figsize=(5.4*ncols,6.2*nr),squeeze=False)
    for i,(value,title,label) in enumerate(zip(values,titles,labels)):
        ax=axes.ravel()[i];g=geo.merge(value.rename('value'),left_on='region',right_index=True,how='left');v=g.value.dropna()
        lim=limits[i] if limits else None
        if lim is None:
            m=max(float(v.abs().max()) if len(v) else 1,1e-6);lim=(-m,m)
        cmap=(cmaps[i] if cmaps else 'RdBu');norm=TwoSlopeNorm(vmin=lim[0],vcenter=0,vmax=lim[1]) if lim[0]<0<lim[1] else Normalize(*lim)
        g.plot(column='value',ax=ax,cmap=cmap,norm=norm,edgecolor='#737d85',linewidth=.4,missing_kwds={'color':'#e1e3e6','edgecolor':'#8d959c','hatch':'///'})
        # Basin identifiers are more legible than 22 full names on a small map.
        if n<=4:
            for _,row in g.iterrows():
                p=row.geometry.representative_point();ax.text(p.x,p.y,row.region,fontsize=9,ha='center',va='center',color='#26333d')
        ax.set_title(textwrap.fill(chr(97+i)+') '+title,width=28),fontsize=20,pad=10);ax.set_xlabel('Longitude',fontsize=18);ax.set_ylabel('Latitude',fontsize=18);ax.tick_params(labelsize=15)
        cb=fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=cmap),ax=ax,fraction=.042,pad=.025);cb.set_label(label,fontsize=20);cb.ax.tick_params(labelsize=15)
    for ax in axes.ravel()[n:]:ax.set_visible(False)
    fig.tight_layout();return fig
def panel(lines,title_ylabel='mm water equivalent',testshade=False,ylim=None):
    gc.collect()
    fig,axes=plt.subplots(6,4,figsize=(12,13.3),sharex=True)
    handles=[]
    for k,code in enumerate(codes):
        ax=axes.ravel()[k];has_data=False
        for dates,values,label,color,style in lines(code):
            has_data=has_data or bool(np.isfinite(np.asarray(values,dtype=float)).any())
            h,=ax.plot(dates,values,label=label,color=color,lw=1.1,ls=style);handles.append(h) if k==0 else None
        ax.set_title(code,fontsize=17,loc='left',pad=1);ax.yaxis.set_major_locator(MaxNLocator(3));ax.tick_params(axis='both',labelsize=13)
        ax.axhline(0,color='#bac4c8',lw=.5)
        if testshade:ax.axvspan(pd.Timestamp('2016-01-01'),pd.Timestamp('2023-12-31'),color='#e0ede8',alpha=.55,zorder=-5)
        if ylim:ax.set_ylim(*ylim)
        ax.xaxis.set_major_locator(mdates.YearLocator(10));ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax.tick_params(labelbottom=True)
        if not has_data:ax.text(.5,.5,'Insufficient support',transform=ax.transAxes,ha='center',va='center',color='#68747d',fontsize=12)
    for ax in axes.ravel()[22:]:ax.set_visible(False)
    fig.legend(handles=handles,loc='upper center',ncol=min(3,len(handles)),fontsize=15,frameon=False,bbox_to_anchor=(.5,1.005));fig.supylabel(title_ylabel,fontsize=16,x=.002);fig.supxlabel('Calendar year · basin codes correspond to Appendix A',fontsize=15,y=.003)
    fig.tight_layout(rect=(.025,.02,1,.975),h_pad=.65,w_pad=.65);return fig
def ols(s):
    s=s.dropna();idx=pd.DatetimeIndex(s.index)
    if len(s)<24:return np.nan
    X=np.column_stack([np.ones(len(s)),(idx.year-2002)+(idx.month-1)/12,pd.get_dummies(idx.month,drop_first=True,dtype=float)])
    return float(np.linalg.lstsq(X,s.to_numpy(),rcond=None)[0][1])
def z(s):
    return (s-s.mean())/s.std(ddof=0) if s.notna().sum()>1 and s.std(ddof=0)>0 else s*np.nan
def correlation(a,b,minn=6):
    m=np.isfinite(a)&np.isfinite(b)
    return float(np.corrcoef(np.asarray(a)[m],np.asarray(b)[m])[0,1]) if m.sum()>=minn and np.std(np.asarray(a)[m])>0 and np.std(np.asarray(b)[m])>0 else np.nan
def annual(s):
    s=s.dropna();a=s.resample('YS').agg(['mean','count']);a.loc[a['count']<8,'mean']=np.nan
    if len(s):
        if s.index.min().month>1:a.loc[a.index.year==s.index.min().year,'mean']=np.nan
        if s.index.max().month<12:a.loc[a.index.year==s.index.max().year,'mean']=np.nan
    return a['mean']
print('Generating observed and attribution figures',flush=True)
values=[];titles=[];labels=[];lims=[];cm=[]
for var in ['TWSA','GWSA']:
    g=tr[(tr.variable==var)&(tr.region!='TH')].set_index('region');values += [g.sen_slope_mm_year,g.mk_seasonal_q_FDR];titles += [var+' seasonal Sen slope',var+' seasonal MK FDR q'];labels += ['mm/year','q-value'];m=float(g.sen_slope_mm_year.abs().max());lims += [(-m,m),(0,.1)];cm += ['RdBu','YlOrRd_r']
save(maps(values,titles,labels,lims,cm),1,'Spatial GRACE storage trends and Mann Kendall evidence','Basin-average CSR TWSA and compartment-derived GWSA; seasonal Sen slopes and basin FDR q. q colours saturate at 0.10. Seasonal MK does not correct serial dependence; slope intervals are supplied in the numerical tables. All basins retain the CSR small-support caution.','observed_spatial')
def lines_observed(code):
    g=obs[obs.region==code];return [(g.date,g.TWSA,'CSR TWSA','#173c50','-'),(g.date,g.GWSA,'Derived GWSA','#b66a3c','-')]
save(panel(lines_observed),2,'Observed storage time series for all 22 basins','Monthly CSR TWSA and full-compartment GWSA, in mm. Mission gaps remain missing and GWSA ends in September 2023. Basin codes identify every subplot; full names are in Appendix A.','observed_temporal_all_basins')
values=[];titles=[]
for var in ['TWSA','GWSA']:
    g=ci[(ci.variable==var)&(ci.component=='climate_mm')&(ci.block_years==2)].set_index('region');values.append(g.ols_slope_mm_year);titles.append(var+' naturalized baseline C')
    rows={}
    for code,g in pred[(pred.variable==var)&(pred.date.dt.year>=2002)].groupby('region'):
        dates=at[(at.region==code)&(at.variable==var)].dropna(subset=['climate_mm']).date
        rows[code]=ols(g.set_index('date').emulator_mm.reindex(pd.DatetimeIndex(dates)))
    values.append(pd.Series(rows));titles.append(var+' meteorological emulator')
save(maps(values,titles,['OLS mm/year']*4),3,'Spatial naturalized storage and climate reconstruction','Calendar-month fixed-effect slopes. C is the naturalized WaterGAP baseline used in R=O−C; the statistical emulator reconstructs its parent-model target on its retained verification footprint. Emulator slopes use CSR-available dates through 2023, not a fit to GRACE. These columns are related model estimates, not independent observations.','climate_spatial')
for n,var in [(4,'TWSA'),(5,'GWSA')]:
    def lines(code,var=var):
        g=pred[(pred.region==code)&(pred.variable==var)&(pred.date.dt.year>=2002)];return [(g.date,g.naturalized_target_mm,'Naturalized parent','#173c50','-'),(g.date,g.emulator_mm,'Climate emulator','#b66a3c','--')]
    save(panel(lines,testshade=True),n,var+' climate reconstruction for all 22 basins','Naturalized parent-model target and frozen meteorological ensemble reconstruction. Green shading identifies the held-out 2016–2023 period; earlier values are training or validation context. The emulator targets a hydrological model, not independently observed storage.','climate_'+var+'_temporal')
values=[];titles=[]
for var in ['TWSA','GWSA']:
    for col,label in [('residual_mm','Residual R = O − C'),('modeled_human_mm','Paired model H = A − C')]:
        g=ci[(ci.variable==var)&(ci.component==col)&(ci.block_years==2)].set_index('region');values.append(g.ols_slope_mm_year);titles.append(var+' '+label)
save(maps(values,titles,['OLS mm/year']*4),6,'Spatial residual and modeled human perturbation','Calendar-month fixed-effect slopes on the same observation-valid support. R includes the represented direct-human perturbation H and discrepancy E. Each panel has its own labelled scale to keep small H visible; compare numerical scales before comparing colours. These slopes are not additive Sen-slope fractions.','residual_spatial')
for n,var in [(7,'TWSA'),(8,'GWSA')]:
    def lines(code,var=var):
        g=at[(at.region==code)&(at.variable==var)];return [(g.date,g.residual_mm,'Residual R','#b66a3c','-'),(g.date,g.modeled_human_mm,'Modeled human H','#288c82','-')]
    save(panel(lines),n,var+' residual histories for all 22 basins','Observed-minus-naturalized residual R and paired modeled human perturbation H. Missing observed months are retained. R−H is unresolved observation–historical-model discrepancy; a negative R is not automatically measured pumping.','residual_'+var+'_temporal')
print('Rebuilding matched GLDAS and WaterGAP components',flush=True)
with xr.open_dataset(ROOT/'Thailand_Objective1/analysis_v3/netcdf/Thailand_TWSA_GWSA_components.nc',engine='h5netcdf') as d:noah=d.GLDAS_land_storage_anomaly.load().astype('float64')
land=0
for var in ['soilmoist','canopystor','swe']:
    with xr.open_dataset(ROOT/f'shared_data/WaterGAP/WaterGAP22e_ERA5_natural_{var}_Thailand_1981_2023.nc',engine='h5netcdf') as d:land=land+d[var].reindex(time=noah.time).interp(lat=noah.lat,lon=noah.lon,method='nearest').load().astype('float64')
common=land.notnull()&noah.notnull();ref=common&(noah.time.dt.year>=2004)&(noah.time.dt.year<=2009)
land=(land-land.where(ref).mean('time')).where(common);noah=(noah-noah.where(ref).mean('time')).where(common)
landrows=[];bench=[]
for code,name,w in region_weights(noah.lat,noah.lon):
    a,_=weighted_series(land,w,threshold=.5);b,_=weighted_series(noah,w,threshold=.5)
    landrows.append(pd.DataFrame({'date':noah.time.values,'region':code,'GLDAS_land_mm':b,'naturalized_land_mm':a}));bench.append({'region':code,**metrics(b,a)})
landts=pd.concat(landrows,ignore_index=True);landts.to_csv(T/'GLDAS_matched_land_timeseries.csv',index=False);bm=pd.DataFrame(bench)
old=pd.read_csv(E/'hydrological_benchmarks.csv',dtype={'region':str});old=old[old.variable=='land_storage'].set_index('region')
bench_differences=[]
for row in bench:
    for key in ['r','NSE','RMSE_mm']:
        delta=abs(row[key]-old.loc[row['region'],key]);bench_differences.append(delta)
        assert np.isclose(row[key],old.loc[row['region'],key],rtol=1e-5,atol=1e-5),(row['region'],key,delta)
bm.to_csv(T/'GLDAS_matched_land_metrics.csv',index=False)
ld=[]
for code,g in landts.groupby('region'):
    g=g.set_index('date');ld.append({'region':code,'GLDAS_slope_mm_year':ols(g.GLDAS_land_mm),'naturalized_slope_mm_year':ols(g.naturalized_land_mm)})
ld=pd.DataFrame(ld).set_index('region');ld['difference']=ld.naturalized_slope_mm_year-ld.GLDAS_slope_mm_year;ld.to_csv(T/'GLDAS_land_trend_comparison.csv')
save(maps([ld.GLDAS_slope_mm_year,ld.naturalized_slope_mm_year,ld.difference],['GLDAS Noah land storage','Naturalized model land storage','Naturalized minus GLDAS'],['OLS mm/year']*3,ncols=3),9,'Spatial GLDAS matched compartment comparison','Soil + canopy + snow only, common valid-cell support and common 2004–2009 reference. The record extends through December 2023. Each panel has a labelled scale; groundwater and surface water are excluded. This is a cross-model benchmark, not independent full-TWS or residual validation.','gldas_spatial')
def landlines(code):
    g=landts[landts.region==code];return [(g.date,g.GLDAS_land_mm,'GLDAS land storage','#4d7d8c','-'),(g.date,g.naturalized_land_mm,'Naturalized land storage','#b66a3c','-')]
save(panel(landlines),10,'Matched GLDAS time series for all 22 basins','Matched soil + canopy + snow anomalies in mm. GLDAS and WaterGAP share climatic influences. Agreement evaluates land-component consistency; it cannot validate groundwater or the entire human residual.','gldas_temporal_all_basins')
comparison=[];compts=[]
for code,g in landts.groupby('region'):
    g=g.set_index('date');tw=at[(at.region==code)&(at.variable=='TWSA')].set_index('date').residual_mm;gw=at[(at.region==code)&(at.variable=='GWSA')].set_index('date').residual_mm
    joined=pd.concat([g.GLDAS_land_mm,tw.rename('TWS_residual_mm'),gw.rename('GWS_residual_mm')],axis=1);joint=joined.dropna();zz=joint.apply(z);full=zz.reindex(joined.index)
    compts.append(full.reset_index().assign(region=code))
    comparison.append({'region':code,'n_months':len(joint),**{col+'_standardized_OLS_year':ols(zz[col]) for col in zz},'TWS_residual_GLDAS_r':correlation(joint.GLDAS_land_mm,joint.TWS_residual_mm,24),'GWS_residual_GLDAS_r':correlation(joint.GLDAS_land_mm,joint.GWS_residual_mm,24)})
cp=pd.DataFrame(comparison).set_index('region');cts=pd.concat(compts,ignore_index=True);cp.to_csv(T/'GLDAS_residual_comparison_metrics.csv');cts.to_csv(T/'GLDAS_residual_standardized_timeseries.csv',index=False)
save(maps([cp.GLDAS_land_mm_standardized_OLS_year,cp.TWS_residual_mm_standardized_OLS_year,cp.GWS_residual_mm_standardized_OLS_year,cp.TWS_residual_GLDAS_r,cp.GWS_residual_GLDAS_r,bm.set_index('region').r],['GLDAS standardized trend','TWS residual standardized trend','GWS residual standardized trend','GLDAS / TWS residual r','GLDAS / GWS residual r','Matched land-model / GLDAS r'],['SD/year']*3+['Pearson r']*3,limits=[(-.2,.2)]*3+[(-1,1)]*3,ncols=3),11,'Spatial GLDAS and residual comparisons','Top: slopes of separately standardized series on identical joint months; scale saturates at ±0.2 SD/year. Bottom: descriptive correlations, with the matched land-component correlation for context. GLDAS land storage and residual storage are different quantities. No cross-compartment NSE, RMSE or claim of human validation is made. GLDAS also contributes to GWS subtraction.','gldas_residual_spatial')
def complines(code):
    g=cts[cts.region==code];return [(g.date,g.GLDAS_land_mm,'GLDAS land','#4d7d8c','-'),(g.date,g.TWS_residual_mm,'TWS residual','#b66a3c','-'),(g.date,g.GWS_residual_mm,'GWS residual','#7b78a4','-')]
save(panel(complines,'Standard deviation units'),12,'GLDAS and residual histories for all 22 basins','Each variable is standardized on the same jointly observed months within each basin. Different compartments are compared in timing and shape, not treated as equivalent water volumes. Missing months remain gaps. This is a dependence diagnostic, not independent anthropogenic validation.','gldas_residual_temporal')
print('Generating spatial and temporal evaluation metrics',flush=True)
vals=[];titles=[];labels=[];lims=[];cm=[]
for var in ['TWSA','GWSA']:
    g=ev[ev.variable==var].set_index('region')
    for key,title,lim,cmap in [('NSE','Raw NSE',(-1,1),'RdYlGn'),('deseasonalized_NSE','Anomaly NSE',(-1,1),'RdYlGn'),('RMSE_mm','RMSE',(0,max(1,float(g.RMSE_mm.max()))),'YlOrRd')]:vals.append(g[key]);titles.append(var+' '+title);labels.append('mm' if key=='RMSE_mm' else 'NSE');lims.append(lim);cm.append(cmap)
save(maps(vals,titles,labels,lims,cm,ncols=3),13,'Spatial climate model evaluation','Frozen ensemble verification against naturalized parent storage during 2016–2023. Maps distinguish raw NSE, training-climatology-anomaly NSE and RMSE; NSE colours saturate below −1. High seasonal skill is not observational validation of a natural counterfactual.','climate_evaluation_spatial')
annualmetrics=[]
for (code,var),g in pred[pred.date.dt.year.between(2016,2023)].groupby(['region','variable']):
    for year,q in g.groupby(g.date.dt.year):
        m=metrics(q.naturalized_target_mm,q.emulator_mm);am=metrics(q.naturalized_target_mm-q.climatology_mm,q.emulator_mm-q.climatology_mm)
        annualmetrics.append({'region':code,'variable':var,'year':year,**m,'anomaly_NSE':am['NSE']})
am=pd.DataFrame(annualmetrics);am.to_csv(T/'climate_evaluation_by_test_year.csv',index=False)
fig,axes=plt.subplots(2,2,figsize=(11,7.6))
for row,var in enumerate(['TWSA','GWSA']):
    for col,key,label in [(0,'anomaly_NSE','Anomaly NSE'),(1,'RMSE_mm','RMSE (mm)')]:
        ax=axes[row,col];g=am[(am.variable==var)&(am.region!='TH')].groupby('year')[key];q=g.quantile([.25,.5,.75]).unstack();ax.fill_between(q.index,q[.25],q[.75],color='#b7d3d0',label='Basin interquartile range');ax.plot(q.index,q[.5],color='#288c82',label='Basin median');n=am[(am.variable==var)&(am.region=='TH')];ax.plot(n.year,n[key],'o-',color='#173c50',label='National');ax.set(title=var+' '+label,xlabel='Held-out calendar year',ylabel=label)
        if col==0:ax.axhline(0,color='#aaa',lw=.8)
axes[0,0].legend(fontsize=10);fig.tight_layout();save(fig,14,'Climate model evaluation through time','Metrics are calculated separately for each held-out year using the training-climatology anomaly definition. Shading is spatial interquartile variation, not a confidence interval. Annual scores use 12 modeled months and may be unstable when anomaly variance is small; pooled 96-month results remain primary.','climate_evaluation_temporal')
vals=[];titles=[];labels=[];lims=[];cm=[]
for var in ['TWSA','GWSA']:
    g=well[(well.variable==var)&(well.component=='residual_mm')&(well.quality=='retained_flags')].set_index('region')
    for key,title in [('r','Raw head correlation'),('detrended_r','Detrended head correlation'),('n_years','Matched annual support')]:
        v=g[key].copy()
        if key!='n_years':v[g.n_years<8]=np.nan
        vals.append(v);titles.append(var+' '+title);labels.append('Years' if key=='n_years' else 'Pearson r');lims.append((0,max(g.n_years.max(),1)) if key=='n_years' else (-1,1));cm.append('YlGnBu' if key=='n_years' else 'RdBu')
save(maps(vals,titles,labels,lims,cm,ncols=3),15,'Spatial evaluation of residual agreement with groundwater','Observed annual heads compared separately with TWS and GWS residuals. Hatching marks unavailable correlations or fewer than eight matched years. Support maps expose small samples. Heads and equivalent water depth are not commensurate volumes, so head–storage NSE and RMSE are not calculated. Raw association is indirect groundwater evidence for TWS, not total-human validation.','residual_validation_spatial')
d=pd.read_csv(ROOT/'Thailand_Objective2/analysis_v3/tables/groundwater_signed_anomalies.csv',dtype={'region':str},parse_dates=['date']);av=[]
for code in ['TH']+codes:
    v=d if code=='TH' else d[d.region==code];v=v[(v.interval=='YS')&v.head_z.notna()];station=v.groupby(['date','station_group']).head_z.median().unstack('station_group').sort_index()
    for var in ['TWSA','GWSA']:
        g=at[(at.region==code)&(at.variable==var)].set_index('date');y=annual(g.residual_mm);c=annual(g.climate_mm);idx=y.index.union(station.index).intersection(c.index);M=station.reindex(idx).to_numpy();yy=y.reindex(idx).to_numpy();cc=c.reindex(idx).to_numpy()
        if M.shape[1]:M=M[:,np.isfinite(M[np.isfinite(yy)&np.isfinite(cc)]).any(axis=0)]
        with warnings.catch_warnings():warnings.simplefilter('ignore');head=np.nanmean(M,axis=1) if M.shape[1] else np.full(len(idx),np.nan)
        ok=np.isfinite(head)&np.isfinite(yy)&np.isfinite(cc);got=correlation(head[ok],yy[ok]);expected=well[(well.region==code)&(well.variable==var)&(well.component=='residual_mm')&(well.quality=='retained_flags')].iloc[0]
        if np.isfinite(expected.r):assert abs(got-expected.r)<1e-9,(code,var,got,expected.r)
        av.append(pd.DataFrame({'date':idx,'region':code,'variable':var,'head_index':np.where(ok,head,np.nan),'residual_mm':np.where(ok,yy,np.nan),'matched_station_groups':np.isfinite(M).sum(axis=1) if M.shape[1] else 0}))
av=pd.concat(av,ignore_index=True);av.to_csv(T/'annual_residual_groundwater_validation_series.csv',index=False)
def welllines(code):
    g=av[(av.region==code)&(av.variable=='GWSA')].set_index('date');tw=av[(av.region==code)&(av.variable=='TWSA')].set_index('date').residual_mm.reindex(g.index);joint=pd.concat([g.head_index,g.residual_mm,tw.rename('TWS_residual')],axis=1).dropna();zz=joint.apply(z).reindex(g.index)
    return [(zz.index,zz.head_index,'Head index','#173c50','-'),(zz.index,zz.residual_mm,'GWS residual','#7b78a4','-'),(zz.index,zz.TWS_residual,'TWS residual','#b66a3c','-')]
save(panel(welllines,'Standard deviation units'),16,'Annual groundwater and residual histories for all 22 basins','Co-located wells are first grouped by station, then averaged. Displayed series are standardized on their joint annual support; they are not water-volume conversions. Annual storage requires at least eight valid months and complete year endpoints. Gaps remain missing. Numerical correlation maps use each target’s own longest eligible support, whereas this three-line display uses joint support.','residual_validation_temporal')
vals=[];titles=[]
for var in ['TWSA','GWSA']:
    g=res[(res.variable==var)&(res.component=='residual_mm')&(res.level==1)].set_index('region');v=g.r_month_trend_removed.copy();v[g.n_months<24]=np.nan;vals.append(v);titles.append(var+' / reservoirs, adjusted r')
g=res[(res.variable=='TWSA')&(res.component=='residual_mm')&(res.level==1)].set_index('region');vals.append(g.reservoir_count);titles.append('Fixed pre-2004 reservoir count')
save(maps(vals,titles,['Pearson r','Pearson r','Reservoirs'],limits=[(-1,1),(-1,1),(0,max(g.reservoir_count.max(),1))],cmaps=['RdBu','RdBu','YlGnBu'],ncols=3),17,'Spatial independent reservoir component evidence','MSEA-Res Level-1 scene estimates, fixed pre-2004 populations and matched-month season/trend-adjusted correlations. Grey hatching means unavailable evidence, not zero effect. Reservoir correlations with GWS residuals are dependence diagnostics and do not directly validate groundwater. No naturalized observed reservoir counterfactual is available.','reservoir_validation_spatial')
rolling=[]
for (code,var),g in av.groupby(['region','variable']):
    g=g.set_index('date')
    for end in range(2011,2024):
        q=g[g.index.year.to_series(index=g.index).between(end-7,end)];ok=q[['head_index','residual_mm']].dropna();rolling.append({'region':code,'variable':var,'end_year':end,'window_years':8,'n_years':len(ok),'r':correlation(ok.head_index,ok.residual_mm)})
roll=pd.DataFrame(rolling);roll.to_csv(T/'residual_head_rolling_correlations.csv',index=False)
fig,axes=plt.subplots(2,2,figsize=(11,7.5))
for row,var in enumerate(['TWSA','GWSA']):
    a=axes[row,0];b=axes[row,1];n=roll[(roll.region=='TH')&(roll.variable==var)];a.plot(n.end_year,n.r,'o-',color='#173c50');a.set(title=var+' residual / head, 8-year windows',xlabel='Window ending year',ylabel='Pearson r',ylim=(-1,1));a.axhline(0,color='#aaa',lw=.8)
    q=av[(av.region=='TH')&(av.variable==var)];b.bar(q.date.dt.year,q.matched_station_groups,color='#528e97');b.set(title=var+' matched head-network support',xlabel='Calendar year',ylabel='Coordinate station groups')
fig.tight_layout();save(fig,18,'Residual validation metrics and network support through time','National rolling head–residual correlations require at least six observed annual pairs in an eight-calendar-year window. Windows overlap and are descriptive, not independent tests or a model-selection device. Bars show represented coordinate-station groups; station counts are not the temporal correlation sample size. Basin-specific rolling metrics accompany the figure.','residual_evaluation_temporal')
(A/'figure_inventory.json').write_text(json.dumps(inventory,indent=2,ensure_ascii=False),encoding='utf-8')
qa={'passed':True,'figures':len(inventory),'basin_subplots_per_temporal_atlas':22,'GLDAS_matched_metrics_reproduced':True,'GLDAS_max_float_precision_difference':max(bench_differences),'GLDAS_comparison_tolerance':'rtol=1e-5, atol=1e-5; explicit float64 rebasing versus retained float32 Noah baseline','annual_groundwater_correlations_reproduced':True,'cross_compartment_volume_error_metrics_avoided':True,'original_scientific_tables_unchanged':True,'time_gaps_retained':True,'missing_spatial_evidence_hatched':True,'climate_test':'2016–2023; frozen ensemble; no test refitting','comparison_scope':'GLDAS land and residual timing/shape, not human-only ground truth'}
(A/'logs/figure_qa.json').write_text(json.dumps(qa,indent=2));print(json.dumps(qa,indent=2),flush=True)
