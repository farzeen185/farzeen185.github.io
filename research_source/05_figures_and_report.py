"""Publication-ready scientific figures and concise verified research report."""
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import xarray as xr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from research_common import ROOT,OBJ1,OBJ2
F=OBJ2/'figures';F.mkdir(exist_ok=True);R=ROOT/'reports'
read=lambda p:pd.read_csv(p,dtype={'region':str})
storage=read(OBJ1/'tables/basin_storage_timeseries.csv');trend=read(OBJ1/'tables/basin_TWSA_GWSA_Sen_MannKendall.csv')
model=read(OBJ2/'tables/ensemble_validation.csv');forecast=read(OBJ2/'tables/basin_climate_residual_timeseries.csv');residual=read(OBJ2/'tables/climate_residual_Sen_MannKendall.csv')
wells=read(OBJ2/'tables/groundwater_well_basin_assignment.csv');indices=read(OBJ2/'tables/basin_groundwater_observation_indices.csv');agreement=read(OBJ2/'tables/groundwater_storage_residual_agreement.csv');pressure=read(OBJ2/'tables/residual_irrigation_spatial_association.csv')
geo=gpd.read_file(ROOT/'Thailand_Objective2/data/BASINS/MainBasin_ONWR_Law_WGS84.shp').to_crs(4326);geo['region']=geo.MB_CODE.str.split('-').str[0].str.zfill(2);geo=geo.dissolve(by='region',as_index=False,aggfunc='first')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold'})
def save(fig,name):fig.tight_layout();fig.savefig(F/name,dpi=220,bbox_inches='tight');plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(11,8))
for ax,var in zip(axes,['TWSA','GWSA']):
    g=trend[(trend.variable==var)&(trend.region!='TH')].sort_values('sen_slope_mm_year');y=np.arange(len(g))
    ax.errorbar(g.sen_slope_mm_year,y,xerr=[g.sen_slope_mm_year-g.sen_lo95_mm_year,g.sen_hi95_mm_year-g.sen_slope_mm_year],fmt='o',color='#147d79',ecolor='#80b3a5',capsize=2)
    ax.set_yticks(y,g.region_name.str.replace('Peninsula - ','Peninsula '),fontsize=8);ax.axvline(0,color='#aaa',lw=.7);ax.set(title=var,xlabel='Seasonal Sen slope (mm/year)')
save(fig,'all_basins_storage_trend_intervals.png')
fig,axes=plt.subplots(1,2,figsize=(11,7))
for ax,var in zip(axes,['TWSA','GWSA']):
    g=residual[(residual.variable==var)&(residual.component=='unexplained_residual')&(residual.region!='TH')];z=geo.merge(g,on='region');lim=max(1,g.sen_slope_mm_year.abs().max())
    z.plot(column='sen_slope_mm_year',cmap='RdBu',vmin=-lim,vmax=lim,ax=ax,edgecolor='#64766e',linewidth=.3,legend=True,legend_kwds={'label':'Residual Sen slope (mm/year)','shrink':.6});ax.set(title=var+' candidate human residual',xlabel='Longitude (°E)',ylabel='Latitude (°N)');ax.set_aspect('equal')
save(fig,'candidate_human_residual_basin_trends.png')
fig,axes=plt.subplots(2,1,figsize=(12,7),sharex=True)
for ax,var in zip(axes,['TWSA','GWSA']):
    g=forecast[(forecast.region=='TH')&(forecast.variable==var)];d=pd.to_datetime(g.date);end=g.loc[g.observed_mm.notna(),'date'].max();g=g.copy();g.loc[g.date>end,['climate_mm','empirical_lower_mm','empirical_upper_mm']]=np.nan
    ax.fill_between(d,g.empirical_lower_mm,g.empirical_upper_mm,color='#8cc3b5',alpha=.23,label='Validation-error band')
    for field,label,color in [('observed_mm','Observed storage','#263f42'),('climate_mm','Climate reconstruction','#137d78'),('unexplained_residual_mm','Candidate human residual','#b9633b')]:ax.plot(d,g[field],label=label,color=color,lw=1.4)
    ax.set_ylabel(var+' (mm)');ax.axhline(0,color='#aaa',lw=.6);ax.legend(ncol=4,fontsize=9,loc='upper right')
save(fig,'national_climate_residual_reconstruction.png')
test=model[(model.period=='Test')&(model.region!='TH')]
fig,axes=plt.subplots(1,2,figsize=(11,8))
for ax,var in zip(axes,['TWSA','GWSA']):
    g=test[test.variable==var].sort_values('NSE');y=np.arange(len(g));ax.barh(y,g.NSE,color='#147d79',label='Full monthly NSE');ax.scatter(g.deseasonalized_NSE,y,color='#b9633b',s=24,label='Deseasonalized NSE');ax.set_yticks(y,g.region_name.str.replace('Peninsula - ','Peninsula '),fontsize=8);ax.axvline(0,color='#aaa',lw=.7);ax.set(title=var+' independent test',xlabel='Nash–Sutcliffe efficiency');ax.legend(fontsize=8)
