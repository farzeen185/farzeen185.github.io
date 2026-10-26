"""Publication vector figures for the direct-method robustness extension."""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
from pathlib import Path
import numpy as np,pandas as pd,geopandas as gpd,json,gc
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import TwoSlopeNorm,Normalize,ListedColormap
from matplotlib.backends.backend_pdf import PdfPages
R=Path(os.environ.get('TWSA_RESEARCH_ROOT',Path(__file__).resolve().parents[1]));O=R/'Thailand_Direct_WaterGAP_Analysis/robustness_extension';T=O/'tables';F=O/'figures';F.mkdir(exist_ok=True)
read=lambda n:pd.read_csv(T/n,dtype={'region':str})
p=read('factorial_product_component_support_trends.csv');m=read('alternative_baseline_trends.csv');w=read('fixed_network_comparison.csv');rv=read('reservoir_cluster_and_influence.csv');rain=read('rainfall_concentration_mechanism.csv');ann=read('rainfall_concentration_annual_indices.csv');evidence=read('basin_evidence_matrix.csv')
geo=gpd.read_file(R/'Thailand_Direct_WaterGAP_Analysis/inputs/basins.geojson');names=dict(zip(p.region,p.basin));codes=sorted(c for c in names if len(c)==2 and c!='TH')
plt.rcParams.update({'font.family':'DejaVu Serif','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
catalog=[];atlas=PdfPages(O/'Robustness_and_Process_Figures.pdf')
def save(fig,stem,title,note):
 fig.suptitle(title,fontweight='bold',fontsize=15,y=.985);fig.text(.035,.015,note,fontsize=9,color='#485760',va='bottom');fig.tight_layout(rect=[.015,.095,.99,.94])
 for ext in ['png','pdf']:fig.savefig(F/(stem+'.'+ext),dpi=200,bbox_inches='tight')
 atlas.savefig(fig,bbox_inches='tight');catalog.append({'file':stem,'title':title,'note':note});plt.close(fig);gc.collect();print(stem,flush=True)
def mapping(ax,vals,title,unit,limit=None,positive=False,hatch=None):
 q=geo.merge(vals.rename('value'),left_on='region',right_index=True,how='left');lim=limit or max(abs(q.value).max(),.0001);norm=Normalize(0,lim) if positive else TwoSlopeNorm(vmin=-lim,vcenter=0,vmax=lim);cm='viridis' if positive else 'RdBu'
 q.plot(column='value',ax=ax,cmap=cm,norm=norm,edgecolor='#71818a',linewidth=.45,missing_kwds={'color':'#ddd','hatch':'///'})
 if hatch is not None:
  q[q.region.isin(hatch)].plot(ax=ax,facecolor='none',edgecolor='#66747b',hatch='///',linewidth=.3)
 ax.set_title(title,fontsize=11);ax.set_xlabel('Longitude');ax.set_ylabel('Latitude');plt.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=cm),ax=ax,fraction=.037,pad=.02,label=unit)
