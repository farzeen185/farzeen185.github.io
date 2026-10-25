"""Research seminar deck with projection-sized figures and Metropolis Beamer.

This is an editorial/figure redesign, not a new scientific fit.
"""
from pathlib import Path
import os,json,shutil,textwrap,gc
import numpy as np,pandas as pd,geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import Normalize,TwoSlopeNorm
R=Path(os.environ.get('TWSA_RESEARCH_ROOT',Path(__file__).resolve().parents[1])).resolve();O=R/'Thailand_Research_v5'
P=O/'presentation/academic_metropolis';F=P/'figures';F.mkdir(parents=True,exist_ok=True)
read=lambda n:pd.read_csv(O/'tables'/n,dtype={'region':str})
obs=read('CSR_basin_storage_timeseries.csv');at=read('CSR_naturalized_attribution.csv');tr=read('CSR_basin_trends.csv');ci=read('attribution_wild_block_intervals.csv')
for d in [obs,at]:d['date']=pd.to_datetime(d.date)
ev=pd.read_csv(R/'Thailand_Objective2/analysis_v4/tables/climate_emulator_validation.csv',dtype={'region':str});ev=ev[(ev.model=='Ensemble')&(ev.period=='Test')]
pred=pd.read_csv(R/'Thailand_Objective2/analysis_v4/tables/climate_emulator_timeseries.csv',dtype={'region':str},parse_dates=['date'])
aux=pd.read_csv(O/'basin_forcing_appendix/tables/forcing_monthly_series_2003_2023.csv',dtype={'region':str},parse_dates=['date'])
fs=pd.read_csv(O/'basin_forcing_appendix/tables/forcing_summary_and_trends.csv',dtype={'region':str})
land=pd.read_csv(O/'figure_revision/tables/GLDAS_matched_land_timeseries.csv',dtype={'region':str},parse_dates=['date'])
lm=pd.read_csv(O/'figure_revision/tables/GLDAS_matched_land_metrics.csv',dtype={'region':str})
well=read('CSR_groundwater_network_evidence.csv');well=well[(well.quality=='retained_flags')&(well.component=='residual_mm')]
res=read('independent_reservoir_evidence.csv');res=res[(res.variable=='TWSA')&(res.component=='residual_mm')&(res.level==1)]
geo=gpd.read_file(R/'Thailand_Objective2/data/BASINS/MainBasin_ONWR_Law_WGS84.shp').to_crs(4326);geo['region']=geo.MB_CODE.astype(str).str.split('-').str[0].str.zfill(2);geo=geo.dissolve(by='region',as_index=False,aggfunc='first');geo.geometry=geo.geometry.simplify(.006,preserve_topology=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':17,'axes.spines.top':False,'axes.spines.right':False,'axes.labelsize':17,'axes.titlesize':19,'xtick.labelsize':14,'ytick.labelsize':14})
def save(fig,name):
    fig.tight_layout()
    for ext in ['pdf','png']:fig.savefig(F/(name+'.'+ext),bbox_inches='tight',dpi=180)
    plt.close(fig);gc.collect();print('Figure',name,flush=True);return name
def copyfig(name,folder=None):
    folder=folder or O/'presentation/figures'
    for ext in ['png','pdf']:shutil.copy2(folder/(name+'.'+ext),F/(name+'.'+ext))
    return name
def maps(name,vals,titles,units,ranges=None,cmaps=None):
    fig,axes=plt.subplots(1,len(vals),figsize=(4.5*len(vals),5.4),squeeze=False)
    for i,(ax,val,title,unit) in enumerate(zip(axes.ravel(),vals,titles,units)):
        g=geo.merge(val.rename('value'),left_on='region',right_index=True,how='left')
        if ranges:lo,hi=ranges[i]
        else:m=max(g.value.abs().max(),.001);lo,hi=-m,m
        norm=TwoSlopeNorm(vmin=lo,vcenter=0,vmax=hi) if lo<0<hi else Normalize(lo,hi)
        cmap=cmaps[i] if cmaps else 'RdBu'
        g.plot(column='value',ax=ax,norm=norm,cmap=cmap,edgecolor='#737d85',linewidth=.4,missing_kwds={'color':'#ddd','hatch':'///'})
        ax.set_title(textwrap.fill(title,25));ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
        cb=fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=cmap),ax=ax,fraction=.045,pad=.025);cb.set_label(unit,fontsize=16)
    return save(fig,name)
