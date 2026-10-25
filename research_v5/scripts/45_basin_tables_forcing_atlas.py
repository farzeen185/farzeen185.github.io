"""Tabulate verified basin results and plot actual forcing/supporting datasets.

No model is refitted. All summaries use saved, reproducible basin series.
"""
from pathlib import Path
import os,json,gc,textwrap,hashlib
import numpy as np,pandas as pd,geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import Normalize,TwoSlopeNorm
from matplotlib.ticker import MaxNLocator
R=Path(os.environ.get('TWSA_RESEARCH_ROOT',Path(__file__).resolve().parents[1])).resolve()
O=R/'Thailand_Research_v5';A=O/'basin_forcing_appendix';F=A/'figures';T=A/'tables'
for p in [F,T,A/'logs']:p.mkdir(parents=True,exist_ok=True)
read=lambda name:pd.read_csv(O/'tables'/name,dtype={'region':str})
geo=gpd.read_file(R/'Thailand_Objective2/data/BASINS/MainBasin_ONWR_Law_WGS84.shp').to_crs(4326)
geo['region']=geo.MB_CODE.astype(str).str.split('-').str[0].str.zfill(2)
geo=geo.dissolve(by='region',as_index=False,aggfunc='first');geo.geometry=geo.geometry.simplify(.006,preserve_topology=True)
codes=sorted(geo.region);tr=read('CSR_basin_trends.csv');names=dict(zip(tr.region,tr.region_name))
ev=pd.read_csv(R/'Thailand_Objective2/analysis_v4/tables/climate_emulator_validation.csv',dtype={'region':str})
ev=ev[(ev.model=='Ensemble')&(ev.period=='Test')]
ci=read('attribution_wild_block_intervals.csv');ci=ci[ci.block_years==2]
well=read('CSR_groundwater_network_evidence.csv');well=well[(well.component=='residual_mm')&(well.quality=='retained_flags')]
gld=pd.read_csv(O/'figure_revision/tables/GLDAS_matched_land_metrics.csv',dtype={'region':str})
reservoir=read('independent_reservoir_evidence.csv');reservoir=reservoir[(reservoir.component=='residual_mm')&(reservoir.level==1)&(reservoir.variable=='TWSA')]
stress=read('precipitation_source_stress_test.csv')
base=pd.DataFrame({'region':codes,'basin':[names[c] for c in codes]})
tables=[]
def table(id,title,frame,headers,cols,note):
    frame=base[['region','basin']].merge(frame,on='region',how='left',validate='one_to_one')
    assert list(frame.region)==codes and len(frame)==22
    file=f'C{id:02d}_basin_values.csv';frame.to_csv(T/file,index=False)
    tables.append({'id':id,'title':title,'file':file,'headers':headers,'columns':cols,'note':note})

q=base[['region']].copy()
for var,prefix in [('TWSA','TWS'),('GWSA','GWS')]:
    g=tr[tr.variable==var].set_index('region')
    for field,out in [('sen_slope_mm_year','slope'),('mk_seasonal_q_FDR','q'),('n_months','n')]:q[prefix+'_'+out]=q.region.map(g[field])
table(1,'Observed storage trends for every basin',q,['Basin','TWS slope','TWS q','n','GWS slope','GWS q','n'],['region','TWS_slope','TWS_q','TWS_n','GWS_slope','GWS_q','GWS_n'],'Slopes are seasonal Sen estimates in mm/year. q is seasonal Mann–Kendall FDR across basins; n is observed months. Full intervals and original p-values remain in CSR_basin_trends.csv. Basin names are listed in Appendix A.')
for id,var in [(2,'TWSA'),(3,'GWSA')]:
    g=ev[ev.variable==var][['region','n','r','NSE','deseasonalized_NSE','RMSE_mm','MAE_mm']]
    table(id,var+' climate reconstruction performance',g,['Basin','n','r','NSE','Anom NSE','RMSE','MAE'],list(g.columns),'Frozen ensemble, 2016–2023 test data. Target: naturalized WaterGAP, not GRACE. Errors are mm; anomaly NSE removes the training monthly climatology. Higher NSE and lower errors are better.')