fig,ax=plt.subplots(figsize=(12,5));ax.axis('off')
boxes=[(.02,.58,.22,.25,'Observed storage\nGRACE TWSA / derived GWSA'),(.38,.58,.24,.25,'Climate reference\nNaturalized WaterGAP'),(.76,.58,.22,.25,'Residual\nObservation − reference'),(.02,.12,.27,.23,'Processing/support tests\nGravity × soil × coast × scale'),(.36,.12,.28,.23,'Baseline/process tests\nAlternative no-water-management runs\nRainfall concentration and dry spells'),(.71,.12,.27,.23,'Independent evidence\nFixed groundwater well panels\nReservoir scene-supported storage')]
for x,y,b,h,s in boxes:ax.add_patch(plt.Rectangle((x,y),b,h,facecolor='#eef4f3',edgecolor='#407b7c',lw=1.3));ax.text(x+b/2,y+h/2,s,ha='center',va='center',fontsize=11)
for start,end in [((.24,.705),(.38,.705)),((.62,.705),(.76,.705)),((.87,.58),(.85,.35)),((.5,.58),(.5,.35)),((.13,.58),(.15,.35))]:ax.annotate('',xy=end,xytext=start,arrowprops={'arrowstyle':'->','color':'#526d77','lw':1.5})
save(fig,'01_framework','A direct-model framework for testing attribution limits','The analysis tests robustness and physical consistency; it does not identify all residual storage as human-caused.\nClimate reconstruction and residence-time fitting are excluded from this design.')
groups=['TH','M_CP','M_MK','M_S','M_W','M_E'];chains=['CSR_Noah','CSR_G3Psoil','COSTG_Noah','COSTG_G3Psoil'];colors=['#234c66','#4d97a4','#c17d36','#b65077']
fig,axes=plt.subplots(1,2,figsize=(12,7),sharey=True)
for ax,var in zip(axes,['TWSA','GWSA']):
 q=p[(p.variable==var)&(p.component=='residual_mm')&(p.support=='provider_land')];use=chains[::2] if var=='TWSA' else chains
 for j,chain in enumerate(use):
  z=q[q.chain==chain].set_index('region').reindex(groups);yy=np.arange(len(groups))+(j-(len(use)-1)/2)*.15
  ax.errorbar(z.OLS_mm_year,yy,xerr=[z.OLS_mm_year-z.OLS_lo95,z.OLS_hi95-z.OLS_mm_year],fmt='o',ms=4,capsize=2,color=colors[chains.index(chain)],label=chain)
 ax.set_title(var+' residual trends');ax.set_yticks(range(len(groups)),[names[c] for c in groups]);ax.axvline(0,color='#888',lw=.8);ax.set_xlabel('Month-adjusted OLS slope (mm/year)');ax.grid(axis='x',alpha=.15);ax.legend(fontsize=8)
axes[0].invert_yaxis();save(fig,'02_regional_factorial_trends','Do declines survive gravity and soil-component choices?','Intervals: conditional two-year calendar-block wild regression; they do not include all satellite/model uncertainty.\nRegional groups aggregate reporting basins, not new independent GRACE measurements; TWSA does not depend on soil choice.')
fig,axes=plt.subplots(2,2,figsize=(11,10))
for row,var in enumerate(['TWSA','GWSA']):
 q=p[(p.variable==var)&(p.component=='residual_mm')&(p.support=='provider_land')&(p.region.isin(codes))];g=q.groupby('region').seasonal_sen_mm_year
 mapping(axes[row,0],g.median(),var+': median across tested chains','mm/year');mapping(axes[row,1],g.max()-g.min(),var+': tested-chain slope range','mm/year',positive=True)
save(fig,'03_spatial_processing_sensitivity','Residual trend magnitude and its processing sensitivity','Median/range across two gravity products and, for GWSA, two soil estimates. Other subtraction terms are held fixed.\nA narrow range within this tested set is not proof of small total uncertainty; basin-scale GRACE support remains coarse.')
bs=read('alternative_baseline_monthly.csv');bs.date=pd.to_datetime(bs.date);labels={'WaterGAP_GSWP3_ERA5':'WaterGAP / GSWP3–ERA5','watergap2-2e_20CRV3_ERA5':'WaterGAP / 20CRV3–ERA5','lpjml5-7-10-fire_20CRV3_ERA5':'LPJmL / 20CRV3–ERA5','miroc-integ-land_20CRV3_ERA5':'MIROC-INTEG-LAND / 20CRV3–ERA5'}
models=list(labels);fig,axes=plt.subplots(2,1,figsize=(12,8),sharex=True)
for j,model in enumerate(models):
 q=bs[(bs.region=='TH')&(bs.baseline==model)].set_index('date');q=q.reindex(pd.date_range(q.index.min(),q.index.max(),freq='MS'))
 for ax,col in zip(axes,['climate_mm','residual_mm']):ax.plot(q.index,q[col],color=colors[j],lw=1.1,label=labels[model]);ax.axhline(0,color='#999',lw=.5);ax.set_ylabel('Anomaly (mm)')