def lines(name,frame,variables,series,ylabel='mm water equivalent'):
    fig,axes=plt.subplots(len(variables),1,figsize=(12,3.0*len(variables)),sharex=True,squeeze=False)
    for ax,var in zip(axes.ravel(),variables):
        g=frame[(frame.region=='TH')&(frame.variable==var)].set_index('date').sort_index()
        g=g.reindex(pd.date_range(g.index.min(),g.index.max(),freq='MS'))
        for col,label,color in series:ax.plot(g.index,g[col],label=label,color=color,lw=1.6)
        if name=='climate_national':ax.axvspan(pd.Timestamp('2016-01-01'),pd.Timestamp('2023-12-31'),color='#368c83',alpha=.12,zorder=-5)
        ax.set_ylabel(var+' (mm)');ax.axhline(0,color='#aaa',lw=.6);ax.grid(axis='y',alpha=.16)
    handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='upper center',ncol=len(series),fontsize=16,frameon=False,bbox_to_anchor=(.5,1.04));axes[-1,0].set_xlabel('Year')
    return save(fig,name)
copyfig('01_study_basins');copyfig('05_product_ranking_scatter');copyfig('13_climate_memory_ablation')
lines('storage_national',obs.assign(variable='TWSA',value=obs.TWSA).pipe(lambda x:pd.concat([x,obs.assign(variable='GWSA',value=obs.GWSA)])),['TWSA','GWSA'],[('value','Observed / derived storage','#203a49')])
maps('storage_slopes',[tr[tr.variable==v].set_index('region').sen_slope_mm_year for v in ['TWSA','GWSA']],['Total storage trend','Groundwater storage trend'],['mm/year']*2)
maps('trend_evidence',[tr[tr.variable==v].set_index('region').mk_seasonal_q_FDR for v in ['TWSA','GWSA']],['TWSA seasonal MK','GWSA seasonal MK'],['FDR q']*2,[(0,.1)]*2,['YlOrRd_r']*2)
g=aux[aux.region=='TH'];fig,ax=plt.subplots(2,1,figsize=(12,5.7),sharex=True)
ax[0].plot(g.date,g.Native_P,label='Native precipitation',color='#203a49',lw=1.4);ax[0].plot(g.date,g.CHIRPS_P,label='CHIRPS precipitation',color='#bc6b3d',lw=1.2,alpha=.8);ax[0].set_ylabel('P (mm/month)');ax[0].legend(frameon=False,ncol=2,fontsize=15)
ax[1].plot(g.date,g.Native_PET,color='#368c83',lw=1.5);ax[1].set_ylabel('PET (mm/month)');ax[1].set_xlabel('Year');save(fig,'forcing_national')
maps('forcing_spatial',[fs[fs.variable==v].set_index('region')['mean'] for v in ['Native_P','Native_PET','CHIRPS_P']],['Native precipitation','Native potential ET','CHIRPS precipitation'],['mm/month']*3,[(0,300),(0,180),(0,300)],['viridis']*3)
maps('climate_scores',[ev[ev.variable==v].set_index('region').deseasonalized_NSE for v in ['TWSA','GWSA']],['TWSA anomaly skill','GWSA anomaly skill'],['Test anomaly NSE']*2,[(0,1)]*2,['viridis']*2)
lines('climate_national',pred,['TWSA','GWSA'],[('naturalized_target_mm','Naturalized target','#203a49'),('emulator_mm','Weather reconstruction','#bc6b3d')])
annual=pd.read_csv(O/'figure_revision/tables/climate_evaluation_by_test_year.csv',dtype={'region':str})
fig,ax=plt.subplots(figsize=(12,4.9))
for var,c in [('TWSA','#203a49'),('GWSA','#bc6b3d')]:
    q=annual[(annual.region=='TH')&(annual.variable==var)];ax.plot(q.year,q.anomaly_NSE,'o-',label=var,color=c,lw=2,ms=6)
