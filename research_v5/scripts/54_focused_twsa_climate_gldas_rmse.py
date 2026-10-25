"""Focused spatial/temporal plots with explicitly matched RMSE targets."""
from pathlib import Path
import os,json,shutil,zipfile,textwrap,hashlib
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
os.environ['MKL_NUM_THREADS']='1'
import numpy as np,pandas as pd,geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize,TwoSlopeNorm
from matplotlib.ticker import MaxNLocator
import matplotlib.dates as mdates
from pypdf import PdfReader,PdfWriter
R=Path(os.environ.get('TWSA_RESEARCH_ROOT',Path(__file__).resolve().parents[1])).resolve();O=R/'Thailand_Research_v5';D=O/'focused_twsa_climate_gldas_rmse';F=D/'figures';T=D/'tables'
for p in [F,T,D/'qa']:p.mkdir(parents=True,exist_ok=True)
read=lambda p:pd.read_csv(p,dtype={'region':str})
at=read(O/'tables/CSR_naturalized_attribution.csv');at=at[at.variable=='TWSA'].copy();at['date']=pd.to_datetime(at.date)
pred=read(R/'Thailand_Objective2/analysis_v4/tables/climate_emulator_timeseries.csv');pred=pred[pred.variable=='TWSA'].copy();pred['date']=pd.to_datetime(pred.date)
land=read(O/'figure_revision/tables/GLDAS_matched_land_timeseries.csv');land['date']=pd.to_datetime(land.date)
names=dict(zip(at.region,at.region_name));codes=sorted(c for c in names if c!='TH')
geo=gpd.read_file(R/'Thailand_Objective2/data/BASINS/MainBasin_ONWR_Law_WGS84.shp').to_crs(4326);geo['region']=geo.MB_CODE.astype(str).str.split('-').str[0].str.zfill(2);geo=geo.dissolve(by='region',as_index=False,aggfunc='first');geo.geometry=geo.geometry.simplify(.006,preserve_topology=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':15,'axes.spines.top':False,'axes.spines.right':False})
inventory=[]
def rmse(a,b):
    q=np.isfinite(a)&np.isfinite(b)
    return float(np.sqrt(np.mean((np.asarray(a)[q]-np.asarray(b)[q])**2))) if q.any() else np.nan
comparisons={
 'emulator_parent':('Climate emulator / naturalized TWSA','naturalized_target_mm','emulator_mm',pred,'Parent-model reconstruction'),
 'baseline_GRACE':('Climate baseline / GRACE TWSA','observed_mm','climate_mm',at,'Observed full-TWS benchmark'),
 'land_GLDAS':('WaterGAP land / GLDAS Noah','GLDAS_land_mm','naturalized_land_mm',land,'Matched soil + canopy + snow benchmark')}
# Reproduce the existing pooled values before computing focused annual results.
ev=read(R/'Thailand_Objective2/analysis_v4/tables/climate_emulator_validation.csv');ev=ev[(ev.variable=='TWSA')&(ev.model=='Ensemble')&(ev.period=='Test')].set_index('region')
obm=read(O/'tables/CSR_model_observation_benchmarks.csv');obm=obm[(obm.variable=='TWSA')&(obm.model=='naturalized')].set_index('region')
lm=read(O/'figure_revision/tables/GLDAS_matched_land_metrics.csv').set_index('region')
for code in ['TH',*codes]:
    p=pred[(pred.region==code)&pred.date.dt.year.between(2016,2023)]
    a=at[at.region==code];l=land[land.region==code]
    assert np.isclose(rmse(p.naturalized_target_mm,p.emulator_mm),ev.loc[code,'RMSE_mm'],rtol=1e-5,atol=1e-5)
    assert np.isclose(rmse(a.observed_mm,a.climate_mm),obm.loc[code,'RMSE_mm'],rtol=1e-5,atol=1e-5)
    assert np.isclose(rmse(l.GLDAS_land_mm,l.naturalized_land_mm),lm.loc[code,'RMSE_mm'],rtol=1e-5,atol=1e-5)
pooled=[];annual=[]
for key,(title,y,p,frame,role) in comparisons.items():
    for code in ['TH',*codes]:
        g=frame[(frame.region==code)&frame.date.dt.year.between(2016,2023)].dropna(subset=[y,p])
        pooled.append({'region':code,'basin':names[code],'comparison':key,'label':title,'role':role,'period':'2016–2023','n_months':len(g),'RMSE_mm':rmse(g[y],g[p])})
        for year in range(2016,2024):
            z=g[g.date.dt.year==year];annual.append({'region':code,'basin':names[code],'comparison':key,'year':year,'n_months':len(z),'RMSE_mm':rmse(z[y],z[p]) if len(z)>=8 else np.nan,'status':'estimated' if len(z)>=8 else 'fewer than eight paired months'})
pooled=pd.DataFrame(pooled);annual=pd.DataFrame(annual)
pooled.to_csv(T/'pooled_RMSE_2016_2023.csv',index=False);annual.to_csv(T/'annual_RMSE_2016_2023.csv',index=False)
pred.to_csv(T/'climate_TWSA_reconstruction_series.csv',index=False);land.to_csv(T/'GLDAS_matched_land_series.csv',index=False)
at[['date','region','region_name','observed_mm','climate_mm']].to_csv(T/'observed_and_climate_TWSA_series.csv',index=False)
def save(fig,n,title,note):
    fig.tight_layout();stem=f'{n:02d}_'+['','storage_spatial','national_temporal','climate_TWSA_all_basins','GLDAS_land_all_basins','RMSE_spatial','RMSE_annual','RMSE_all_basins'][n]
    for ext in ['png','pdf']:fig.savefig(F/(stem+'.'+ext),dpi=180,bbox_inches='tight')
    plt.close(fig);inventory.append({'id':n,'title':title,'file':stem+'.png','pdf':stem+'.pdf','note':note});print('Saved',stem,flush=True)
def maps(vals,titles,units,positive=False):
    fig,axes=plt.subplots(1,len(vals),figsize=(5.4*len(vals),6.5),squeeze=False)
    for ax,v,title,unit in zip(axes.ravel(),vals,titles,units):
        g=geo.merge(v.rename('value'),left_on='region',right_index=True,how='left');m=max(g.value.abs().max(),.001)
        norm=Normalize(0,m) if positive else TwoSlopeNorm(vmin=-m,vcenter=0,vmax=m);cmap='YlOrRd' if positive else 'RdBu'
        g.plot(column='value',ax=ax,cmap=cmap,norm=norm,edgecolor='#73818a',linewidth=.5,missing_kwds={'color':'#ddd','hatch':'///'})
        ax.set_title(textwrap.fill(title,27),fontsize=20);ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
        cb=fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=cmap),ax=ax,fraction=.045,pad=.025);cb.set_label(unit,fontsize=18)
    return fig
