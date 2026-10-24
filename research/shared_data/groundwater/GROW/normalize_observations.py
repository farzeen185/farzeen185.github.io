"""Normalize downloaded Thai observed groundwater aggregates, excluding filled values."""
from pathlib import Path
import json
import pandas as pd

ROOT=Path(__file__).resolve().parent
raw=pd.read_csv(ROOT/'GROW_Thailand_timeseries_raw.csv',dtype={'GROW_ID':str})
meta=pd.read_csv(ROOT/'GROW_Thailand_attributes.csv',dtype={'GROW_ID':str})
col='groundwater_depth_from_ground_elevation_m'
raw=raw[raw[col].notna()].copy()
out=pd.DataFrame({'well_id':raw.GROW_ID,'date':pd.to_datetime(raw.date).dt.strftime('%Y-%m-%d'),'depth_to_water_m':pd.to_numeric(raw[col]),'interval':raw.interval,'value_status':'observed aggregate; excludes interpolated filled columns','source':'GROW / IGRAC / Thai Ministry of Natural Resources and Environment'})
for flag in ['aggregated_from_n_values','outliers_change_points','plateaus']:
    out[flag]=raw[flag]
out=out.merge(meta[['GROW_ID','latitude','longitude','provider_ground_elevation_m_asl']].rename(columns={'GROW_ID':'well_id'}),on='well_id',validate='many_to_one')
out['groundwater_level_m_asl']=out.provider_ground_elevation_m_asl-out.depth_to_water_m
out['groundwater_head_anomaly_m']=-out.depth_to_water_m+out.groupby('well_id').depth_to_water_m.transform('mean')
out=out.sort_values(['well_id','date'])
out.to_csv(ROOT/'GROW_Thailand_observations.csv',index=False)
for interval,label in [('YS','annual'),('MS','monthly')]:
    out[out.interval==interval].to_csv(ROOT/f'GROW_Thailand_{label}_observations.csv',index=False)
out.groupby('well_id').agg(records=('date','count'),start=('date','min'),end=('date','max'),interval=('interval','first')).to_csv(ROOT/'GROW_Thailand_observed_coverage.csv')
summary=out.groupby('interval').agg(wells=('well_id','nunique'),observations=('date','count'),start=('date','min'),end=('date','max'))
summary.to_csv(ROOT/'observed_coverage_summary.csv')
provenance={'source':'https://zenodo.org/records/15149480','original_source':'IGRAC GGMN; Thai Ministry of Natural Resources and Environment','package_license_notice':'CC BY-NC-SA 4.0 per Zenodo package and Readme','Thai_metadata_license':'CC BY 4.0','reference_point':'depth below ground surface, positive downward','units':'m','head_anomaly_definition':'negative depth plus per-well mean observed depth; full observed period, not GRACE baseline','aggregation':'GROW annual YS and monthly MS aggregates; not original daily measurements','interpolation':'No filled groundwater values retained','warning':'Groundwater head fluctuations are not storage changes without aquifer storage coefficients; correlation does not prove human attribution','observations':len(out),'wells':out.well_id.nunique(),'summary':summary.reset_index().to_dict('records')}
provenance['outliers_change_points_flagged']=int(out.outliers_change_points.sum())
provenance['quality_control']='Provider flags retained; compare sensitivity including/excluding flagged outliers/change points and plateaus.'
(ROOT/'provenance.json').write_text(json.dumps(provenance,indent=2),encoding='utf8')
print(summary.to_string())