for id,var in [(4,'TWSA'),(5,'GWSA')]:
    g=ci[ci.variable==var].pivot(index='region',columns='component',values='ols_slope_mm_year').reset_index()
    cols=['region','observed_mm','climate_mm','modeled_human_mm','residual_mm','discrepancy_mm']
    table(id,var+' additive trends and residual components',g[cols],['Basin','O','C','H','R','E'],cols,'Calendar-month fixed-effect OLS slopes, mm/year, on common available months. O observed; C naturalized; H historical minus naturalized; R observed minus naturalized; E observed minus historical. R = H + E. These are not additive Sen slopes or measured pumping rates. Conditional intervals are supplied in attribution_wild_block_intervals.csv.')
table(6,'GLDAS matched land storage performance',gld[['region','n','r','NSE','RMSE_mm','MAE_mm','bias_mm']],['Basin','n','r','NSE','RMSE','MAE','Bias'],['region','n','r','NSE','RMSE_mm','MAE_mm','bias_mm'],'Soil, canopy and snow only; naturalized WaterGAP compared with GLDAS Noah on matched months. Errors are mm; bias = WaterGAP minus GLDAS. This does not validate full TWS, GWS or human-only storage.')
q=base[['region']].copy()
for var,p in [('TWSA','TWS'),('GWSA','GWS')]:
    g=well[well.variable==var].set_index('region')
    for f in ['r','detrended_r','n_years']:q[p+'_'+f]=q.region.map(g[f])
table(7,'Residual agreement with annual groundwater head',q,['Basin','TWS r','TWS detr r','Years','GWS r','GWS detr r','Years'],['region','TWS_r','TWS_detrended_r','TWS_n_years','GWS_r','GWS_detrended_r','GWS_n_years'],'Longest-overlap retained-flags panel. Positive r means lower residual tends to occur with lower head. Detr r removes a linear trend. An em dash means unavailable evidence, not zero. Head is not converted into storage; no cross-unit NSE or RMSE is reported. Other station panels and conditional intervals remain in the complete CSV.')
rc=['region','reservoir_count','n_months','r_raw','r_month_trend_removed','adjusted_r_year_cluster_boot_ci_low','adjusted_r_year_cluster_boot_ci_high']
table(8,'TWS residual agreement with independent reservoir storage',reservoir[rc],['Basin','Reservoirs','Months','Raw r','Adjusted r','95% low','95% high'],rc,'Scene-screened Level 1 estimates; fixed pre-2004 reservoir panel. Adjusted correlation removes season and trend. Intervals resample whole calendar years. Missing or insufficient evidence is left unavailable. This checks a surface-water component, not a human-only total.')
q=base[['region']].copy()
for var,p in [('TWSA','TWS'),('GWSA','GWS')]:
    for src,s in [('Native_GSWP3_ERA5','Native'),('CHIRPS_unadjusted','CHIRPS')]:
        g=stress[(stress.variable==var)&(stress.P_source==src)].set_index('region')
        q[p+'_'+s]=q.region.map(g.deseasonalized_NSE)
table(9,'Rainfall source sensitivity in the controlled Ridge model',q,['Basin','TWS native','TWS CHIRPS','GWS native','GWS CHIRPS'],list(q.columns),'Test-period anomaly NSE for the frozen Weather_memory Ridge experiment, holding PET and the native-forced parent target fixed. CHIRPS is unadjusted here. This is forcing sensitivity, not evidence that one rainfall product is more accurate. It is a different experiment from the ensemble in Tables C.2–C.3.')

# The same meteorological basin series are repeated by storage target in the
# saved parent table. Check equality before retaining just one copy.
raw=pd.read_csv(R/'Thailand_Objective2/analysis_v4/tables/naturalized_attribution_timeseries.csv',dtype={'region':str},parse_dates=['date'])
keys=['precipitation_mm_day','potential_ET_mm_day']
for k in keys:
    wide=raw.pivot(index=['region','date'],columns='variable',values=k)
    assert np.allclose(wide.TWSA,wide.GWSA,equal_nan=True),k