ax.axhline(0,color='#999',ls='--');ax.set(xlabel='Held-out test year',ylabel='Annual anomaly NSE');ax.legend(frameon=False,ncol=2);save(fig,'annual_skill')
lines('residual_national',at,['TWSA','GWSA'],[('residual_mm','Residual R','#bc6b3d'),('modeled_human_mm','Modeled human H','#368c83'),('discrepancy_mm','Discrepancy E','#81769b')])
q=ci[ci.block_years==2]
maps('residual_spatial',[q[(q.variable==v)&(q.component=='residual_mm')].set_index('region').ols_slope_mm_year for v in ['TWSA','GWSA']],['TWSA residual trend','GWSA residual trend'],['OLS mm/year']*2)
g=land[land.region=='TH'];fig,ax=plt.subplots(figsize=(12,4.8));ax.plot(g.date,g.GLDAS_land_mm,label='GLDAS Noah',color='#203a49',lw=1.5);ax.plot(g.date,g.naturalized_land_mm,label='Naturalized WaterGAP',color='#bc6b3d',lw=1.4);ax.set(xlabel='Year',ylabel='Land storage anomaly (mm)');ax.legend(frameon=False,ncol=2);save(fig,'gldas_national')
maps('gldas_scores',[lm.set_index('region').NSE,lm.set_index('region').RMSE_mm],['Matched land-storage skill','Matched land-storage error'],['NSE','RMSE (mm)'],[(-1,1),(0,100)],['RdBu','YlOrRd'])
maps('head_spatial',[well[well.variable==v].set_index('region').r for v in ['TWSA','GWSA']],['TWS residual / head','GWS residual / head'],['Annual Pearson r']*2,[(-1,1)]*2)
rst=read('independent_reservoir_timeseries.csv');rst['date']=pd.to_datetime(rst.date)
g=at[(at.region=='TH')&(at.variable=='TWSA')].merge(rst[(rst.region=='TH')&(rst.level==1)][['date','SWSA_reservoir_mm']],on='date').dropna(subset=['residual_mm','SWSA_reservoir_mm'])
d=pd.DatetimeIndex(g.date);X=np.column_stack([np.ones(len(g)),(d.year-d.year.min())+(d.month-1)/12,pd.get_dummies(d.month,drop_first=True,dtype=float)])
values=[]
for col in ['residual_mm','SWSA_reservoir_mm']:
    y=g[col].to_numpy();z=y-X@np.linalg.lstsq(X,y,rcond=None)[0];values.append(z/z.std())
assert np.isclose(np.corrcoef(values)[0,1],res[res.region=='TH'].r_month_trend_removed.iloc[0],atol=1e-6)
fig,ax=plt.subplots(figsize=(12,4.8))
for y,label,color in zip(values,['TWS residual','Reservoir storage'],['#203a49','#bc6b3d']):ax.plot(g.date,y,'o',ms=4,label=label,color=color,alpha=.85)
ax.set(xlabel='Scene-supported observation date',ylabel='Adjusted standardized anomaly');ax.legend(frameon=False,ncol=2);save(fig,'reservoir_national')
maps('reservoir_spatial',[res.set_index('region').r_month_trend_removed,res.set_index('region').n_months],['TWS residual / reservoir','Matched scene months'],['Adjusted Pearson r','Months'],[(-1,1),(0,260)],['RdBu','YlGnBu'])
g=aux[aux.region=='TH'];fig,axes=plt.subplots(2,2,figsize=(12,6.1),sharex=True)
for ax,cols,title,unit in zip(axes.ravel(),[['GLEAM_ET','MODIS_ET'],['ESA_CCI_SSM'],['ESA_CCI_RZSM'],['MODIS_LST']],['Actual evapotranspiration','Surface soil moisture','Root-zone moisture','Land surface temperature'],['mm/month','m³/m³','m³/m³','°C']):
    for col,c in zip(cols,['#203a49','#bc6b3d']):ax.plot(g.date,g[col],label=col.replace('_',' '),lw=1.2,color=c)
    ax.set_title(title,fontsize=16);ax.set_ylabel(unit,fontsize=15)
    if len(cols)>1:ax.legend(frameon=False,fontsize=12)
