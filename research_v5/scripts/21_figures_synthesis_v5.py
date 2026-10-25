"""Publication figures and machine-readable synthesis from completed v5 tests."""
import json,warnings
import h5py,numpy as np,pandas as pd,geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from research_common import ROOT
OUT=ROOT/'Thailand_Research_v5';F=OUT/'figures'
read=lambda n:pd.read_csv(OUT/'tables'/n,dtype={'region':str})
t=read('CSR_basin_trends.csv');series=read('CSR_basin_storage_timeseries.csv');a=read('common_support_product_audit.csv');s=read('native_mascon_support.csv');shared=read('basin_shared_support.csv');at=read('CSR_naturalized_attribution.csv');ci=read('attribution_wild_block_intervals.csv');D=read('discrepancy_magnitude_diagnostic.csv');ab=read('climate_feature_ablation.csv');ps=read('precipitation_source_stress_test.csv');lag=read('heldout_precipitation_storage_response.csv');gw=read('CSR_groundwater_network_evidence.csv');cover=read('groundwater_station_coverage.csv');wt=read('well_level_trend_and_agreement.csv');gs=read('groundwater_station_trend_summary.csv');windows=read('trend_window_sensitivity.csv');hc=read('multisource_hydroclimate_series.csv')
names=dict(zip(s.region,s.region_name));codes=sorted(x for x in names if x!='TH');labels=[names[x] for x in codes]
short={'03':'Northeast Khong','18':'Phetchaburi/Prachuap','19':'Upper east coast','20':'Songkhla','21':'Lower east coast','22':'West coast'}
labels=[code+' '+short.get(code,names[code]) for code in codes]
geo=gpd.read_file(ROOT/'Thailand_Objective2/data/BASINS/MainBasin_ONWR_Law_WGS84.shp').to_crs(4326);geo['region']=geo.MB_CODE.astype(str).str.split('-').str[0].str.zfill(2);geo=geo.dissolve(by='region',as_index=False,aggfunc='first')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':15,'axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'white'})
def save(fig,name,tight=True):
    if tight:fig.tight_layout()
    fig.savefig(F/(name+'.png'),dpi=240,bbox_inches='tight');fig.savefig(F/(name+'.pdf'),bbox_inches='tight');plt.close(fig)
def basemap(ax,frame,col,title,cmap='RdBu',lim=None):
    z=geo.merge(frame[['region',col]],on='region',how='left');kw={}
    if lim is not None:
        if cmap=='RdBu' and lim[0]<0<lim[1]:kw['norm']=TwoSlopeNorm(vmin=lim[0],vcenter=0,vmax=lim[1])
        else:kw.update(vmin=lim[0],vmax=lim[1])
    z.plot(column=col,ax=ax,cmap=cmap,legend=True,edgecolor='#56646b',linewidth=.4,missing_kwds={'color':'#dddddd'},legend_kwds={'shrink':.7},**kw);ax.set(title=title,xlabel='Longitude (°E)',ylabel='Latitude (°N)');ax.set_aspect('equal')
fig,ax=plt.subplots(figsize=(7,9));geo.plot(ax=ax,color='#e7eef0',edgecolor='#506771',linewidth=.7)
for _,r in geo.iterrows():p=r.geometry.representative_point();ax.text(p.x,p.y,r.region,fontsize=8,ha='center',va='center')
ax.set(title='Thailand principal basins and analysis codes',xlabel='Longitude (°E)',ylabel='Latitude (°N)');save(fig,'01_study_basins')
fig,axes=plt.subplots(2,1,figsize=(10,7),sharex=True)
for ax,var in zip(axes,['TWSA','GWSA']):
    g=series[series.region=='TH'];ax.plot(pd.to_datetime(g.date),g[var],color='#185d75',lw=1.5);ax.axhline(0,color='#999',lw=.6);ax.set_ylabel(var+' (mm)')