raw=raw[raw.variable=='TWSA'][['date','region',*keys]].copy()
raw['Native_P']=raw.precipitation_mm_day*raw.date.dt.days_in_month
raw['Native_PET']=raw.potential_ET_mm_day*raw.date.dt.days_in_month
aux=read('multisource_hydroclimate_series.csv');aux['date']=pd.to_datetime(aux.date)
auxvars=['CHIRPS_P','GLEAM_ET','MODIS_ET','ESA_CCI_SSM','ESA_CCI_RZSM','MODIS_LST']
data=raw[['date','region','Native_P','Native_PET']].merge(aux[['date','region',*auxvars,*[x+'_coverage' for x in auxvars]]],on=['date','region'],how='outer',validate='one_to_one')
data=data[data.date.dt.year.between(2003,2023)].sort_values(['region','date'])
data.to_csv(T/'forcing_monthly_series_2003_2023.csv',index=False)
variables={
 'Native_P':('Native precipitation','mm/month','Primary meteorological predictor'),
 'Native_PET':('Native potential ET','mm/month','Primary meteorological predictor'),
 'CHIRPS_P':('CHIRPS precipitation','mm/month','Alternative forcing in rainfall sensitivity test'),
 'GLEAM_ET':('GLEAM actual ET','mm/month','Supporting context; not a primary climate predictor'),
 'MODIS_ET':('MODIS actual ET','mm/month','Supporting context; not a primary climate predictor'),
 'ESA_CCI_SSM':('ESA CCI surface moisture','m³/m³','Supporting context; not a primary climate predictor'),
 'ESA_CCI_RZSM':('ESA CCI root zone moisture','m³/m³','Supporting context; not a primary climate predictor'),
 'MODIS_LST':('MODIS surface temperature','°C','Supporting context; not a primary climate predictor')}
stats=[]
for code,g in data.groupby('region'):
    for v,(title,unit,role) in variables.items():
        z=g[['date',v]].dropna();d=pd.DatetimeIndex(z.date)
        if len(z)>=24:
            X=np.column_stack([np.ones(len(z)),(d.year-2003)+(d.month-1)/12,pd.get_dummies(d.month,drop_first=True,dtype=float)])
            slope=float(np.linalg.lstsq(X,z[v].to_numpy(),rcond=None)[0][1])
        else:slope=np.nan
        stats.append({'region':code,'basin':names[code],'variable':v,'label':title,'units':unit,'role':role,'start':z.date.min(),'end':z.date.max(),'n_months':len(z),'mean':z[v].mean(),'sd':z[v].std(),'month_effect_OLS_slope_per_year':slope})
stats=pd.DataFrame(stats);stats.to_csv(T/'forcing_summary_and_trends.csv',index=False)
for id,vs in [(10,['Native_P','Native_PET','CHIRPS_P','GLEAM_ET']),(11,['MODIS_ET','ESA_CCI_SSM','ESA_CCI_RZSM','MODIS_LST'])]:
    q=stats.pivot(index='region',columns='variable',values='mean').reset_index()[['region',*vs]]
    table(id,'Basin mean forcing and supporting data '+str(id-9),q,['Basin',*[variables[v][0] for v in vs]],list(q.columns),'Available-month means within January 2003–December 2023. Rainfall and ET are mm/month; moisture is m³/m³; temperature is °C. Means are not annual totals. Coverage and sample counts differ between products and are supplied in forcing_summary_and_trends.csv. Actual ET, moisture and temperature are supporting context, not added climate-model predictors.')

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':13,'axes.spines.top':False,'axes.spines.right':False})
figures=[]
def save(fig,id,title,note,height):
    file=f'D{id:02d}_forcing';fig.savefig(F/(file+'.pdf'),bbox_inches='tight');fig.savefig(F/(file+'.png'),bbox_inches='tight',dpi=150)
    plt.close(fig);gc.collect();figures.append({'id':id,'title':title,'file':file+'.png','pdf':file+'.pdf','note':note,'height':height});print('Saved',file,flush=True)
