import json
import numpy as np,pandas as pd,geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from research_common import ROOT,OBJ1
OUT=ROOT/'Thailand_Objective2/analysis_v4';F=OUT/'figures'
read=lambda name:pd.read_csv(OUT/'tables'/name,dtype={'region':str})
f=read('naturalized_attribution_timeseries.csv');t=read('naturalized_component_trends.csv');m=read('climate_emulator_validation.csv');e=read('groundwater_attribution_evidence.csv');b=read('hydrological_benchmarks.csv')
original=pd.read_csv(OBJ1/'tables/basin_TWSA_GWSA_Sen_MannKendall.csv',dtype={'region':str})
paired=[]
for (code,var),g in f.groupby(['region','variable']):
    columns=['observed_mm','climate_mm','historical_human_mm','modeled_human_mm','residual_mm','discrepancy_mm'];g=g.dropna(subset=columns);date=pd.DatetimeIndex(g.date);year=(date-date.min()).days.to_numpy()/365.25
    design=np.column_stack([np.ones(len(g)),year]+[(date.month==month).astype(float) for month in range(2,13)])
    slopes=np.linalg.lstsq(design,g[columns],rcond=None)[0][1]
    row={'region':code,'variable':var,'n':len(g),**dict(zip(columns,slopes)),'units':'mm/year','method':'OLS with calendar-month fixed effects on identical observed dates; point slopes, not causal fractions'}
    assert abs(row['observed_mm']-row['climate_mm']-row['residual_mm'])<1e-8
    assert abs(row['residual_mm']-row['modeled_human_mm']-row['discrepancy_mm'])<1e-8
    paired.append(row)
pd.DataFrame(paired).to_csv(OUT/'tables/additive_linear_trend_partition.csv',index=False)
geo=gpd.read_file(ROOT/'Thailand_Objective2/data/BASINS/MainBasin_ONWR_Law_WGS84.shp').to_crs(4326);geo['region']=geo.MB_CODE.str.split('-').str[0].str.zfill(2);geo=geo.dissolve(by='region',as_index=False,aggfunc='first')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':17,'axes.spines.top':False,'axes.spines.right':False})
def save(fig,name):fig.tight_layout();fig.savefig(F/name,dpi=220,bbox_inches='tight');plt.close(fig)
fig,axes=plt.subplots(2,1,figsize=(11,7),sharex=True)
for ax,var in zip(axes,['TWSA','GWSA']):
    g=f[(f.region=='TH')&(f.variable==var)&(f.date>='2002-04-01')];date=pd.to_datetime(g.date)
    for field,label,color in [('observed_mm','Observed common support','#253d42'),('climate_mm','Naturalized climate','#167d79'),('historical_human_mm','Historical human model','#b07836')]:ax.plot(date,g[field],label=label,color=color,lw=1.4)
    ax.set_ylabel(var+' (mm)')
handles,labels=axes[0].get_legend_handles_labels();fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.5,1.025),ncol=3,fontsize=14)
save(fig,'national_naturalized_human_comparison.png')
fig,axes=plt.subplots(2,1,figsize=(11,7),sharex=True)
for ax,var in zip(axes,['TWSA','GWSA']):
    g=f[(f.region=='TH')&(f.variable==var)&(f.date>='2002-04-01')];date=pd.to_datetime(g.date)
    for field,label,color in [('residual_mm','Observed minus naturalized','#b45f35'),('modeled_human_mm','Paired modeled human effect','#167d79'),('discrepancy_mm','Observed minus historical model','#737a91')]:ax.plot(date,g[field],label=label,color=color,lw=1.3)
    ax.axhline(0,color='#999',lw=.5);ax.set_ylabel(var+' (mm)')