axes[0].set_title('National CSR-based storage; missing GRACE months retained');save(fig,'02_national_storage')
fig,axes=plt.subplots(1,2,figsize=(12,9),sharey=True)
for ax,var in zip(axes,['TWSA','GWSA']):
    g=t[(t.variable==var)&(t.region!='TH')].set_index('region').reindex(codes);y=np.arange(len(codes));ax.errorbar(g.sen_slope_mm_year,y,xerr=np.vstack([g.sen_slope_mm_year-g.sen_lo95_mm_year,g.sen_hi95_mm_year-g.sen_slope_mm_year]),fmt='o',color='#185d75',capsize=2,ms=4);ax.axvline(0,color='#888',lw=.6);ax.set(title=var,xlabel='Seasonal Sen slope (mm/year)');ax.set_yticks(y,labels);ax.invert_yaxis()
save(fig,'03_basin_sen_intervals')
fig,axes=plt.subplots(1,2,figsize=(10,9))
for ax,var in zip(axes,['TWSA','GWSA']):basemap(ax,t[t.variable==var],'sen_slope_mm_year',var+' Sen (mm/year)',lim=(-45,5))
save(fig,'04_basin_trend_maps')
fig,axes=plt.subplots(1,2,figsize=(10,5))
for ax,var in zip(axes,['TWSA','GWSA']):
    g=a[(a.variable==var)&(a.region!='TH')].pivot(index='region',columns='source',values='sen_slope_mm_year');ax.scatter(g.CSR,g.COSTG_G3P,color='#b66a3c',s=35)
    lim=[min(g.CSR.min(),g.COSTG_G3P.min())-1,max(g.CSR.max(),g.COSTG_G3P.max())+1];ax.plot(lim,lim,color='#aaa',ls='--');ax.set(title=var+' full-chain product comparison',xlabel='CSR-based Sen (mm/year)',ylabel='COST-G/G3P Sen (mm/year)')
save(fig,'05_product_ranking_scatter')
fig,ax=plt.subplots(figsize=(10,8));g=t[(t.region!='TH')&t.variable.isin(['GWSA','GWSA_filtered_soil'])].pivot(index='region',columns='variable',values='sen_slope_mm_year').reindex(codes);native=a[(a.region!='TH')&(a.variable=='GWSA')&(a.source=='COSTG_G3P')].set_index('region').reindex(codes)
for i,(field,label,color) in enumerate([('GWSA','CSR + Noah soil','#185d75'),('GWSA_filtered_soil','CSR + filtered root-zone soil','#288c82')]):ax.scatter(g[field],np.arange(22)+(i-1)*.15,label=label,color=color,s=22)
ax.scatter(native.sen_slope_mm_year,np.arange(22)+.15,label='COST-G/G3P groundwater',color='#b66a3c',s=22);ax.set_yticks(np.arange(22),labels);ax.invert_yaxis();ax.set_xlabel('Sen slope (mm/year); component/source definitions differ');ax.legend(loc='lower left',fontsize=8);save(fig,'06_groundwater_product_structure')
fig,ax=plt.subplots(figsize=(9,8));matrix=shared[shared.region_a.isin(codes)&shared.region_b.isin(codes)].pivot(index='region_a',columns='region_b',values='shared_native_weight').reindex(index=codes,columns=codes);im=ax.imshow(matrix,vmin=0,vmax=1,cmap='YlGnBu');ax.set_xticks(range(22),codes,rotation=90);ax.set_yticks(range(22),labels);fig.colorbar(im,ax=ax,label='Shared native-mascon weight (not error covariance)');save(fig,'07_shared_native_support')
fig,ax=plt.subplots(figsize=(10,5));z=s[s.region!='TH'];ax.scatter(z.basin_area_km2,z.native_weight_concentration_count,color='#185d75',s=35)
for r in z.itertuples():ax.annotate(r.region,(r.basin_area_km2,r.native_weight_concentration_count),xytext=(3,3),textcoords='offset points',fontsize=8)
ax.set(xlabel='Basin polygon/intersection area (km²)',ylabel='Inverse native-weight concentration',title='Nominal support concentration is not independent information');save(fig,'08_support_concentration')
fig,axes=plt.subplots(2,2,figsize=(12,8),sharex=True)
for row,var in enumerate(['TWSA','GWSA']):
    g=at[(at.region=='TH')&(at.variable==var)];date=pd.to_datetime(g.date)
    for key,label,color in [('observed_mm','Observed','#1f343e'),('climate_mm','Naturalized','#288c82'),('historical_human_mm','Historical-human','#b66a3c')]:axes[row,0].plot(date,g[key],label=label,color=color,lw=1.1)
    for key,label,color in [('residual_mm','Residual R','#b66a3c'),('modeled_human_mm','Modeled human H','#288c82'),('discrepancy_mm','Discrepancy E','#7b78a4')]:axes[row,1].plot(date,g[key],label=label,color=color,lw=1.1)
    axes[row,0].set_ylabel(var+' (mm)');axes[row,1].set_ylabel(var+' (mm)')
