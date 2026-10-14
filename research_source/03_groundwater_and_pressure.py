"""Independent observational pattern checks and human-pressure associations.
Annual wells stay annual; no groundwater head-to-storage coefficient is invented.
"""
import json,warnings
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.windows import from_bounds
from shapely.geometry import box
from pyproj import Geod
from scipy.stats import theilslopes,spearmanr
from research_common import ROOT,OBJ1,OBJ2,output

OUT=ROOT/'Thailand_Objective2/analysis_v3';GROW=ROOT/'shared_data/groundwater/GROW';geod=Geod(ellps='WGS84')
geo=gpd.read_file(ROOT/'Thailand_Objective2/data/BASINS/MainBasin_ONWR_Law_WGS84.shp').to_crs(4326)
# Six island features use codes such as 10-is; retain them in their parent basin.
geo['region']=geo.MB_CODE.astype(str).str.split('-').str[0].str.zfill(2)
geo=geo.dissolve(by='region',as_index=False,aggfunc='first')
d=pd.read_csv(GROW/'GROW_Thailand_observations.csv',parse_dates=['date']);meta=pd.read_csv(GROW/'GROW_Thailand_attributes.csv')
wellmeta=d.groupby('well_id').agg(latitude=('latitude','first'),longitude=('longitude','first'),interval=('interval','first'),n=('date','size')).reset_index()
points=gpd.GeoDataFrame(wellmeta,geometry=gpd.points_from_xy(wellmeta.longitude,wellmeta.latitude),crs=4326)
joined=gpd.sjoin(points,geo[['region','MBASIN_E','geometry']],how='left',predicate='within')
if joined.well_id.duplicated().any():raise ValueError('Ambiguous well-to-basin assignment')
assignment=joined.drop(columns=['geometry','index_right']);assignment.to_csv(output(OUT,'tables','groundwater_well_basin_assignment.csv'),index=False)
d=d.merge(assignment[['well_id','region']],on='well_id',how='left');d['head_m']=-d.depth_to_water_m
coords=d.latitude.round(5).astype(str)+'_'+d.longitude.round(5).astype(str);d['station_group']=coords
# Full observed-series normalization is used only for descriptive well indices;
# it is never a feature for climate-model fitting or a predictive accuracy claim.
d['head_z']=d.groupby('well_id').head_m.transform(lambda v:(v-v.mean())/v.std() if v.std()>0 else np.nan)
outlier=d.outliers_change_points.astype(str).str.lower().isin(['true','1']);plateau=pd.to_numeric(d.plateaus,errors='coerce').fillna(0)>0
d['source_flagged']=outlier|plateau
d.to_csv(output(OUT,'tables','groundwater_signed_anomalies.csv'),index=False)
indices=[]
for quality in ['retained_flags','exclude_flagged_sensitivity','fixed_2013_2022_panel']:
    v=d[d.region.notna()&d.head_z.notna()]
    if quality=='exclude_flagged_sensitivity':v=v[~v.source_flagged]
    if quality=='fixed_2013_2022_panel':
        eligible=v[(v.interval=='YS')&(v.date.dt.year.between(2013,2022))].groupby('well_id').date.nunique()
        fixed=set(eligible[eligible>=8].index)
        v=v[(v.interval=='MS')|v.well_id.isin(fixed)]
    # Equal weight per coordinate station; co-located wells cannot dominate a basin index.
    station=v.groupby(['region','interval','date','station_group']).head_z.median().reset_index()
    regional=station.groupby(['region','interval','date']).head_z.agg(['mean','count']).reset_index().rename(columns={'mean':'well_head_z','count':'n_station_groups'})
    national=station.groupby(['interval','date']).head_z.agg(['mean','count']).reset_index().rename(columns={'mean':'well_head_z','count':'n_station_groups'});national['region']='TH'
    regional=pd.concat([regional,national],ignore_index=True);regional['quality']=quality;indices.append(regional)
index=pd.concat(indices,ignore_index=True);index.to_csv(output(OUT,'tables','basin_groundwater_observation_indices.csv'),index=False)
print('Actual groundwater observations assigned and aggregated; flagged observations retained with separate sensitivity.',flush=True)