axes[0].set_title('a. No-water-management baseline sensitivity',loc='left');axes[1].set_title('b. GRACE minus each baseline',loc='left');axes[0].legend(fontsize=8,ncol=2)
save(fig,'04_alternative_baseline_histories','How strongly does the storage difference depend on the reference?','Exact common 2002–2021 support and 2004–2009 reference. LPJmL/MIROC are structural diagnostics, excluded from full-TWS evidence flags.\nTheir groundwater accounting is not verified as equivalent to WaterGAP; nowatermgt can retain other historical human forcings.')
fig,ax=plt.subplots(figsize=(11,9));q=m[(m.component=='residual_mm')&m.region.isin(codes)].pivot(index='region',columns='baseline',values='seasonal_sen_mm_year').reindex(index=codes,columns=models);lim=abs(q).max().max();im=ax.imshow(q,cmap='RdBu',vmin=-lim,vmax=lim,aspect='auto');ax.set_yticks(range(22),[c+' '+names[c] for c in codes]);ax.set_xticks(range(4),['WaterGAP\nGSWP3–ERA5','WaterGAP\n20CRV3–ERA5','LPJmL\n20CRV3–ERA5','MIROC\n20CRV3–ERA5']);plt.colorbar(im,ax=ax,label='Residual seasonal Sen slope (mm/year)')
for i in range(22):
 for j in range(4):ax.text(j,i,f'{q.iloc[i,j]:.1f}',ha='center',va='center',fontsize=8,color='white' if abs(q.iloc[i,j])>lim*.6 else '#253940')
save(fig,'05_baseline_basin_heatmap','Basin storage differences across four reference simulations','TWSA differences, common 2002–2021 support. LPJmL/MIROC are structural diagnostics, not verified equivalent full-TWS baselines.\nOnly the two WaterGAP variants enter baseline-robustness flags. Differences combine forcing, model structure and experiment definitions.')
fig,axes=plt.subplots(1,2,figsize=(12,8))
q=w[(w.variable=='GWSA')&(w.component=='residual_mm')&(w.n_years>=8)&w.region.isin(['TH']+codes)];eligible=sorted(q.region.unique(),key=lambda x:(x!='TH',x))
for j,panel in enumerate(['changing_network','strict_balanced']):
 z=q[q.panel==panel].set_index('region').reindex(eligible);yy=np.arange(len(eligible))+(j-.5)*.18
 axes[0].errorbar(z.r,yy,xerr=[z.r-z.station_boot_lo95,z.station_boot_hi95-z.r],fmt='o',ms=4,capsize=2,label=panel,color=colors[j])