for ax in axes[0]:ax.legend(fontsize=8,loc='upper right')
save(fig,'09_paired_national_decomposition')
fig,axes=plt.subplots(1,2,figsize=(11,5),sharey=True);fields=['observed_mm','climate_mm','modeled_human_mm','residual_mm','discrepancy_mm'];flabel=['Observed','Naturalized','Modeled human','Residual','Discrepancy']
for ax,var in zip(axes,['TWSA','GWSA']):
    g=ci[(ci.region=='TH')&(ci.variable==var)&(ci.block_years==2)].set_index('component').reindex(fields);ax.errorbar(g.ols_slope_mm_year,np.arange(5),xerr=np.vstack([g.ols_slope_mm_year-g.lo95,g.hi95-g.ols_slope_mm_year]),fmt='o',color='#185d75',capsize=3);ax.axvline(0,color='#999',lw=.7);ax.set(title=var,xlabel='Fixed-month OLS slope (mm/year)');ax.set_yticks(range(5),flabel);ax.invert_yaxis()
save(fig,'10_additive_slope_uncertainty')
fig,axes=plt.subplots(1,2,figsize=(10,9))
for ax,var in zip(axes,['TWSA','GWSA']):basemap(ax,D[(D.variable==var)&(D.block_years==2)],'discrepancy_magnitude_index',var+' discrepancy magnitude D','YlOrBr',(0,1))
save(fig,'11_discrepancy_diagnostic_maps')
fig,axes=plt.subplots(1,2,figsize=(11,5),sharey=True)
for ax,var in zip(axes,['TWSA','GWSA']):
    for i,(length,color) in enumerate([(1,'#185d75'),(2,'#288c82'),(3,'#b66a3c')]):
        g=ci[(ci.region=='TH')&(ci.variable==var)&(ci.block_years==length)].set_index('component').reindex(fields);ax.errorbar(g.ols_slope_mm_year,np.arange(5)+(i-1)*.16,xerr=np.vstack([g.ols_slope_mm_year-g.lo95,g.hi95-g.ols_slope_mm_year]),fmt='o',label=f'{length}-year blocks',color=color,ms=3,capsize=2)
    ax.axvline(0,color='#aaa',lw=.6);ax.set_yticks(range(5),flabel);ax.invert_yaxis();ax.set(title=var,xlabel='OLS slope and conditional 95% interval (mm/year)')
axes[0].legend(fontsize=8);save(fig,'12_block_length_sensitivity')
fig,axes=plt.subplots(1,2,figsize=(11,5),sharey=True);groups=['Season_only','Current_weather','Weather_lags','Weather_memory','Weather_without_season'];gl=['Season','Current','Lags','Memory','No season']
for ax,var in zip(axes,['TWSA','GWSA']):
    g=ab[(ab.variable==var)&(ab.period=='Test')];ax.boxplot([g[(g.feature_group==group)&(g.region!='TH')].deseasonalized_NSE for group in groups],tick_labels=gl,showfliers=True);national=g[g.region=='TH'].set_index('feature_group').reindex(groups);ax.scatter(np.arange(1,6),national.deseasonalized_NSE,color='#b66a3c',label='National',zorder=4);ax.axhline(0,color='#aaa',ls='--',lw=.7);ax.set(title=var,ylabel='Held-out deseasonalized NSE');ax.tick_params(axis='x',rotation=25)
axes[0].legend();save(fig,'13_climate_memory_ablation')
fig,axes=plt.subplots(1,2,figsize=(11,5),sharey=True)
for ax,var in zip(axes,['TWSA','GWSA']):
    g=ps[(ps.variable==var)&(ps.region!='TH')].pivot(index='region',columns='P_source',values='deseasonalized_NSE')
    for key,color,label in [('CHIRPS_unadjusted','#b66a3c','CHIRPS'),('CHIRPS_training_monthly_mean_adjusted','#288c82','CHIRPS mean-adjusted')]:ax.scatter(g.Native_GSWP3_ERA5,g[key],color=color,label=label,s=25,alpha=.8)
    lim=[min(-.1,axes[0].get_ylim()[0],g.min().min()),1.02];ax.plot([0,1],[0,1],color='#aaa',ls='--');ax.set(title=var,xlabel='Native-forcing anomaly NSE',ylabel='Changed-forcing anomaly NSE');ax.legend(fontsize=8)