save(fig,'all_basins_climate_test_skill.png')
fig,axes=plt.subplots(1,2,figsize=(11,7))
count=wells.groupby('region').well_id.nunique().rename('wells').reset_index();geo.merge(count,on='region',how='left').fillna({'wells':0}).plot(column='wells',ax=axes[0],cmap='YlGnBu',legend=True,legend_kwds={'label':'Actual historical wells','shrink':.65},edgecolor='#888',linewidth=.3);axes[0].set(title='511 wells; five monthly',xlabel='Longitude (°E)',ylabel='Latitude (°N)');axes[0].set_aspect('equal')
for quality,label,color in [('retained_flags','Changing observation network','#137d78'),('fixed_2013_2022_panel','Fixed eligibility panel','#b9633b')]:
    g=indices[(indices.region=='TH')&(indices.interval=='YS')&(indices.quality==quality)];axes[1].plot(pd.to_datetime(g.date).dt.year,g.well_head_z,'o-',label=label,color=color)
axes[1].set(title='Annual groundwater head indices',xlabel='Year',ylabel='Standardized sign-corrected head');axes[1].legend(fontsize=9)
save(fig,'groundwater_coverage_and_indices.png')
with xr.open_dataset(OBJ1/'netcdf/spatial_Sen_MannKendall.nc') as ds:
    fig,axes=plt.subplots(1,2,figsize=(11,8))
    for ax,var in zip(axes,['TWSA','GWSA']):
        z=ds[var+'_sen_slope_mm_year'];lim=np.nanmax(abs(z));z.plot(ax=ax,cmap='RdBu',vmin=-lim,vmax=lim,cbar_kwargs={'label':'Sen slope (mm/year)','shrink':.65});geo.boundary.plot(ax=ax,color='#222',linewidth=.3);ax.set(title=var+' grid trend');ax.set_aspect('equal')
    save(fig,'spatial_grid_storage_trends.png')
summary={'national_trends':trend[(trend.region=='TH')&(trend.variable.isin(['TWSA','GWSA']))].to_dict('records'),'national_test':model[(model.region=='TH')&(model.period=='Test')].to_dict('records'),
 'national_well_agreement':agreement[(agreement.region=='TH')&(agreement.interval=='YS')&(agreement.quality=='retained_flags')].to_dict('records'),'fixed_panel_agreement':agreement[(agreement.region=='TH')&(agreement.interval=='YS')&(agreement.quality=='fixed_2013_2022_panel')&(agreement.component=='observed_storage')&(agreement.scope=='all_overlap')].to_dict('records'),
 'pressure_associations':pressure.to_dict('records'),'basin_test':test.to_dict('records'),'basin_trends':trend[(trend.region!='TH')&(trend.variable.isin(['TWSA','GWSA']))].to_dict('records')}
# Pandas JSON normalizes missing values to JSON null.
(R/'verified_research_results.json').write_text(pd.Series(summary).to_json(force_ascii=False,indent=2),encoding='utf-8')
lines=['# Thailand water-storage research: completed three-objective release','','All 22 principal basins plus Thailand national aggregate; 46 climate ensembles and 1,380 candidate model configurations.','','## Results']
for x in summary['national_trends']:lines.append(f"- National {x['variable']}: seasonal Sen {x['sen_slope_mm_year']:.2f} mm/year, block-bootstrap 95% interval {x['sen_lo95_mm_year']:.2f} to {x['sen_hi95_mm_year']:.2f}; {x['n_months']} observed months.")
for x in summary['national_test']:lines.append(f"- National {x['variable']} test: NSE {x['NSE']:.3f}, r {x['r']:.3f}, RMSE {x['RMSE_mm']:.2f} mm, deseasonalized NSE {x['deseasonalized_NSE']:.3f}; n={x['n']}.")
lines+=['','## Groundwater evidence','Actual 5,484 observation aggregates from 511 Thai wells: 506 annual and five monthly. All assigned to a principal basin. Most annual values represent only two original readings. Aquifer storage coefficients and aquifer identities are unavailable.']
for x in summary['national_well_agreement']:
    if x['scope']=='all_overlap':lines.append(f"- {x['variable']} {x['component']}: annual n={x['n']}, r={x.get('r')} (exploratory; no causal attribution).")
lines+=['','Observation-network composition changes affect agreement; fixed-panel and source-flag sensitivities are reported alongside primary results. Post-2015 GWS has fewer than six paired annual years, so correlation is not reported.','','## Interpretation and limits','Negative storage trends are observed signals. Climate reconstruction primarily captures seasonality. Residuals include candidate human influence and unresolved errors, and are not established anthropogenic pumping volumes. GLDAS Noah has no groundwater compartment. G3P is a related benchmark, not independent groundwater validation. Modelled surface water ends September 2023; missing GRACE dates remain missing. Compartment filtering differences and coarse GRACE resolution constrain spatial interpretation. Seasonal MK p-values remain subject to serial dependence; bootstrap slope intervals and FDR q-values do not remove that limitation.','','## Deliverables','- Objective 1: `Thailand_Objective1/analysis_v3/` (NetCDF, trends, time series, figures).','- Objective 2: `Thailand_Objective2/analysis_v3/` (models, validation, residuals, real-well checks).','- Objective 3: `Thailand_Objective3/web_app/`; https://pratikkhanal16.github.io/thailand-water-storage-dss/','- Presentation: `Thailand_Objective3/outputs/Thailand_Three_Objectives_Research.pptx`.','','The earlier `outputs_advanced` analysis is retained as historical work; `analysis_v3` is the authoritative release. Large globally downloaded intermediates may be removed after verified Thai extraction, with an audit log. Original local inputs are retained.']
(R/'RESEARCH_RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Scientific figures and verified research report written.')