save(fig,'supporting_temporal')
maps('supporting_spatial',[fs[fs.variable==v].set_index('region')['mean'] for v in ['GLEAM_ET','ESA_CCI_SSM','ESA_CCI_RZSM','MODIS_LST']],['GLEAM actual ET','Surface moisture','Root-zone moisture','Surface temperature'],['mm/month','m³/m³','m³/m³','°C'],[(0,160),(0,.4),(0,.4),(20,32)],['viridis']*4)

slides=[]
def add(title,section,lines=None,figure=None,table=None,note='',equation=None,layout=None,backup=False):
    slides.append(dict(title=title,section=section,lines=lines or [],figure=figure,table=table,note=note,equation=equation,layout=layout,backup=backup))
add('Water storage change across Thailand','',lines=['Climate reconstruction and the limits of human attribution','Farzeen Khan','MS in Water Engineering and Management','Asian Institute of Technology','Advisor: Dr. Natthachet Tangdamrongsub'],layout='title')
add('Research focus','Introduction',lines=['How are total and groundwater storage changing across Thailand’s 22 principal basins?','How much of the observed change can the climate baseline explain?','How strongly do independent observations support the remaining residual?'])
add('Research objectives','Introduction',table=[['Objective','Output'],['1  Storage change','Monthly TWSA/GWSA, Sen slopes and Mann–Kendall tests'],['2  Climate and residual','Climate reconstruction, GLDAS benchmark and observation checks'],['3  Decision support','Interactive basin app, input data and reproducible code']])
add('Thailand’s 22 principal basins','Study design',figure='01_study_basins',lines=['Official ONWR reporting framework','GRACE information extends across basin boundaries','All basin tables retain coverage and uncertainty'],layout='split',note='ONWR principal-basin geometry. Reporting units do not imply independent GRACE observations.')
add('Data and scientific roles','Study design',table=[['Record','Role'],['CSR RL06.3 GRACE/GRACE-FO','Observed total storage'],['GLDAS Noah and G3P','Non-groundwater storage compartments'],['Paired WaterGAP simulations','Naturalized and historical-human baselines'],['Native P/PET and CHIRPS','Weather reconstruction and rainfall sensitivity'],['Thai wells and MSEA-Res','Groundwater and reservoir consistency evidence']],note='Primary TWSA: April 2002–September 2024. Derived GWSA: April 2002–September 2023.')
add('Analysis workflow','Methodology',lines=['Harmonize monthly units, dates, area weights and the 2004–2009 reference','Calculate GWSA and estimate storage trends','Reconstruct naturalized storage using weather and climate memory','Calculate the residual, examine uncertainty and compare independent observations'])
add('Groundwater storage balance','Methodology',equation='GWSA = TWSA − SMSA − SWSA − CWSA − SWEA',lines=['Subtract soil, surface, canopy and snow storage anomalies','Use common valid cells and a common reference period','Groundwater uncertainty includes every subtracted compartment'],note='Storage anomalies use mm of equivalent water depth. Snow is small in Thailand but retained consistently.')
add('Naturalized and historical simulations','Methodology',table=[['Symbol','Meaning'],['O','Observed or compartment-derived storage'],['C','Naturalized WaterGAP baseline'],['A','Historical WaterGAP with represented human activities']],note='Paired simulations share model structure and forcing. The naturalized baseline remains a model experiment.')
add('Residual accounting','Methodology',equation='R = O − C = (A − C) + (O − A) = H + E',lines=['H describes the human effect represented by the paired model','E retains the observation–historical-model discrepancy','The primary residual uses the published naturalized baseline'],note='The statistical emulator reconstructs C from weather. Its prediction does not replace C in the primary residual.')
add('Chronological model evaluation','Methodology',table=[['Period','Years','Use'],['Warm-up','1981–1990','Initialize climate memory'],['Training','1991–2009','Fit transformations and tune models'],['Validation','2010–2015','Freeze model selection'],['Test','2016–2023','Evaluate unseen years']],note='Ridge, Elastic Net, splines and Random Forest. Predictors exclude GRACE and groundwater observations.')
add('Precipitation and potential ET','Climate forcing',figure='forcing_national',note='National monthly values, 2003–2023. Native P/PET drive reconstruction. CHIRPS supplies the rainfall replacement test.')
add('Spatial distribution of the meteorological inputs','Climate forcing',figure='forcing_spatial',note='Available-month basin means, 2003–2023. Values are mm/month, not annual totals. Each map uses its labelled scale.')
add('Observed storage through time','Objective 1',figure='storage_national',note='National CSR TWSA and compartment-derived GWSA. Missing months remain gaps. Groundwater ends earlier because of compartment availability.')
add('National storage decline','Objective 1',table=[['Storage','Sen slope (mm/year)','Conditional 95% interval'],['Total storage','−7.51','−9.79 to −5.68'],['Groundwater storage','−6.84','−8.77 to −5.11']],note='237 TWSA months through September 2024; 225 GWSA months through September 2023. Full-record seasonal Sen slopes.')
add('Storage trend patterns across basins','Objective 1',figure='storage_slopes',note='Seasonal Sen slopes. Negative values indicate decline. All basins retain the CSR small-area caution.')
add('Statistical evidence for basin trends','Objective 1',figure='trend_evidence',note='Seasonal Mann–Kendall with basin FDR. Colours saturate at q = 0.10. This test does not remove serial dependence or product uncertainty.')
add('Basin ranking depends on the processing chain','Objective 1',figure='05_product_ranking_scatter',note='Common-date rank correlations: TWSA 0.138 and GWSA 0.027. Groundwater chains also differ in compartment processing.')
add('Climate reconstruction performance','Objective 2',figure='climate_scores',note='Ensemble test anomaly NSE against naturalized WaterGAP, 2016–2023. High scores verify reconstruction of the parent model.')
add('Naturalized storage and weather reconstruction','Objective 2',figure='climate_national',note='National series. Training: 1991–2009; validation: 2010–2015; test: 2016–2023. Parent-model agreement is distinct from observational validation.')
add('Climate memory improves reconstruction','Objective 2',figure='13_climate_memory_ablation',note='Controlled Ridge experiment. National test anomaly NSE: current weather / memory = 0.283 / 0.890 for TWSA and 0.039 / 0.723 for GWSA.')
add('Performance varies between test years','Objective 2',figure='annual_skill',note='2022 national anomaly NSE: TWSA 0.234; GWSA −1.067. Negative NSE indicates performance below the mean benchmark.')
add('Residual and modeled human effects differ','Objective 2',figure='residual_national',note='R = H + E on common observed months. The remaining discrepancy includes unresolved model and observation errors.')
add('Spatial residual trends','Objective 2',figure='residual_spatial',note='Calendar-month fixed-effect OLS slopes on matched support. These slopes describe residual change and do not measure pumping.')
rows=[['Component','TWSA','GWSA']]
for comp,label in [('observed_mm','Observed O'),('climate_mm','Naturalized C'),('modeled_human_mm','Modeled human H'),('residual_mm','Residual R'),('discrepancy_mm','Discrepancy E')]:
    rows.append([label,*[f'{ci[(ci.region=="TH")&(ci.variable==v)&(ci.component==comp)&(ci.block_years==2)].ols_slope_mm_year.iloc[0]:.2f}' for v in ['TWSA','GWSA']]])
