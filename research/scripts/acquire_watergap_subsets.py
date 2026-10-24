"""Public HTTP-range extraction: keep Thai monthly cells, not global downloads."""
import concurrent.futures,json,time,hashlib,io,collections
from pathlib import Path
import requests,numpy as np,pandas as pd,xarray as xr
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'shared_data/WaterGAP'
class RangeReader(io.RawIOBase):
    def __init__(self,url,size):self.url=url;self.size=size;self.pos=0;self.cache=collections.OrderedDict();self.session=requests.Session();self.block=16*1024**2
    def readable(self):return True
    def seekable(self):return True
    def tell(self):return self.pos
    def seek(self,offset,whence=0):self.pos=offset if whence==0 else self.pos+offset if whence==1 else self.size+offset;return self.pos
    def read(self,n=-1):
        n=self.size-self.pos if n<0 else min(n,self.size-self.pos);parts=[]
        while n>0:
            index=self.pos//self.block;start=index*self.block
            if index not in self.cache:
                for attempt in range(4):
                    try:
                        r=self.session.get(self.url,headers={'Range':f'bytes={start}-{min(self.size-1,start+self.block-1)}'},timeout=120);r.raise_for_status();assert r.status_code==206
                        self.cache[index]=r.content;break
                    except (requests.RequestException,AssertionError):
                        if attempt==3:raise
                        time.sleep(2**attempt)
                while len(self.cache)>4:self.cache.popitem(last=False)
            data=self.cache[index];offset=self.pos-start;take=min(n,len(data)-offset)
            if take<=0:raise IOError('Incomplete publisher byte range')
            parts.append(data[offset:offset+take]);self.pos+=take;n-=take
        return b''.join(parts)
    def readinto(self,b):v=self.read(len(b));b[:len(v)]=v;return len(v)
def sanitize(attrs):
    return {str(k):str(v).encode('utf-8',errors='replace').decode('utf-8') if isinstance(v,str) else v for k,v in attrs.items()}
def acquire(job):
    scenario,file=job;variable=file['name'].split('_')[2]
    dest=OUT/f'WaterGAP22e_ERA5_{scenario}_{variable}_Thailand_1981_2023.nc'
    if dest.exists():return {'file':dest.name,'status':'retained verified previous subset'}
    start=time.time()
    with RangeReader(file['url'],file['bytes']) as handle:
        with xr.open_dataset(handle,engine='h5netcdf') as source:
            subset=source.sel(time=slice('1981-01-01','2023-12-30'),lat=slice(24,2),lon=slice(94,109)).load()
            calendar=source.time.encoding.get('calendar');originalattrs=sanitize(source.attrs)
            # Source uses synthetic CF 360-day labels for monthly records.
            # Preserve year/month identity; no daily values or interpolation are created.
            subset=subset.assign_coords(time=pd.to_datetime([f'{t.year:04d}-{t.month:02d}-01' for t in subset.time.values]))
            subset.attrs=sanitize(subset.attrs);subset.attrs.update(source_url=file['url'],source_monthly_calendar=str(calendar),monthly_label_policy='Original year/month labels mapped to month-start dates; no resampling/interpolation.',subset='94–109E;2–24N;1981–2023')
            for v in subset:subset[v].attrs=sanitize(subset[v].attrs)
            assert subset.time.size==516 and subset.lat.size==44 and subset.lon.size==30
            assert np.isfinite(subset[variable]).any()
            subset.to_netcdf(dest,encoding={v:{'zlib':True,'complevel':3} for v in subset.data_vars})
    with dest.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
    record={'scenario':scenario,'variable':variable,'source':file,'subset_file':str(dest),'subset_sha256':sha,'source_attrs':originalattrs,'source_calendar':calendar,'elapsed_seconds':round(time.time()-start,1),'data_cells_per_month':44*30,'months':516}
    (OUT/(dest.stem+'_provenance.json')).write_text(json.dumps(record,indent=2,default=str),encoding='utf-8')
    return record
if __name__=='__main__':
    inventory=json.loads((OUT/'publisher_inventory.json').read_text(encoding='utf-8'));jobs=[]
    required={'natural':['tws','groundwstor','soilmoist','canopystor','swe','precmon','potevap'],'human':['tws','groundwstor','anag']}
    for scenario,variables in required.items():
        for variable in variables:
            found=[f for f in inventory[scenario]['files'] if '_'+variable+'_' in f['name']];assert len(found)==1
            jobs.append((scenario,found[0]))
    results=[]
    with concurrent.futures.ProcessPoolExecutor(max_workers=3) as pool:
        for result in pool.map(acquire,jobs):
            results.append(result);print('Acquired:',result.get('variable',result.get('file')),result.get('scenario',''),result.get('elapsed_seconds','cached'),'seconds',flush=True)
    (OUT/'acquisition_status.json').write_text(json.dumps({'status':'complete','variables':results,'license':'CC BY 4.0 per publisher and native NetCDF attributes','public_transport':'Publisher-supported HTTP byte ranges; no authentication bypass'},indent=2,default=str),encoding='utf-8')
