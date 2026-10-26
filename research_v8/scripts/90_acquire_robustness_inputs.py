"""Publisher-range subsets: daily CHIRPS and no-water-management ISIMIP TWS."""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
from pathlib import Path
import io,json,time,hashlib,collections,requests,gc,concurrent.futures
import numpy as np,pandas as pd,h5py,xarray as xr,geopandas as gpd
from shapely import contains_xy
from research_common import region_weights,weighted_series
R=Path(os.environ.get('TWSA_RESEARCH_ROOT',Path(__file__).resolve().parents[1]));O=R/'Thailand_Direct_WaterGAP_Analysis/robustness_extension';I=O/'inputs';I.mkdir(exist_ok=True)
class HTTPRange(io.RawIOBase):
 def __init__(self,url,size=None):
  self.url=url;self.pos=0;self.s=requests.Session();self.cache=collections.OrderedDict();self.received=0;self.prefetched={}
  if size is None:
   r=self.s.get(url,headers={'Range':'bytes=0-15'},timeout=45);r.raise_for_status();assert r.status_code==206;size=int(r.headers['Content-Range'].split('/')[-1])
  self.size=size
 def readable(self):return True
 def seekable(self):return True
 def tell(self):return self.pos
 def seek(self,n,whence=0):self.pos=n if whence==0 else self.pos+n if whence==1 else self.size+n;return self.pos
 def fetch(self,start,end):
  for attempt in range(4):
   try:
    r=self.s.get(self.url,headers={'Range':f'bytes={start}-{end}','Cache-Control':'no-cache'},timeout=55);r.raise_for_status();assert r.status_code==206 and len(r.content)==end-start+1,(r.status_code,len(r.content),start,end);self.received+=len(r.content);return r.content
   except Exception:
    if attempt==3:raise
    time.sleep(1+attempt)
 def read(self,n=-1):
  n=min(self.size-self.pos,n if n>=0 else self.size-self.pos)
  if n<=0:return b''
  if n>65536:
   b=self.prefetched.pop((self.pos,n),None)
   if b is None:b=self.fetch(self.pos,self.pos+n-1)
   self.pos+=n;return b
  b=[]
  while n:
   start=self.pos//65536*65536
   if start not in self.cache:
    self.cache[start]=self.fetch(start,min(start+65535,self.size-1))
    while len(self.cache)>128:self.cache.popitem(last=False)
   offset=self.pos-start;v=self.cache[start][offset:offset+n];b.append(v);self.pos+=len(v);n-=len(v)
  return b''.join(b)
 def readinto(self,b):v=self.read(len(b));b[:len(v)]=v;return len(v)