def slope(g,col):
    d=pd.DatetimeIndex(g.date);X=np.column_stack([np.ones(len(g)),(d.year-2003)+(d.month-1)/12,pd.get_dummies(d.month,drop_first=True,dtype=float)])
    return np.linalg.lstsq(X,g[col].to_numpy(),rcond=None)[0][1]
joint=at[['date','region','observed_mm','climate_mm']].merge(land[['date','region','GLDAS_land_mm']],on=['date','region'],validate='one_to_one')
joint=joint[joint.date.dt.year.between(2003,2023)].dropna(subset=['observed_mm','climate_mm','GLDAS_land_mm'])
tr=[]
for code,g in joint.groupby('region'):
    tr.append({'region':code,'basin':names[code],'n_common_months':len(g),**{c:slope(g,c) for c in ['observed_mm','climate_mm','GLDAS_land_mm']}})
tr=pd.DataFrame(tr).set_index('region');tr.to_csv(T/'common_month_storage_trends_2003_2023.csv')
save(maps([tr[c] for c in ['observed_mm','climate_mm','GLDAS_land_mm']],['GRACE observed TWSA','Naturalized climate TWSA','GLDAS Noah land storage'],['OLS mm/year']*3),1,'Spatial storage trends','2003–2023 common available months within each basin; calendar-month fixed-effect OLS. These differ from full-record seasonal Sen slopes. GLDAS land storage excludes groundwater and surface water. Each panel has its own scale; the three storage definitions are not interchangeable.')
fig,ax=plt.subplots(2,1,figsize=(13,8),sharex=True)
g=at[at.region=='TH'].set_index('date').reindex(pd.date_range('2003-01-01','2023-12-01',freq='MS'))
for c,label,color in [('observed_mm','GRACE TWSA','#173c50'),('climate_mm','Naturalized climate TWSA','#b66a3c')]:ax[0].plot(g.index,g[c],label=label,color=color,lw=1.4)
g=land[land.region=='TH'].set_index('date').reindex(pd.date_range('2003-01-01','2023-12-01',freq='MS'))
for c,label,color in [('GLDAS_land_mm','GLDAS Noah land storage','#173c50'),('naturalized_land_mm','WaterGAP matching land storage','#b66a3c')]:ax[1].plot(g.index,g[c],label=label,color=color,lw=1.4)
for a,title in zip(ax,['Total water storage','Soil + canopy + snow storage']):a.set_title(title,fontsize=19);a.set_ylabel('Anomaly (mm)');a.legend(frameon=False,ncol=2,fontsize=13);a.axhline(0,color='#aaa',lw=.5)
ax[1].set_xlabel('Year');save(fig,2,'National temporal comparison','Separate panels retain different storage definitions. Top: observed and naturalized total storage. Bottom: matching land compartments. Gaps are retained; no direct full-TWS error is assigned to partial GLDAS land storage.')
inv=json.loads((O/'figure_revision/figure_inventory.json').read_text(encoding='utf-8'))
for n,old in [(3,4),(4,10)]:
    x=next(x for x in inv if x['id']==old)
    fig,axes=plt.subplots(6,4,figsize=(13,14),sharex=True);handles=[]
    cols=[('naturalized_target_mm','Naturalized parent','#173c50'),('emulator_mm','Climate emulator','#b66a3c')] if n==3 else [('GLDAS_land_mm','GLDAS land storage','#4d7d8c'),('naturalized_land_mm','WaterGAP matching land storage','#b66a3c')]
    for i,code in enumerate(codes):
        ax=axes.ravel()[i];g=(pred if n==3 else land);g=g[(g.region==code)&(g.date.dt.year>=2002)].set_index('date').sort_index();g=g.reindex(pd.date_range(g.index.min(),g.index.max(),freq='MS'))
        for col,label,color in cols:
            h,=ax.plot(g.index,g[col],label=label,color=color,lw=1.1,ls='--' if col=='emulator_mm' else '-')
            if i==0:handles.append(h)
        if n==3:ax.axvspan(pd.Timestamp('2016-01-01'),pd.Timestamp('2023-12-31'),color='#288c82',alpha=.10,zorder=-5)
        ax.set_title(code+' '+names[code][:16],loc='left',fontsize=12,color='#173c50',pad=5);ax.yaxis.set_major_locator(MaxNLocator(3));ax.tick_params(labelsize=10,labelbottom=True);ax.xaxis.set_major_locator(mdates.YearLocator(10));ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'));ax.axhline(0,color='#b9c3c9',lw=.5)
    for ax in axes.ravel()[22:]:ax.set_visible(False)
    fig.legend(handles=handles,loc='lower right',bbox_to_anchor=(.98,.075),fontsize=12,frameon=False,ncol=1);fig.supylabel('Storage anomaly (mm)',fontsize=16);fig.supxlabel('Year · full basin names are retained in the supplied CSV tables',fontsize=13)
    save(fig,n,x['title'],x['caption'])
