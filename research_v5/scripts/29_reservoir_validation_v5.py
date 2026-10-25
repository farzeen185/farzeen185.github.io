"""Exploratory independent reservoir check; never a total-human validation."""
import h5py
from pathlib import Path
import json,zipfile,io,re
import pandas as pd,numpy as np,geopandas as gpd
from shapely.geometry import Point
from scipy.stats import theilslopes
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from research_common import ROOT,bh_fdr
O=ROOT/'Thailand_Research_v5';P=ROOT/'shared_data/reservoir_independent'
g=gpd.read_file(ROOT/'Thailand_Objective2/data/BASINS/MainBasin_ONWR_Law_WGS84.shp').to_crs(4326)
g['region']=g.MB_CODE.astype(str).str.split('-').str[0].str.zfill(2);g=g.dissolve(by='region',as_index=False,aggfunc='first')
area=pd.read_csv(O/'tables/native_mascon_support.csv',dtype={'region':str}).set_index('region').basin_area_km2
dates=pd.date_range('2002-04-01','2023-12-01',freq='MS');records=[];long=[]
compact=P/'MSEA_Thailand_monthly.csv';inventory=P/'MSEA_Thailand_inventory.csv'
if compact.exists() and inventory.exists():
    monthly=pd.read_csv(compact,dtype={'region':str,'id':str},parse_dates=['date']);inv=pd.read_csv(inventory,dtype={'region':str,'id':str})
else:
    z=zipfile.ZipFile(P/'MSEA-Res_database_v2.zip')
    for file in z.namelist():
        if not file.endswith('.shp'):continue
        tokens=Path(file).stem.split('_');rid,year,lon,lat=tokens[1:5];p=Point(float(lon),float(lat));hit=g[g.geometry.covers(p)]
        if len(hit)!=1:continue
        code=hit.region.iloc[0];entries=[x for x in z.namelist() if '/Level1/' in x and Path(x).name.startswith('Level1_'+rid+'_'+year+'_')]
        if len(entries)!=1:continue
        name=Path(entries[0]).stem.split('_',3)[3];record={'id':rid,'commission_year':int(year),'name':name,'region':code,'lon':float(lon),'lat':float(lat)}
        for level in [1,2]:
            member=next(x for x in z.namelist() if f'/Level{level}/' in x and Path(x).name.startswith(f'Level{level}_{rid}_{year}_'))
            d=pd.read_csv(io.BytesIO(z.read(member)),parse_dates=['Date']);col='Tot_res_volume_km3' if level==1 else 'Storage_km3'
            s=d.set_index('Date')[col].sort_index().resample('MS').agg(['mean','count']).reindex(dates)
            if level==2:s.loc[s['count']<20,'mean']=np.nan
            long.extend({'date':date,'id':rid,'region':code,'level':level,'storage_km3':row['mean'],'source_records':row['count']} for date,row in s.iterrows())
        records.append(record)
    inv=pd.DataFrame(records);monthly=pd.DataFrame(long);inv.to_csv(inventory,index=False);monthly.to_csv(compact,index=False)
print('Thai reservoirs',len(inv),flush=True)
attrib=pd.read_csv(O/'tables/CSR_naturalized_attribution.csv',dtype={'region':str},parse_dates=['date']);rng=np.random.default_rng(29525)
rows=[];series=[]
def corr(a,b):
    ok=np.isfinite(a)&np.isfinite(b)
    return float(np.corrcoef(a[ok],b[ok])[0,1]) if ok.sum()>=24 and np.std(a[ok]) and np.std(b[ok]) else np.nan
def adjusted(v,idx,climate=None):
    x=np.asarray(v,float);t=(idx.year-2002)+(idx.month-1)/12
    X=np.column_stack([np.ones(len(idx)),t,pd.get_dummies(idx.month,drop_first=True,dtype=float)])
    if climate is not None:X=np.column_stack([X,climate])
    ok=np.isfinite(x)&np.isfinite(X).all(axis=1);r=np.full(len(x),np.nan)
    if ok.sum()>=24:r[ok]=x[ok]-X[ok]@np.linalg.lstsq(X[ok],x[ok],rcond=None)[0]
    return r