save(fig,'14_precipitation_source_stress')
fig,axes=plt.subplots(1,2,figsize=(11,8),sharey=True)
for ax,var in zip(axes,['TWSA','GWSA']):
    g=lag[(lag.variable==var)&(lag.region!='TH')].set_index('region').reindex(codes);colors=np.where(g.test_q_FDR<.05,'#185d75','#b4bfc3');ax.barh(np.arange(22),g.test_r,color=colors);ax.set_yticks(range(22),labels);ax.invert_yaxis();ax.set(title=var+' held-out P response',xlabel='2016–2023 Pearson r; dark q<0.05');ax.set_xlim(-1,1)
save(fig,'15_heldout_rainfall_response')
fig,axes=plt.subplots(3,2,figsize=(11,9));g=hc[hc.region=='TH'].copy();g['month']=pd.to_datetime(g.date).dt.month;cl=g.groupby('month').mean(numeric_only=True)
for ax,var,title in zip(axes.ravel(),['CHIRPS_P','GLEAM_ET','MODIS_ET','ESA_CCI_SSM','ESA_CCI_RZSM','MODIS_LST'],['Rainfall (mm/month)','GLEAM ET (mm/month)','MODIS ET (mm/month)','Surface soil moisture (m³/m³)','Root-zone moisture (m³/m³)','Land surface temperature (°C)']):ax.plot(cl.index,cl[var],'-o',color='#185d75',ms=3);ax.set(title=title,xlabel='Calendar month');ax.set_xticks([1,3,5,7,9,11])
save(fig,'16_hydroclimate_seasonality')
fig,ax=plt.subplots(figsize=(11,8));g=cover[(cover.region!='TH')&(cover.quality=='retained_flags')].pivot(index='region',columns='year',values='station_groups_observed').reindex(codes).fillna(0);im=ax.imshow(np.log1p(g),aspect='auto',cmap='YlGnBu');ax.set_yticks(range(22),labels);ax.set_xticks(range(len(g.columns)),g.columns,rotation=90);fig.colorbar(im,ax=ax,label='log(1 + observed coordinate station groups)');ax.set_title('Annual observation-network coverage; no inferred measurements');save(fig,'17_well_network_coverage')
fig,axes=plt.subplots(1,2,figsize=(11,5),sharey=True);quality=['retained_flags','exclude_flagged','fixed_2013_2022','common_period_retained','strict_balanced_2013_2022'];ql=['All overlap','Exclude flags','Fixed eligibility','Common period','Strict balanced']
for ax,var in zip(axes,['TWSA','GWSA']):
    z=gw[(gw.region=='TH')&(gw.variable==var)&(gw.component=='residual_mm')].set_index('quality').reindex(quality);ax.plot(np.arange(5),z.r,'o-',label='Raw',color='#185d75');ax.plot(np.arange(5),z.climate_controlled_r,'s--',label='Climate controlled',color='#288c82');ax.plot(np.arange(5),z.detrended_r,'^:',label='Detrended',color='#b66a3c');ax.axhline(0,color='#aaa',lw=.7);ax.set(title=var+' residual / head',ylim=(-1,1),ylabel='Pearson correlation');ax.set_xticks(range(5),ql,rotation=30,ha='right')