keys=list(comparisons);labels=[comparisons[k][0] for k in keys];colors=['#173c50','#b66a3c','#288c82']
save(maps([pooled[pooled.comparison==k].set_index('region').RMSE_mm for k in keys],labels,['RMSE (mm)']*3,positive=True),5,'Spatial RMSE by evaluation target','Pooled 2016–2023 metrics. Climate reconstruction targets naturalized TWSA; the climate baseline is separately compared with observed GRACE TWSA; land storage is compared with matching GLDAS compartments. Pair counts differ because GRACE has gaps. Compare basins within the same panel, rather than ranking models across different targets.')
fig,axes=plt.subplots(3,1,figsize=(12,10),sharex=True)
for ax,key,label,color in zip(axes,keys,labels,colors):
    q=annual[(annual.comparison==key)&(annual.region!='TH')].groupby('year').RMSE_mm.quantile([.25,.5,.75]).unstack();national=annual[(annual.comparison==key)&(annual.region=='TH')]
    ax.fill_between(q.index,q[.25],q[.75],color=color,alpha=.2,label='Basin interquartile range');ax.plot(q.index,q[.5],color=color,ls='--',label='Basin median');ax.plot(national.year,national.RMSE_mm,'o-',color=color,label='National');ax.set_title(label,fontsize=18);ax.set_ylabel('RMSE (mm)')
