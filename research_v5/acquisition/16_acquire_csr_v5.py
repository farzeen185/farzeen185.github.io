"""Acquire documented CSR RL06.3 and preserve compact Thai-buffer inputs."""
from pathlib import Path
import json,hashlib,time
import requests,h5py,xarray as xr,pandas as pd,numpy as np
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'shared_data/CSR_RL0603';OUT.mkdir(exist_ok=True)
BASE='https://download.csr.utexas.edu/outgoing/grace/RL0603_mascons/'
files=['CSR_GRACE_GRACE-FO_RL0603_Mascons_all-corrections.nc','CSR_GRACE_GRACE-FO_RL0603_mascons_mapping_file.nc','CSR_GRACE_GRACE-FO_RL06_Mascons_v02_LandMask.nc']
records=[]
for name in files:
    p=OUT/name
    if not p.exists():
        partial=p.with_suffix('.part');r=requests.get(BASE+name,stream=True,timeout=(30,180));r.raise_for_status()
        with partial.open('wb') as f:
            for block in r.iter_content(4*1024**2):f.write(block)
        partial.rename(p)
    digest=hashlib.sha256(p.read_bytes()).hexdigest();print(name,p.stat().st_size,digest,flush=True)
    with xr.open_dataset(p) as d:
        print(d,flush=True)
        # CSR uses uppercase Units, which CF decoders do not recognize automatically.
        if 'time' in d.coords and not np.issubdtype(d.time.dtype,np.datetime64):
            units=d.time.attrs.get('units',d.time.attrs.get('Units',''))
            assert units=='days since 2002-01-01T00:00:00Z',units
            raw=d.time.values.copy();d=d.assign_coords(time=pd.Timestamp('2002-01-01')+pd.to_timedelta(raw,unit='D'))
            if 'time_bounds' in d:d['time_bounds']=(d.time_bounds.dims,(np.datetime64('2002-01-01')+pd.to_timedelta(d.time_bounds.values.ravel(),unit='D').to_numpy()).reshape(d.time_bounds.shape))
        rename={n:('lat' if n.lower()=='latitude' else 'lon') for n in d.coords if n.lower() in ['latitude','longitude']};d=d.rename(rename)
        if 'lon' in d.coords:d=d.assign_coords(lon=((d.lon+180)%360)-180).sortby('lon')
        subset=d.sel(lat=slice(2,24) if d.lat[0]<d.lat[-1] else slice(24,2),lon=slice(94,110)).load()
        if 'time' in subset.coords:
            subset=subset.sel(time=slice('2002-01-01','2024-09-30'))
            centers=pd.DatetimeIndex(subset.time.values);months=list(centers.to_period('M').to_timestamp())
            # Special GRACE solutions can have their midpoint in the preceding month.
            # Preserve both solutions: the second October2011/April2015 entry is
            # the nominal November2011/May2015 field, rather than a duplicate average.
            fixes={pd.Timestamp('2011-10-31 12:00:00'):pd.Timestamp('2011-11-01'),pd.Timestamp('2015-04-27'):pd.Timestamp('2015-05-01')}
            months=pd.DatetimeIndex([fixes.get(c,m) for c,m in zip(centers,months)])
            assert len(months)>200 and not months.duplicated().any();subset=subset.assign_coords(time=months)
            pd.DataFrame({'source_midpoint':centers,'nominal_month':months,'special_month_adjusted':centers.to_period('M')!=months.to_period('M')}).to_csv(OUT/'CSR_month_assignment_audit.csv',index=False)
        dest=OUT/(name.replace('.nc','_Thailand.nc'))
        subset.attrs.update(download_url=BASE+name,source_sha256=digest,accessed='2026-10-24',subset='94–110E;2–24N;through September2024; nominal GRACE month identities, two documented special-month assignments, no interpolation')
        subset.to_netcdf(dest)
        records.append({'source_url':BASE+name,'source_sha256':digest,'source_bytes':p.stat().st_size,'subset':dest.name,'subset_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'source_attrs':{k:str(v) for k,v in d.attrs.items()}})
    print('Subset retained',dest.name,flush=True)
(OUT/'provenance.json').write_text(json.dumps({'provider':'University of Texas at Austin Center for Space Research','release':'RL06.3','provider_documentation':'https://www2.csr.utexas.edu/grace/RL0603_mascons.html','data_citation':'Save, H. (2020). CSR GRACE and GRACE-FO RL06 Mascon Solutions v02. https://doi.org/10.15781/cgq9-nh24','records':records},indent=2),encoding='utf-8')