add('Additive national trend partition','Objective 2',table=rows,note='OLS slopes, mm/year, using the same months. R = H + E. Seasonal Sen slopes are reported separately because their medians are not additive.')
add('GLDAS comparison on matching compartments','Evaluation',figure='gldas_national',note='Soil + canopy + snow only. National r = 0.969, NSE = 0.738, RMSE = 52.49 mm across 261 months. Groundwater and surface water are excluded.')
add('GLDAS agreement varies among basins','Evaluation',figure='gldas_scores',note='Matched land-storage benchmark. NSE colours saturate below −1 and RMSE above 100 mm. GLDAS also contributes to the groundwater subtraction.')
add('Groundwater level and storage use different units','Evaluation',table=[['Observation','What the comparison establishes'],['Groundwater head or depth (m)','Local aquifer response and direction'],['Regional storage anomaly (mm)','Water-mass change over a basin'],['Paired annual correlation','Agreement in timing on observed years']],note='A head-to-storage conversion requires aquifer storage coefficients and representative areas. Those inputs are unavailable here.')
add('Well selection changes residual agreement','Evaluation',table=[['Station panel','TWS r','GWS r','GWS years'],['Longest overlap','0.127','0.037','17'],['Fixed eligibility / wider history','0.657','0.511','17'],['Common period','0.325','0.029','8'],['Strictly balanced','0.305','≈0.000','8']],note='511 wells provide 5,484 aggregates. Co-located wells are grouped. The common-period panels cover eight usable storage years within 2013–2022.')
add('Spatial groundwater consistency','Evaluation',figure='head_spatial',note='Residual–head correlations on available annual pairs. Grey hatching marks insufficient evidence. These comparisons cannot validate a human-only total.')
add('Independent reservoir evidence','Evaluation',figure='reservoir_national',note='26-reservoir fixed panel, 73 scene-supported months. Adjusted r = 0.439, year-cluster 95% interval 0.188–0.665. Both curves remove season and linear trend.')
add('Reservoir agreement and observation support','Evaluation',figure='reservoir_spatial',note='Scene-screened MSEA-Res Level 1. Reservoir storage checks a surface-water component. Climate and operating decisions both affect reservoirs.')
stress=read('precipitation_source_stress_test.csv');rows=[['Storage','Native rainfall','CHIRPS replacement']]
for var in ['TWSA','GWSA']:
    rows.append([var,*[f'{stress[(stress.region=="TH")&(stress.variable==var)&(stress.P_source==src)].deseasonalized_NSE.iloc[0]:.3f}' for src in ['Native_GSWP3_ERA5','CHIRPS_unadjusted']]])