# Area-intersection weights for static FAO irrigation pressure, including coastal edges.
pressure=[]
aei=ROOT/'shared_data/human_pressure/GMIA_v5_area_equipped_pct_total_area_Thailand_buffer.tif'
gw=ROOT/'shared_data/human_pressure/GMIA_v5_groundwater_irrigation_pct_equipped_area_Thailand_buffer.tif'
with rasterio.open(aei) as ra,rasterio.open(gw) as rg:
    for _,b in geo.iterrows():
        raw=from_bounds(*b.geometry.bounds,transform=ra.transform)
        left,top=int(np.floor(raw.col_off)),int(np.floor(raw.row_off));right,bottom=int(np.ceil(raw.col_off+raw.width)),int(np.ceil(raw.row_off+raw.height))
        window=rasterio.windows.Window(left,top,right-left,bottom-top).intersection(rasterio.windows.Window(0,0,ra.width,ra.height))
        a=ra.read(1,window=window,masked=True).filled(np.nan);g=rg.read(1,window=window,masked=True).filled(np.nan);transform=ra.window_transform(window)
        numerator=gnumerator=denominator=gdenominator=0.
        for row in range(a.shape[0]):
            for col in range(a.shape[1]):
                x,y=transform*(col,row);cell=box(x,y+transform.e,x+transform.a,y)
                if not cell.intersects(b.geometry):continue
                overlap=cell.intersection(b.geometry)
                if overlap.is_empty or overlap.area<=0:continue
                area=abs(geod.geometry_area_perimeter(overlap)[0])
                if np.isfinite(a[row,col]):numerator+=area*a[row,col];denominator+=area
                if np.isfinite(a[row,col]) and np.isfinite(g[row,col]):gnumerator+=area*a[row,col]*g[row,col]/100;gdenominator+=area
        pressure.append({'region':b.region,'region_name':b.MBASIN_E,'irrigation_equipped_pct':numerator/denominator if denominator else np.nan,'groundwater_equipped_pct_total_area':gnumerator/gdenominator if gdenominator else np.nan,'irrigation_valid_area_fraction':denominator/abs(geod.geometry_area_perimeter(b.geometry)[0]),'reference':'FAO GMIA v5; Thailand equipped-area statistics2007; groundwater share inferred from1994–2006rice/provincial assumptions','interpretation':'static spatial pressure proxy, not measured abstraction or temporal causal evidence'})
pd.DataFrame(pressure).to_csv(output(OUT,'tables','basin_irrigation_pressure.csv'),index=False)
print('Irrigation pressure aggregated by exact geographic-cell/basin intersections.',flush=True)

# The remaining evidence calculations depend on completed climate output.
climate_path=OBJ2/'tables/basin_climate_residual_timeseries.csv'
if not climate_path.exists():
    output(OUT,'logs','groundwater_validation_status.json').write_text(json.dumps({'status':'observations_and_pressure_prepared; climate_output_pending','wells':int(d.well_id.nunique()),'observations':len(d)},indent=2),encoding='utf-8')
    print('Climate output pending: rerun after02_climate_models.py to complete correlations.');raise SystemExit(0)
storage=pd.read_csv(OBJ1/'tables/basin_storage_timeseries.csv',dtype={'region':str},parse_dates=['date'])
climate=pd.read_csv(climate_path,dtype={'region':str},parse_dates=['date'])
rng=np.random.default_rng(731);correlations=[];wellchecks=[]
def annual_series(s):
    s=s.dropna()
    if s.empty:return pd.Series(dtype=float)
    a=s.resample('YS').agg(['mean','count']);a.loc[a['count']<8,'mean']=np.nan
    # Never compare a full annual groundwater aggregate with a partial endpoint year.
    if s.index.min().month>1:a.loc[a.index.year==s.index.min().year,'mean']=np.nan
    if s.index.max().month<12:a.loc[a.index.year==s.index.max().year,'mean']=np.nan
    return a['mean']
def corr(a,b):
    z=pd.concat([a.rename('well'),b.rename('storage')],axis=1,sort=True).dropna();n=len(z)
    if n<6 or not (z.std()>0).all():return {'n':n,'r':np.nan,'spearman_r':np.nan,'status':'insufficient temporal pairs'}
    values=z.values;rep=[]
    for _ in range(300):
        starts=rng.integers(0,n,int(np.ceil(n/2)));ix=((starts[:,None]+np.arange(2))%n).ravel()[:n];v=values[ix]
        if np.std(v[:,0])>0 and np.std(v[:,1])>0:rep.append(np.corrcoef(v[:,0],v[:,1])[0,1])
    lo,hi=np.nanpercentile(rep,[2.5,97.5])
    return {'n':n,'r':float(z.well.corr(z.storage)),'spearman_r':float(z.well.corr(z.storage,method='spearman')),'r_lo95':float(lo),'r_hi95':float(hi),'status':'exploratory observed-pattern agreement','note':'bootstrap on observed pairs; irregular sampling and mixed aquifers limit inference'}