axes[0].set_yticks(range(len(eligible)),[names[c] for c in eligible],fontsize=9);axes[0].axvline(0,color='#999',lw=.7);axes[0].set(xlabel='GWSA residual–head correlation',title='a. Fixed-period well-network sensitivity');axes[0].legend(fontsize=8);axes[0].invert_yaxis()
z=rv.sort_values('r_season_trend_removed');axes[1].errorbar(z.r_season_trend_removed,range(len(z)),xerr=[z.r_season_trend_removed-z.year_cluster_lo95,z.year_cluster_hi95-z.r_season_trend_removed],fmt='o',ms=4,capsize=2,color='#399b8c');axes[1].set_yticks(range(len(z)),[names[c] for c in z.region],fontsize=9);axes[1].axvline(0,color='#999',lw=.7);axes[1].set(xlabel='Season/trend-adjusted correlation',title='b. Reservoir storage versus TWSA residual')
save(fig,'06_independent_evidence_intervals','What do independent observations support?','Wells: 2013–2022, ≥8 paired years; station-bootstrap intervals conditional on observed years (changing/strict panels).\nReservoirs: ≥24 scene-supported months; year-cluster intervals. Correlations are not causal attribution or storage-volume validation.')
fig,axes=plt.subplots(1,3,figsize=(13,6))
from scipy.stats import theilslopes
for ax,col,title,unit in zip(axes,['P_annual_mm','area_mean_local_daily_Gini','area_mean_local_CDD_days'],['Mean annual rainfall','Mean local daily rainfall Gini','Mean local longest dry spell'],['mm/year','Gini','days']):mapping(ax,ann.groupby('region')[col].mean(),title,unit,positive=True)
save(fig,'07_rainfall_concentration_maps','Rainfall amount, concentration and dry spells: 2003–2023','CHIRPS v2 daily at native 0.05° pixel centres, cosine-latitude area weights. Higher Gini means more concentrated daily rainfall.\nLocal indices are calculated per grid cell before basin averaging; dry days have rainfall <1 mm. Daily CHIRPS is a derived rainfall product.')
pa=read('rainfall_storage_annual_paired.csv');g=pa[(pa.region=='TH')&(pa.variable=='TWSA')];fig,axes=plt.subplots(3,1,figsize=(12,8),sharex=True)
axes[0].bar(g.year,g.P_annual_mm,color='#3e7295');axes[0].set_ylabel('Rainfall (mm/year)');axes[1].plot(g.year,g.area_mean_local_daily_Gini,'o-',color='#b77c36');axes[1].set_ylabel('Local daily Gini')
for c,label,color in [('observed_mm','GRACE','#294653'),('climate_mm','Naturalized WaterGAP','#b77c36'),('residual_mm','Residual','#399b8c')]:
 q=g.set_index('year')[c].reindex(range(2003,2024));axes[2].plot(q.index,q,'o-',label=label,color=color,lw=1.2,ms=3)