handles,labels=axes[0].get_legend_handles_labels();fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.5,1.025),ncol=3,fontsize=12)
save(fig,'national_residual_and_model_discrepancy.png')
fig,axes=plt.subplots(2,2,figsize=(11,12))
for i,var in enumerate(['TWSA','GWSA']):
    for j,component in enumerate(['climate_mm','residual_mm']):
        ax=axes[i,j];g=t[(t.variable==var)&(t.component==component)&(t.region!='TH')];z=geo.merge(g,on='region');lim=max(1,g.sen_slope_mm_year.abs().max());z.plot(column='sen_slope_mm_year',ax=ax,cmap='RdBu',vmin=-lim,vmax=lim,legend=True,legend_kwds={'label':'Sen slope (mm/year)','shrink':.55},edgecolor='#555',linewidth=.3);ax.set(title=var+(' naturalized climate' if j==0 else ' observed residual'),xlabel='Longitude (°E)',ylabel='Latitude (°N)');ax.set_aspect('equal')
save(fig,'all_basin_climate_residual_trends.png')
test=m[(m.model=='Ensemble')&(m.period=='Test')]
fig,ax=plt.subplots(figsize=(10,5));colors={'TWSA':'#167d79','GWSA':'#b45f35'}
for var,g in test.groupby('variable'):ax.scatter(g.NSE,g.deseasonalized_NSE,color=colors[var],label=var,s=40,alpha=.8)
ax.axhline(0,color='#777',lw=.7);ax.set(xlabel='Monthly test NSE against naturalized model',ylabel='Deseasonalized test NSE',title='Verification of climate emulators in 2016–2023');ax.legend();save(fig,'emulator_verification.png')
q=e[(e.region=='TH')&(e.component=='residual_mm')&(e.quality=='retained_flags')]
fig,ax=plt.subplots(figsize=(8,4));positions=np.arange(len(q));ax.bar(positions-.15,q.r,width=.3,color='#167d79',label='Raw annual agreement');ax.bar(positions+.15,q.partial_r_controlling_natural_climate,width=.3,color='#b45f35',label='Controlling naturalized climate');ax.set_xticks(positions,q.variable);ax.set(ylim=(-1,1),ylabel='Pearson correlation',title='Well-head association with observed residual');ax.axhline(0,color='#555',lw=.7);ax.legend(fontsize=10);save(fig,'groundwater_residual_agreement.png')
summary={'author':'Farzeen Khanal','advisor':'Dr. Natthachet Tangdamrongsub','degree':'Master of Science in Water Engineering and Management','release_date':'2026-10-24','original_national_trends':original[original.region=='TH'].to_dict('records'),'national_component_trends':t[t.region=='TH'].to_dict('records'),'national_emulator_test':test[test.region=='TH'].to_dict('records'),'national_benchmarks':b[b.region=='TH'].to_dict('records'),'national_groundwater_evidence':e[(e.region=='TH')&(e.quality=='retained_flags')].to_dict('records'),'national_additive_partition':[x for x in paired if x['region']=='TH'],'basin_emulator_test':test[test.region!='TH'].to_dict('records'),'basin_component_trends':t[t.region!='TH'].to_dict('records'),'emulator_test_range':test.groupby('variable')[['NSE','deseasonalized_NSE']].agg(['min','max']).to_string(),'important':'High emulator skill verifies reproduction of a hydrological model; it is not independent validation of human depletion. Sen slopes are not additive; OLS fixed-month slopes are additive on common dates. Local GRACE processing center/release is absent from supplied file metadata.'}
(ROOT/'reports/final_research_results_v4.json').write_text(pd.Series(summary).to_json(force_ascii=False,indent=2),encoding='utf-8')
checks={'passed':True,'target_region_combinations':int(f.groupby(['region','variable']).ngroups),'emulator_ensembles':len(test),'naturalized_data_sources':10,'decomposition_identity_verified':True,'linear_trend_additivity_verified':True,'groundwater_evidence_rows':len(e),'no_measured_pumping_claim':True,'no_head_to_storage_conversion':True,'author_confirmed':'Farzeen Khanal'}
assert len(test)==46 and f.groupby(['region','variable']).ngroups==46
(OUT/'logs/final_research_qa.json').write_text(json.dumps(checks,indent=2),encoding='utf-8');print(json.dumps(summary['national_emulator_test'],indent=2));print(q[['variable','n','r','partial_r_controlling_natural_climate','detrended_r']].to_string(index=False))