for code in ['TH']+geo.region.tolist():
    for variable in ['TWSA','GWSA']:
        original=storage[storage.region==code].set_index('date')[variable]
        c=climate[(climate.region==code)&(climate.variable==variable)].set_index('date')
        for component,signal in [('observed_storage',original),('unexplained_residual',c.unexplained_residual_mm if not c.empty else pd.Series(dtype=float))]:
            for interval in ['YS','MS']:
                for quality in ['retained_flags','exclude_flagged_sensitivity','fixed_2013_2022_panel']:
                    obs=index[(index.region==code)&(index.interval==interval)&(index.quality==quality)].set_index('date').well_head_z
                    target=annual_series(signal) if interval=='YS' else signal
                    if interval=='MS' and not signal.empty:
                        # Descriptive monthly anomaly agreement: remove each calendar-month mean.
                        target=signal-signal.groupby(signal.index.month).transform('mean')
                        obs=obs-obs.groupby(obs.index.month).transform('mean') if not obs.empty else obs
                    for scope in ['all_overlap','post2015']:
                        a,b=(obs,target) if scope=='all_overlap' else (obs.loc['2016':],target.loc['2016':])
                        correlations.append({'region':code,'variable':variable,'component':component,'interval':interval,'quality':quality,'scope':scope,**corr(a,b)})
    for well,g in d[(d.region==code)&(d.interval=='YS')].groupby('well_id'):
        for variable in ['TWSA','GWSA']:
            target=annual_series(storage[storage.region==code].set_index('date')[variable]);s=g.set_index('date').head_m
            z=pd.concat([s.rename('head'),target.rename('storage')],axis=1,sort=True).dropna()
            if len(z)>=6:
                year=z.index.year.to_numpy();hs=float(theilslopes(z['head'],year).slope);ss=float(theilslopes(z['storage'],year).slope)
                wellchecks.append({'well_id':well,'region':code,'variable':variable,'n_years':len(z),'head_Sen_m_year':hs,'storage_Sen_mm_year':ss,'trend_direction_agrees':bool(np.sign(hs)==np.sign(ss)),'head_storage_r':float(z['head'].corr(z['storage'])),'note':'No storage coefficient assumed; agreement is directional only'})
pd.DataFrame(correlations).to_csv(output(OUT,'tables','groundwater_storage_residual_agreement.csv'),index=False)
pd.DataFrame(wellchecks).to_csv(output(OUT,'tables','well_storage_trend_direction.csv'),index=False)
trends=pd.read_csv(OBJ2/'tables/climate_residual_Sen_MannKendall.csv',dtype={'region':str});press=pd.DataFrame(pressure);association=[]
for variable in ['TWSA','GWSA']:
    z=trends[(trends.variable==variable)&(trends.component=='unexplained_residual')&(trends.region!='TH')].merge(press,on='region')
    for predictor in ['irrigation_equipped_pct','groundwater_equipped_pct_total_area']:
        v=z[['sen_slope_mm_year',predictor]].dropna();s=spearmanr(v.sen_slope_mm_year,v[predictor]) if len(v)>=6 else None
        association.append({'variable':variable,'pressure_proxy':predictor,'n_basins':len(v),'spearman_r':float(s.statistic) if s else np.nan,'nominal_p':float(s.pvalue) if s else np.nan,'interpretation':'exploratory spatial association; basins not independent GRACE samples; static/inferred irrigation is not pumping attribution'})
pd.DataFrame(association).to_csv(output(OUT,'tables','residual_irrigation_spatial_association.csv'),index=False)
status={'status':'executed','wells':int(d.well_id.nunique()),'observations':len(d),'annual_wells':int(wellmeta.interval.eq('YS').sum()),'monthly_wells':int(wellmeta.interval.eq('MS').sum()),'outside_basin_wells':int(assignment.region.isna().sum()),'annual_typical_source_readings':2,'annual_endpoint_policy':'exclude incomplete endpoint calendar years;minimum8GRACEobservations','human_attribution':'candidatehuman/unexplainedresidual; well/pressure associations support consistency tests but do not establish causal pumping quantities','aquifer_metadata':'not provided inGROWThai metadata; mixedaquifer limitation','monthly_normalization':'descriptive contemporaneous deseasonalization, not fitted model features','license':'GROWpackageCCBYNCSA4.0;Thai sourceCCBY4.0'}
output(OUT,'logs','groundwater_validation_status.json').write_text(json.dumps(status,indent=2),encoding='utf-8');print(json.dumps(status,indent=2),flush=True)