axes[0].legend(frameon=False,ncol=3,fontsize=12);axes[-1].set_xlabel('Evaluation year');save(fig,6,'Annual RMSE through time','Years 2016–2023; at least eight paired months are required per annual score. GRACE mission-gap years may have no score. Shading describes variation among basins, not a confidence interval. Each panel has its own vertical scale and evaluation target.')
fig,axes=plt.subplots(6,4,figsize=(13,14),sharex=True);handles=[]
for i,code in enumerate(codes):
    ax=axes.ravel()[i]
    for key,label,color in zip(keys,labels,colors):
        g=annual[(annual.region==code)&(annual.comparison==key)];h,=ax.plot(g.year,g.RMSE_mm,'o-',color=color,lw=1.2,ms=3,label=label)
        if i==0:handles.append(h)
    ax.set_title(code,loc='left',fontsize=17);ax.yaxis.set_major_locator(MaxNLocator(3));ax.set_xticks([2016,2020,2023]);ax.tick_params(labelsize=12,labelbottom=True)
for ax in axes.ravel()[22:]:ax.set_visible(False)
fig.legend(handles=handles,loc='lower right',ncol=1,frameon=False,fontsize=13,bbox_to_anchor=(.98,.07));fig.supylabel('Annual RMSE (mm)',fontsize=17);fig.supxlabel('Year · basin codes match the supplied CSV names',fontsize=14);save(fig,7,'Annual RMSE for all 22 basins','All three explicitly labelled evaluation targets are retained. Different targets and compartment variances prevent interpreting a smaller cross-target RMSE as a better climate model. Missing annual scores remain gaps.')
inventory.sort(key=lambda x:x['id']);(D/'figure_inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2),encoding='utf-8')
writer=PdfWriter()
for x in inventory:writer.append(PdfReader(F/x['pdf']))
writer.add_metadata({'/Title':'Thailand TWSA climate GLDAS and RMSE spatial temporal plots','/Author':'Farzeen Khan'});writer.write(D/'TWSA_Climate_GLDAS_RMSE_Plots.pdf');assert len(PdfReader(D/'TWSA_Climate_GLDAS_RMSE_Plots.pdf').pages)==7
guide='# Focused TWSA climate, GLDAS and RMSE plots\n\n'
guide+='Climate baseline means naturalized WaterGAP TWSA. Climate emulator means the weather-based reconstruction of that parent target. GLDAS land storage means soil + canopy + snow; it excludes groundwater and surface water.\n\n'
for x in inventory:guide+=f"## Figure {x['id']} {x['title']}\n\n{x['note']}\n\n"
guide+='RMSE maps and annual plots use 2016–2023; annual scores require eight observed pairs. Spatial storage trends use 2003–2023 common available months and month-effect OLS, not the main report seasonal Sen estimates. Full-precision CSV values, sample counts and basin names are included. Rebuild after the complete scientific run by setting TWSA_RESEARCH_ROOT and running script 54. Install the additional PDF dependency with: python -m pip install pypdf==6.21.2 . All other numerical dependencies are in the main research lock file. Scientific models are not refitted.\n'
(D/'README.md').write_text(guide,encoding='utf-8')
with zipfile.ZipFile(D/'TWSA_Climate_GLDAS_RMSE_Source_Plots.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in [*sorted(F.glob('*')),*sorted(T.glob('*.csv')),D/'README.md',D/'figure_inventory.json']:z.write(p,p.relative_to(D))
    z.write(Path(__file__),'code/54_focused_twsa_climate_gldas_rmse.py')
(D/'qa/checks.json').write_text(json.dumps({'passed':True,'figures':7,'basins':22,'pooled_RMSE_targets_verified':69,'evaluation_period':'2016–2023','annual_min_pairs':8,'no_refitting':True,'national_pooled_RMSE':pooled[pooled.region=='TH'].to_dict('records')},indent=2),encoding='utf-8')
print('Focused spatial/temporal plot package complete.')