def daily_chirps():
 geo=gpd.read_file(R/'Thailand_Direct_WaterGAP_Analysis/inputs/basins.geojson');geoms=dict(zip(geo.region,geo.geometry));geoms={'TH':geo.geometry.union_all(),**geoms}
 provenance=[]
 for year in range(2003,2024):
  dest=I/f'CHIRPS_daily_basins_{year}.csv';indices=I/f'CHIRPS_annual_indices_{year}.csv'
  if dest.exists() and indices.exists():print('retained CHIRPS',year,flush=True);continue
  url=f'https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_daily/netcdf/p05/chirps-v2.0.{year}.days_p05.nc';started=time.time()
  with HTTPRange(url) as f:
   with h5py.File(f,'r') as h:
    lat=h['latitude'][:];lon=h['longitude'][:];yi=np.where((lat>=5.4)&(lat<=20.7))[0];xi=np.where((lon>=97.1)&(lon<=105.8))[0]
    dates=pd.date_range(f'{year}-01-01',f'{year}-12-31',freq='D');assert len(dates)==h['precip'].shape[0]
    dataset=h['precip'];ct,cy,cx=dataset.chunks;chunks=[]
    for ti in range(0,len(dates),ct):
     for yy in range(yi[0]//cy*cy,yi[-1]+1,cy):
      for xx in range(xi[0]//cx*cx,xi[-1]+1,cx):
       info=dataset.id.get_chunk_info_by_coord((ti,yy,xx))
       if info.size:chunks.append((info.byte_offset,info.size))
    def chunkget(info):
     offset,length=info;return info,f.fetch(offset,offset+length-1)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
     for info,blob in pool.map(chunkget,chunks):f.prefetched[info]=blob
    arr=dataset[:,yi[0]:yi[-1]+1,xi[0]:xi[-1]+1];arr[arr<0]=np.nan
    assert arr.shape==(len(dates),len(yi),len(xi))
    X,Y=np.meshgrid(lon[xi],lat[yi]);weights={code:contains_xy(g,X,Y)*np.cos(np.deg2rad(Y)) for code,g in geoms.items()}
    flat=arr.reshape(len(dates),-1);valid=np.isfinite(flat);clean=np.nan_to_num(flat,nan=0);rows=[];annual=[]
    # Area-mean local daily Gini complements the Gini of basin-mean daily rain.
    local_gini=np.full(flat.shape[1],np.nan);local_cdd=np.full(flat.shape[1],np.nan)
    for first in range(0,flat.shape[1],3000):
     block=flat[:,first:first+3000];ok=np.isfinite(block).all(axis=0);ordered=np.sort(np.nan_to_num(block,nan=0),axis=0);den=ordered.sum(axis=0);numer=((2*np.arange(1,len(dates)+1)-len(dates)-1)[:,None]*ordered).sum(axis=0)
     local_gini[first:first+block.shape[1]]=np.divide(numer,len(dates)*den,out=np.full(len(den),np.nan),where=ok&(den>0))
     run=np.zeros(block.shape[1],int);longest=run.copy()
     for day in block:run=np.where(day<1,run+1,0);longest=np.maximum(longest,run)
     local_cdd[first:first+block.shape[1]]=np.where(ok,longest,np.nan)
    for code,weight in weights.items():
     ww=weight.ravel();den=valid@ww;p=np.divide(clean@ww,den,out=np.full(len(dates),np.nan),where=den>0);coverage=den/ww.sum();p[coverage<.95]=np.nan
     rows.extend({'date':dt.strftime('%Y-%m-%d'),'region':code,'precip_mm_day':value,'area_coverage':cov} for dt,value,cov in zip(dates,p,coverage))
     good=np.isfinite(p);ordered=np.sort(p[good]);n=len(ordered);gini=np.sum((2*np.arange(1,n+1)-n-1)*ordered)/(n*ordered.sum()) if n and ordered.sum()>0 else np.nan
     run=longest=0
     for v in p:run=run+1 if np.isfinite(v) and v<1 else 0;longest=max(longest,run)
     avg=lambda vals:float(np.nansum(vals*ww)/np.sum(ww[np.isfinite(vals)])) if np.sum(ww[np.isfinite(vals)]) else np.nan
     annual.append({'year':year,'region':code,'valid_days':int(good.sum()),'calendar_days':len(dates),'P_annual_mm':float(np.sum(p)) if good.all() else np.nan,'basin_mean_daily_Gini':gini if good.all() else np.nan,'area_mean_local_daily_Gini':avg(local_gini),'basin_mean_CDD_days':longest if good.all() else np.nan,'area_mean_local_CDD_days':avg(local_cdd),'rain_days_ge1mm':int(np.sum(p>=1)) if good.all() else np.nan})
  pd.DataFrame(rows).to_csv(dest,index=False);pd.DataFrame(annual).to_csv(indices,index=False)
  rec={'year':year,'url':url,'subset':'97.1–105.8E,5.4–20.7N; native 0.05-degree pixel centres','bytes_transferred':f.received,'daily_csv_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'seconds':round(time.time()-started,1)}
  (I/f'CHIRPS_{year}_provenance.json').write_text(json.dumps(rec,indent=2),encoding='utf-8');print('CHIRPS',year,rec['bytes_transferred'],rec['seconds'],flush=True);del arr,flat,clean,valid;gc.collect()

def baselines():
 inventory=json.loads((O/'ISIMIP_tws_inventory.json').read_text());base=R/'Thailand_Research_v5/netcdf/CSR_storage_components.nc'
 with xr.open_dataset(base,engine='h5netcdf') as h:lat=h.lat.values;lon=h.lon.values
 regs=region_weights(lat,lon)
 for model in ['lpjml5-7-10-fire','watergap2-2e','miroc-integ-land']:
  dest=I/(model+'_no_water_management_Thailand.nc')
  if dest.exists():
   try:
    with xr.open_dataset(dest,engine='h5netcdf') as check:assert check.tws.shape[0]==240 and np.isfinite(check.tws.values).any()
    print('retained baseline',model,flush=True);continue
   except Exception:dest.rename(dest.with_suffix('.incomplete'))
  f=next(f for f in inventory if f['name']==model+'_20crv3-era5_obsclim_histsoc_nowatermgt_tws_global_monthly_1901_2021.nc')
  with HTTPRange(f['file_url'],f['size']) as handle:
   with xr.open_dataset(handle,engine='h5netcdf') as ds:
    print(model,'metadata',ds.tws.attrs,ds.time.encoding.get('calendar'),flush=True)
    ti=np.where((ds.time.dt.year.values>=2002)&(ds.time.dt.year.values<=2021))[0]
    with h5py.File(handle,'r') as raw:
     chunks=[]
     for index in ti:
      info=raw['tws'].id.get_chunk_info_by_coord((int(index),0,0))
      if info.size:chunks.append((info.byte_offset,info.size))
     def chunkget(info):
      offset,length=info;return info,handle.fetch(offset,offset+length-1)
     with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
      for info,blob in pool.map(chunkget,chunks):handle.prefetched[info]=blob
    sub=ds.sel(time=slice('2002-01-01','2021-12-31')).sortby('lat').sel(lat=slice(4,22),lon=slice(96,107)).load()
    sub=sub.assign_coords(time=pd.to_datetime([f'{int(y):04d}-{int(m):02d}-01' for y,m in zip(sub.time.dt.year.values,sub.time.dt.month.values)]))
    sub.attrs.update(source_url=f['file_url'],scenario='obsclim_histsoc_nowatermgt; historical land use/CO2 retained where represented; not a pristine-world counterfactual')
    sanitize=lambda attrs:{str(k):(v.encode('utf-8',errors='replace').decode('utf-8') if isinstance(v,str) else v) for k,v in attrs.items()}
    sub.attrs=sanitize(sub.attrs)
    for var in sub.variables:sub[var].attrs=sanitize(sub[var].attrs)
    tmp=dest.with_suffix('.partial.nc');sub.to_netcdf(tmp,engine='h5netcdf',encoding={'tws':{'zlib':True,'complevel':3}});tmp.replace(dest)
  (I/(model+'_provenance.json')).write_text(json.dumps({'publisher_file':f,'bytes_transferred':handle.received,'subset_sha256':hashlib.sha256(dest.read_bytes()).hexdigest()},indent=2),encoding='utf-8');print('baseline acquired',model,handle.received,flush=True)
if __name__=='__main__':
 import sys
 if '--baselines' in sys.argv:baselines()
 else:daily_chirps()
