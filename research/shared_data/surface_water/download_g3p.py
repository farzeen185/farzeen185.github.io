from pathlib import Path
import requests,json,hashlib,time
from remotezip import RemoteZip
import xarray as xr

root=Path(__file__).parent
url='https://isdc-data.gfz.de/grace/GravIS/G3P/v1.12/G3P_v1.12.zip'
readme=requests.get(url.replace('.zip','_readme.txt'),timeout=60)
(root/'G3P_v1.12_readme.txt').write_text(readme.text,encoding='utf-8')
with RemoteZip(url) as z:
    name=next(n for n in z.namelist() if '/SWS/' in n and n.endswith('.nc'))
    dst=root/Path(name).name
    if not dst.exists():
        with z.open(name) as source,dst.open('wb') as target:
            while data:=source.read(1024*1024):target.write(data)
        print('Downloaded',dst.stat().st_size,flush=True)
with xr.open_dataset(dst) as ds:
    print(ds,flush=True)
    print(ds.attrs,flush=True)
    for n in ds.variables:print(n,ds[n].attrs,flush=True)
    lat=next(n for n in ds.coords if 'lat' in n.lower())
    lon=next(n for n in ds.coords if 'lon' in n.lower())
    subset=ds.sel({lat:slice(24,2),lon:slice(94,109)}).load()
    out=root/'G3P_v1.12_SWS_Thailand_buffer_monthly_200204_202309.nc'
    subset.to_netcdf(out)
    provenance={'source_url':url,'archive_member':name,'doi':'10.5880/G3P.2024.001','version':'1.12','subset_file':str(out),'subset_bbox':[94,2,109,24],'global_file_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'source_global_attributes':dict(ds.attrs),'variables':{n:dict(ds[n].attrs) for n in ds.variables},'limitations':['Model-derived GloFAS version 4.0 LISFLOOD surface water combines river, lake and artificial reservoir storage; not observation-based reservoir validation.','250 km Gaussian-filtered compartment must not be assumed spatially identical to another GRACE product.','Record ends September 2023; do not extrapolate subsequent surface water observations.']}
    (root/'G3P_surface_water_provenance.json').write_text(json.dumps(provenance,indent=2,default=str),encoding='utf-8')
    print('Saved',out,flush=True)