add('Sensitivity to the rainfall source','Evaluation',table=rows,lines=['Test anomaly NSE in the frozen Ridge memory experiment'],note='PET and the native-forced parent target stay fixed. This tests forcing dependence, rather than which rainfall product is more accurate.')
add('Decision support and reproducibility','Objective 3',lines=['Interactive storage histories, trend maps and observation support for all 22 basins','Downloadable basin performance tables and spatial/temporal forcing figures','Input subsets, pinned dependencies and executable scientific workflows'],note='https://pratikkhanal16.github.io/thailand-water-storage-dss/extended/  •  Source repository: pratikkhanal16/thailand-water-storage-dss')
add('Conclusions','Conclusions',lines=['The primary records show national TWSA and GWSA decline','Basin rankings and residual interpretation depend on products and observation support','Climate memory reconstructs the naturalized parent well, with weaker performance in some years','Wells and reservoirs provide complementary, limited evidence for residual interpretation'],note='Contribution: a reproducible joint assessment of product sensitivity, climate memory, paired-model discrepancy and monitoring-network uncertainty.')
add('Selected references','References',lines=['Save et al. (2016), CSR mascons. doi:10.1002/2016JB013007','Müller Schmied et al. (2024), WaterGAP. doi:10.5194/gmd-17-8817-2024','Sharifi et al. (2025), groundwater storage. doi:10.5194/hess-29-6985-2025','MSEA-Res (2025), reservoir storage. doi:10.5194/essd-17-2693-2025','GROW groundwater observations. doi:10.5281/zenodo.15149480'],note='Full bibliography, source terms and basin results accompany the report. Theme: Metropolis by Matthias Vogelgesang and contributors, https://github.com/matze/mtheme.')
main=len(slides)
add('Supporting results','Backup',lines=['Additional hydroclimatic context','Basin performance tables for questions','Observation support and interpretation'],layout='divider',backup=True)
add('Supporting hydroclimatic histories','Backup',figure='supporting_temporal',note='National monthly observations, 2003–2023. Actual ET, soil moisture and surface temperature provide context; they are not added primary predictors.',backup=True)
add('Spatial hydroclimatic context','Backup',figure='supporting_spatial',note='Basin available-month means, 2003–2023. Product coverage differs. Volumetric moisture is distinct from storage in mm.',backup=True)
add('Spatial support and uncertainty','Backup',lines=['National aggregation touches 68 native CSR mascons','Inverse weight concentration is about 50.1 and does not count independent observations','Every principal basin is below the provider’s approximate 200,000 km² small-area caution','Conditional intervals do not include all gravity, compartment and hydrological-model errors'],backup=True)
inventory=json.loads((O/'basin_forcing_appendix/table_inventory.json').read_text(encoding='utf-8'))
for id in [1,2,3,6,7]:
    x=next(x for x in inventory if x['id']==id);g=pd.read_csv(O/'basin_forcing_appendix/tables'/x['file'],dtype={'region':str})
    def val(v,col):
        if col=='region':return str(v)
        if pd.isna(v):return '—'
        if col=='n' or col.endswith('_n') or col.endswith('_years'):return str(int(v))
        if col.endswith('_q'):return '<.001' if v<.001 else f'{v:.3f}'
        return f'{v:.3f}' if 'NSE' in col or col=='r' or col.endswith('_r') else f'{v:.2f}'
    for start in [0,11]:
        rows=[x['headers']]+[[val(row[c],c) for c in x['columns']] for _,row in g.iloc[start:start+11].iterrows()]
        add(x['title']+f' ({start+1:02d}–{start+11:02d})','Basin tables',table=rows,note=x['note'],backup=True)
