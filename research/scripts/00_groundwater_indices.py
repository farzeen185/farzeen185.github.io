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