groups=[['Native_P','Native_PET','CHIRPS_P','GLEAM_ET'],['MODIS_ET','ESA_CCI_SSM','ESA_CCI_RZSM','MODIS_LST']]
for idx,vs in enumerate(groups):
    for mode,field in [('mean','mean'),('trend','month_effect_OLS_slope_per_year')]:
        fig,axes=plt.subplots(2,2,figsize=(11,12.5))
        for ax,v in zip(axes.ravel(),vs):
            val=stats[stats.variable==v].set_index('region')[field];g=geo.merge(val.rename('value'),left_on='region',right_index=True,how='left');finite=g.value.dropna()
            if mode=='trend':
                m=max(abs(finite).max(),1e-8);norm=TwoSlopeNorm(vmin=-m,vcenter=0,vmax=m);cmap='RdBu'
            else:norm=Normalize(vmin=finite.min(),vmax=finite.max());cmap='viridis'
            g.plot(column='value',ax=ax,norm=norm,cmap=cmap,edgecolor='#6c7880',linewidth=.4,missing_kwds={'color':'#ddd','hatch':'///'})
            for _,row in g.iterrows():
                p=row.geometry.representative_point();ax.text(p.x,p.y,row.region,ha='center',fontsize=8)
            title,unit,_=variables[v];ax.set_title(textwrap.fill(title+' '+mode,28),fontsize=17);ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
            cb=fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=cmap),ax=ax,fraction=.045,pad=.025);cb.set_label(unit+('/year' if mode=='trend' else ''),fontsize=14)
        fig.tight_layout()
        id=idx*2+(1 if mode=='mean' else 2)
        save(fig,id,('Mean ' if mode=='mean' else 'Trend in ')+'forcing and supporting data '+str(idx+1),('Available-month means' if mode=='mean' else 'OLS slopes with calendar-month effects')+' within 2003–2023; values describe basin averages, not native pixel trends. Native precipitation and PET drive the climate reconstruction; CHIRPS is alternative rainfall. Actual ET, soil moisture and surface temperature provide context. Unequal product coverage is retained; no significance or causal attribution is implied.',6.5)

temporal=[['Native_P'],['Native_PET'],['CHIRPS_P'],['GLEAM_ET','MODIS_ET'],['ESA_CCI_SSM','ESA_CCI_RZSM'],['MODIS_LST']]
for id,vs in enumerate(temporal,5):
    fig,axes=plt.subplots(6,4,figsize=(12,13.3),sharex=True);handles=[]
    for k,code in enumerate(codes):
        ax=axes.ravel()[k];g=data[data.region==code].set_index('date').reindex(pd.date_range('2003-01-01','2023-12-01',freq='MS'))
        for j,v in enumerate(vs):
            h,=ax.plot(g.index,g[v],label=variables[v][0],lw=1.0,color=['#17506a','#bf763a'][j]);
            if k==0:handles.append(h)
        ax.set_title(code,loc='left',fontsize=16,pad=1);ax.tick_params(labelsize=12,labelbottom=True);ax.yaxis.set_major_locator(MaxNLocator(3));ax.xaxis.set_major_locator(mdates.YearLocator(10));ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    for ax in axes.ravel()[22:]:ax.set_visible(False)
    fig.legend(handles=handles,loc='upper center',ncol=len(vs),fontsize=14,frameon=False,bbox_to_anchor=(.5,1.0));fig.supylabel(variables[vs[0]][1],fontsize=16,x=.002);fig.supxlabel('Year · basin codes match Appendix A',y=.003,fontsize=14);fig.tight_layout(rect=(.025,.02,1,.97),h_pad=.6)
    title=' and '.join(variables[v][0] for v in vs)+' for all basins'
    save(fig,id,title,'Monthly basin means during 2003–2023, in the stated physical units. Every basin is shown; unavailable months remain gaps. '+('These are actual meteorological climate-model inputs.' if vs[0].startswith('Native') else 'CHIRPS is used as alternative rainfall in the forcing test.' if vs==['CHIRPS_P'] else 'These datasets provide supporting context; they are not additional predictors in the primary climate reconstruction.'),6.5)

(A/'table_inventory.json').write_text(json.dumps(tables,indent=2,ensure_ascii=False),encoding='utf-8')
(A/'figure_inventory.json').write_text(json.dumps(sorted(figures,key=lambda x:x['id']),indent=2,ensure_ascii=False),encoding='utf-8')
assert len(tables)==11 and len(figures)==10
receipt={'passed':True,'basins':22,'tables':11,'figures':10,'period':'2003–2023','no_refitting':True,'native_forcing_duplicate_targets_equal':True,'monthly_rows':len(data),'sources':['naturalized_attribution_timeseries.csv','multisource_hydroclimate_series.csv','verified basin metrics CSVs'],'tables_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in T.glob('*.csv')}}
(A/'logs/qa.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8');print('Basin tables and forcing atlas complete.')