for code in ['TH']+sorted(g.region):
    # Fixed population: already operating before the anomaly reference, no entry/exit.
    chosen=inv[(inv.commission_year<2004)&((inv.region==code) if code!='TH' else True)]
    for level in [1,2]:
        d=monthly[(monthly.id.isin(chosen.id))&(monthly.level==level)]
        mat=d.pivot(index='date',columns='id',values='storage_km3').reindex(dates)
        # A month is used only when every selected reservoir is represented.
        total=mat.sum(axis=1,min_count=len(chosen)) if len(chosen) else pd.Series(np.nan,index=dates)
        mm=total*1e6/area.loc[code];ref=mm[(mm.index.year>=2004)&(mm.index.year<=2009)].mean();anom=mm-ref
        for date,val in anom.items():series.append({'date':date,'region':code,'level':level,'reservoir_count':len(chosen),'SWSA_reservoir_mm':val,'observed_reservoirs':int(mat.loc[date].notna().sum())})
        for var in ['TWSA','GWSA']:
            a=attrib[(attrib.region==code)&(attrib.variable==var)].set_index('date').reindex(dates)
            for component in ['observed_mm','residual_mm','modeled_human_mm','discrepancy_mm']:
                x=a[component].to_numpy();y=anom.to_numpy();ok=np.isfinite(x)&np.isfinite(y);n=int(ok.sum());raw=corr(x,y)
                matched_x=np.where(ok,x,np.nan);matched_y=np.where(ok,y,np.nan)
                xx=adjusted(matched_x,dates);yy=adjusted(matched_y,dates);adj=corr(xx,yy);xp=adjusted(matched_x,dates,a.climate_mm.to_numpy());yp=adjusted(matched_y,dates,a.climate_mm.to_numpy());partial=corr(xp,yp)
                boot=[]
                if n>=24:
                    good=np.where(ok)[0];years=dates[good].year;uy=np.unique(years)
                    for _ in range(499):
                        picks=rng.choice(uy,len(uy),replace=True);ii=np.concatenate([good[years==yr] for yr in picks]);boot.append(corr(xx[ii],yy[ii]))
                boot=np.array(boot);boot=boot[np.isfinite(boot)]
                rows.append({'region':code,'variable':var,'component':component,'level':level,'reservoir_count':len(chosen),'n_months':n,'reservoir_reference_months':int(mm[(mm.index.year>=2004)&(mm.index.year<=2009)].notna().sum()),'r_raw':raw,'r_month_trend_removed':adj,'r_climate_month_trend_partial':partial,'adjusted_r_year_cluster_boot_ci_low':np.quantile(boot,.025) if len(boot) else np.nan,'adjusted_r_year_cluster_boot_ci_high':np.quantile(boot,.975) if len(boot) else np.nan,'bootstrap_replicates':499 if n>=24 else 0,'evidence_type':'Component consistency; no naturalized reservoir counterfactual; not causal human validation'})
        print('Reservoir evidence',code,level,len(chosen),int(anom.notna().sum()),flush=True)
result=pd.DataFrame(rows);result.to_csv(O/'tables/independent_reservoir_evidence.csv',index=False);ts=pd.DataFrame(series);ts.to_csv(O/'tables/independent_reservoir_timeseries.csv',index=False)
plt.rcParams.update({'font.size':14,'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(1,2,figsize=(11,4.5))
for ax,code,title in zip(axes,['TH','06'],['Thailand','Ping basin']):
    ss=ts[(ts.region==code)&(ts.level==2)].set_index('date').SWSA_reservoir_mm;a=attrib[(attrib.region==code)&(attrib.variable=='TWSA')].set_index('date')
    for s,label,color in [(a.residual_mm,'TWS residual','#173c50'),(ss,'Reservoir anomaly','#b66a3c')]:ax.plot(s.index,s,color=color,label=label,lw=1.1)
    ax.set_title(title);ax.set_ylabel('mm basin-equivalent');ax.tick_params(axis='x',rotation=35)
axes[0].legend(fontsize=11);fig.tight_layout()
for ext in ['png','pdf']:fig.savefig(O/f'figures/22_independent_reservoir_check.{ext}',dpi=240,bbox_inches='tight')
nat=result[(result.region=='TH')&(result.component=='residual_mm')].replace({np.nan:None}).to_dict('records')
qa={'passed':True,'exploratory_extension':'Added after groundwater sensitivity results, at user request; no model retuning','inventory_reservoirs':len(inv),'fixed_pre2004_reservoirs':int((inv.commission_year<2004).sum()),'no_new_gap_filling':True,'Level1':'Scene-based outlier-screened observations; gaps retained','Level2':'Provider spline-interpolated and smoothed daily product, monthly means require20days; not independent daily observations','missing_months_not_zero':True,'same_reservoir_population_each_month':True,'national_residual_checks':nat,'interpretation':'Independent Landsat/hypsometry measurement modality, but water volume responds to climate and operations; comparison cannot isolate causal human storage. Reservoirs do not directly validate GWSA.'}
(O/'logs/reservoir_evidence_qa.json').write_text(json.dumps(qa,indent=2),encoding='utf-8');print(json.dumps(qa,indent=2))