axes[2].set_ylabel('Annual storage (mm)');axes[2].legend(fontsize=9,ncol=3);axes[-1].set_xlabel('Year')
save(fig,'08_national_rainfall_storage','National rainfall concentration and storage variability','Storage: mean deseasonalized anomaly on common dates, ≥8 observed months per year; no mission-gap filling.\nRainfall and Gini use full calendar years. This display is descriptive; the controlled analysis also includes annual PET and time.')
fig,axes=plt.subplots(1,2,figsize=(12,5.8),sharey=True);q=rain[(rain.region=='TH')&rain.primary_metric].copy();q['label']=q.variable+' '+q.component.str.replace('_mm','');q=q.sort_values(['variable','component']);yy=np.arange(len(q))
axes[0].errorbar(q.coefficient_mm_per_metric_SD,yy,xerr=[q.coefficient_mm_per_metric_SD-q.wild_lo95,q.wild_hi95-q.coefficient_mm_per_metric_SD],fmt='o',color='#399b8c',capsize=3);axes[0].set_yticks(yy,q.label);axes[0].axvline(0,color='#999',lw=.8);axes[0].set_xlabel('Storage response per 1 SD rainfall Gini (mm)');axes[0].set_title('a. Controlled association and wild intervals')
axes[1].barh(yy,q.LOYO_RMSE_gain_mm,color=['#399b8c' if v>0 else '#bf7184' for v in q.LOYO_RMSE_gain_mm]);axes[1].axvline(0,color='#999',lw=.8);axes[1].set_xlabel('RMSE improvement after adding Gini (mm)');axes[1].set_title('b. Leave-one-year-out explanatory comparison')
save(fig,'09_national_process_test','Does rainfall concentration add information beyond rainfall totals?','Controls: annual precipitation, annual potential ET and linear time; main predictor: area-mean local daily Gini.\nTwo-year wild intervals; small annual samples. Positive RMSE gain means improvement. These are exploratory associations, not causal effects.')
fig,axes=plt.subplots(1,2,figsize=(11,6));q=rain[(rain.variable=='TWSA')&(rain.component=='residual_mm')&rain.primary_metric].set_index('region');mapping(axes[0],q.coefficient_mm_per_metric_SD,'TWSA residual: rainfall Gini coefficient','mm per SD',hatch=q[q.FDR_q>=.05].index);mapping(axes[1],q.LOYO_RMSE_gain_mm,'Leave-one-year-out RMSE gain','mm')
save(fig,'10_basin_process_diagnostics','Spatial evidence for rainfall concentration in the residual','Hatching: q ≥ 0.05 after adjustment across all fixed basin tests (both storage variables, three responses, three rain metrics).\nBasins share GRACE/climate signals. Improved explanatory fit alone does not establish a mechanism or anthropogenic influence.')
fig,ax=plt.subplots(figsize=(13,9));q=evidence[(evidence.variable=='TWSA')&evidence.region.isin(codes)].set_index('region').reindex(codes);mat=np.column_stack([q.product_component_negative/q.product_component_variants,q.interior_negative/q.interior_variants.replace(0,np.nan),q.alternative_TWS_baselines_negative/q.alternative_TWS_baselines,q.fixed_well_r,q.reservoir_adjusted_r]);im=ax.imshow(mat,aspect='auto',cmap='RdBu',vmin=-1,vmax=1);ax.set_yticks(range(22),[c+' '+names[c] for c in codes],fontsize=9);ax.set_xticks(range(5),['Processing\nnegative fraction','Interior\nnegative fraction','WaterGAP variants\nnegative fraction','Fixed wells\ncorrelation','Reservoirs\ncorrelation']);ax.tick_params(axis='x',labelsize=9);plt.colorbar(im,ax=ax,label='Fraction of tested variants (first 3 columns) / correlation (last 2)')
for i in range(22):
 for j in range(5):
  v=mat[i,j];ax.text(j,i,'—' if not np.isfinite(v) else f'{v:.2f}',ha='center',va='center',fontsize=8,color='white' if np.isfinite(v) and abs(v)>.65 else '#253940')
save(fig,'11_basin_evidence_matrix','Basin evidence: robust declines, sparse support and disagreement','Fractions describe tested variants, not probabilities; baseline flags use only two WaterGAP variants, not the structural diagnostics.\nCorrelations describe consistency, not causality. Missing evidence remains blank; no overall confidence score is assigned.')
shared=pd.read_csv(R/'Thailand_Publication_v6/tables/basin_shared_support.csv',dtype={'region_a':str,'region_b':str});ss=shared.pivot(index='region_a',columns='region_b',values='shared_native_weight').reindex(index=codes,columns=codes);fig,axes=plt.subplots(1,2,figsize=(12,6));im=axes[0].imshow(ss,vmin=0,vmax=1,cmap='viridis');axes[0].set_xticks(range(22),codes,rotation=90,fontsize=8);axes[0].set_yticks(range(22),codes,fontsize=8);axes[0].set_title('a. Shared CSR native-mascon weight');plt.colorbar(im,ax=axes[0],fraction=.04,pad=.02)
co=read('coastal_support_retention.csv');mapping(axes[1],co[co.support!='provider_land'].drop_duplicates('region').set_index('region').retained_land_fraction,'b. Retained area after interior-mask sensitivity','Fraction',limit=1,positive=True)
save(fig,'12_spatial_support_limits','Why 22 reporting basins are not 22 independent satellite regions','Shared native weights describe overlapping sampling, not a full GRACE error covariance or independent effective sample size.\nInterior sensitivity removes a 0.25° grid-cell border next to provider ocean masks; it is a stress test, not a validated coastal correction.')
atlas.close();assert len(catalog)==12;(O/'figure_catalog.json').write_text(json.dumps(catalog,indent=2),encoding='utf-8')