add('Complete basin results and source data','Backup',lines=['Report Appendix C: 11 tables for every basin','Report Appendix D: 10 spatial and temporal forcing figures','The website supplies full-precision CSVs, vector figures and runnable code'],note='https://pratikkhanal16.github.io/thailand-water-storage-dss/extended/basin_forcing/',backup=True)
(P/'academic_slides.json').write_text(json.dumps({'main_slides':main,'slides':slides},ensure_ascii=False,indent=2),encoding='utf-8')

def esc(s):
    return ''.join({'&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','≈':r'$\approx$','−':r'$-$','³':r'$^3$'}.get(c,c) for c in str(s))
tex=[r'''\documentclass[aspectratio=169,11pt]{beamer}
\usepackage{fontspec}
\usetheme[progressbar=frametitle,numbering=fraction,sectionpage=none]{metropolis}
\IfFontExistsTF{Arial}{\setsansfont{Arial}\setmainfont{Arial}}{\setsansfont{TeX Gyre Heros}\setmainfont{TeX Gyre Heros}}
\usepackage{graphicx,booktabs,array,amsmath}
\definecolor{researchnavy}{HTML}{203A49}
\definecolor{researchteal}{HTML}{368C83}
\definecolor{researchpaper}{HTML}{FAFAF8}
\setbeamercolor{normal text}{fg=researchnavy,bg=researchpaper}
\setbeamercolor{frametitle}{bg=researchnavy,fg=white}
\setbeamercolor{alerted text}{fg=researchteal}
\setbeamercolor{progress bar}{fg=researchteal,bg=researchnavy!12}
\setbeamersize{text margin left=8mm,text margin right=8mm}
\setbeamerfont{frametitle}{size=\large,series=\bfseries}
\setbeamerfont{footnote}{size=\scriptsize}
\setbeamertemplate{navigation symbols}{}
\title{Water storage change across Thailand}
\subtitle{Climate reconstruction and the limits of human attribution}
\author{Farzeen Khan}
\institute{MS in Water Engineering and Management\\Asian Institute of Technology\\[2mm]Advisor: Dr. Natthachet Tangdamrongsub}
\date{October 2026}
\newcommand{\sourcenote}[1]{\vfill\par{\fontsize{7.1}{8.4}\selectfont\color{researchnavy!75}#1}}
\begin{document}
''']
for i,s in enumerate(slides):
    if i==main:tex.append(r'\appendix')
    if s['layout']=='title':
        tex.append(r'\begin{frame}[plain]\vspace{3mm}{\LARGE\bfseries Water storage change across Thailand}\par\vspace{3mm}{\large\color{researchteal}Climate reconstruction and the limits of human attribution}\par\vspace{7mm}{\large Farzeen Khan}\par\vspace{2mm}{\small MS in Water Engineering and Management\\Asian Institute of Technology}\par\vspace{5mm}{\small Advisor: Dr. Natthachet Tangdamrongsub}\par\vspace{2mm}{\small October 2026}\end{frame}');continue
    tex.append(r'\begin{frame}{'+esc(s['title'])+'}')
    if s['layout']=='split':
        tex.append(r'\begin{columns}[c]\begin{column}{.43\textwidth}\centering\includegraphics[height=.65\textheight]{figures/'+s['figure']+r'.pdf}\end{column}\begin{column}{.54\textwidth}\begin{itemize}')
        tex.extend(r'\item '+esc(x) for x in s['lines']);tex.append(r'\end{itemize}\end{column}\end{columns}')
    elif s['figure']:tex.append(r'\centering\includegraphics[width=\textwidth,height=.64\textheight,keepaspectratio]{figures/'+s['figure']+'.pdf}')
    elif s['table']:
        n=len(s['table'][0]);dense=len(s['table'])>8
        if s['lines']:tex.append(esc(s['lines'][0])+r'\par\vspace{2mm}')
        cols=''.join(r'>{\raggedright\arraybackslash}p{'+str(round((.88 if dense else .92)/n,3))+r'\textwidth}' for _ in range(n))
        tex.append((r'\fontsize{8.5}{10}\selectfont' if dense else r'\small')+r'\setlength{\tabcolsep}{3pt}\renewcommand{\arraystretch}{'+('1.0' if dense else '1.35')+r'}\begin{tabular}{'+cols+r'}\toprule')
        for j,row in enumerate(s['table']):tex.append(' & '.join(r'\textbf{'+esc(c)+'}' if j==0 else esc(c) for c in row)+r'\\'+(r'\midrule' if j==0 else ''))
        tex.append(r'\bottomrule\end{tabular}')
    else:
        if s['equation']:
            eq=r'\mathrm{GWSA}=\mathrm{TWSA}-\mathrm{SMSA}-\mathrm{SWSA}-\mathrm{CWSA}-\mathrm{SWEA}' if 'GWSA =' in s['equation'] else r'R=O-C=\underbrace{(A-C)}_{H}+\underbrace{(O-A)}_{E}'
            tex.append(r'\[ '+eq+r' \]')
        tex.append(r'\begin{itemize}\setlength{\itemsep}{3mm}')
        tex.extend(r'\item '+esc(x) for x in s['lines']);tex.append(r'\end{itemize}')
    if s['note']:tex.append(r'\sourcenote{'+esc(s['note'])+'}')
    tex.append(r'\end{frame}')
tex.append(r'\end{document}');(P/'Thailand_Academic_Metropolis.tex').write_text('\n'.join(tex),encoding='utf-8')
(P/'design_contract.json').write_text(json.dumps({'theme':'Metropolis','font':'Arial','main_slides':main,'backup_slides':len(slides)-main,'total_slides':len(slides),'scientific_refit':False},indent=2))
print('Academic deck:',main,'main +',len(slides)-main,'backup slides.')