axes[0].legend(fontsize=8);save(fig,'18_network_panel_sensitivity')
fig,axes=plt.subplots(1,2,figsize=(11,5));station=wt.groupby('station_group').head_sen_m_year.median();axes[0].hist(station,bins=25,color='#185d75',alpha=.85);axes[0].axvline(0,color='#b66a3c');axes[0].set(xlabel='Station-median head Sen slope (m/year)',ylabel='Coordinate station groups',title='Eligible annual head trajectories')
g=gs[gs.region!='TH'].set_index('region').reindex(codes).dropna();axes[1].errorbar(g.declining_station_fraction,np.arange(len(g)),xerr=np.vstack([g.declining_station_fraction-g.fraction_lo95,g.fraction_hi95-g.declining_station_fraction]),fmt='o',ms=3,color='#185d75');axes[1].set_yticks(range(len(g)),[names[c] for c in g.index]);axes[1].invert_yaxis();axes[1].set(xlim=(0,1),xlabel='Fraction with declining head; station bootstrap',title='Head direction is not storage volume');save(fig,'19_station_trend_directions')
fig,ax=plt.subplots(figsize=(10,8));z=gw[(gw.variable=='GWSA')&(gw.component=='residual_mm')&(gw.quality=='retained_flags')&(gw.region!='TH')].set_index('region').reindex(codes);valid=z.station_bootstrap_lo95.notna();y=np.arange(22);ax.hlines(y[valid],z.loc[valid,'station_bootstrap_lo95'],z.loc[valid,'station_bootstrap_hi95'],color='#185d75');ax.scatter(z.loc[valid,'r'],y[valid],color='#185d75',s=20);ax.set_yticks(y,labels);ax.invert_yaxis();ax.axvline(0,color='#aaa');ax.set(xlim=(-1,1),xlabel='GWS residual / head r and station-resampling 95% interval',title='Missing intervals identify inadequate observation support');save(fig,'20_basin_groundwater_uncertainty')
fig,axes=plt.subplots(1,2,figsize=(11,9),sharey=True)
for ax,var in zip(axes,['TWSA','GWSA']):
    g=windows[(windows.variable==var)&(windows.component=='observed_mm')&(windows.region!='TH')].pivot(index='region',columns='window',values='seasonal_sen_mm_year').reindex(codes);cols=['common_2003_2023','early_record','later_record','pre_mission_gap','post_mission_gap'];g=g.reindex(columns=cols);im=ax.imshow(g,aspect='auto',cmap='RdBu',vmin=-30,vmax=30);ax.set_yticks(range(22),labels);ax.set_xticks(range(5),['2003–23','2003–10','2012–23','2003–16','2019–23'],rotation=45,ha='right');ax.set_title(var)
fig.tight_layout(rect=(0,0,.90,1));cax=fig.add_axes([.92,.2,.02,.6]);fig.colorbar(im,cax=cax,label='mm/year');save(fig,'21_trend_window_sensitivity',tight=False)
# Dedicated source/metric inventory: one authority for the writing pipeline.
summary={'author':'Farzeen Khan','release':'2026-10-24','national_trends':t[t.region=='TH'].to_dict('records'),'national_product_audit':a[a.region=='TH'].to_dict('records'),'national_OLS_intervals':ci[ci.region=='TH'].to_dict('records'),'national_discrepancy':D[D.region=='TH'].to_dict('records'),'national_ablation':ab[(ab.region=='TH')&(ab.period=='Test')].to_dict('records'),'national_forcing_stress':ps[ps.region=='TH'].to_dict('records'),'national_observed_lag':lag[lag.region=='TH'].to_dict('records'),'national_groundwater':gw[gw.region=='TH'].to_dict('records'),'national_well_directions':gs[gs.region=='TH'].to_dict('records'),'product_ranking':read('product_ranking_robustness.csv').to_dict('records'),'basin_support':s.to_dict('records'),'basin_trends':t[t.region!='TH'].to_dict('records'),'basin_OLS_intervals':ci[(ci.region!='TH')&(ci.block_years==2)].to_dict('records'),'basin_groundwater':gw[(gw.region!='TH')&(gw.quality=='retained_flags')&(gw.component=='residual_mm')].to_dict('records'),'basin_lag':lag[lag.region!='TH'].to_dict('records'),'counts':{'figures':21,'basins':22,'gravity_months':237,'GW_months':225,'annual_well_trends':len(wt),'groundwater_checks':len(gw),'small_basin_flags':int(s[s.region!='TH'].provider_small_basin_caution.sum())},'note':'Primary CSR results differ from earlier unidentified export; uncertainty is conditional; discrepancies and product structure preclude causal pumping attribution.'}
(OUT/'logs/research_synthesis.json').write_text(pd.Series(summary).to_json(force_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary['counts'],indent=2))
