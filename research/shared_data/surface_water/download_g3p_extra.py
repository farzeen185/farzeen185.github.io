from pathlib import Path
import requests,json,hashlib
from remotezip import RemoteZip
import xarray as xr
import numpy as np
root=Path(__file__).parent
url='https://isdc-data.gfz.de/grace/GravIS/G3P/v1.12/G3P_v1.12.zip'
for compartment in ['RZSM','GWSA','TWS']:
    with RemoteZip(url) as z:
        name=next(n for n in z.namelist() if '/'+compartment+'/' in n and n.endswith('.nc'))
        dst=root/Path(name).name
        if not dst.exists():
            with z.open(name) as source,dst.open('wb') as target:
                while data:=source.read(1024*1024):target.write(data)
    with xr.open_dataset(dst) as ds:
        lat=next(n for n in ds.coords if 'lat' in n.lower());lon=next(n for n in ds.coords if 'lon' in n.lower())
        if compartment=='TWS':
            clipped=ds.sel({lat:slice(24,2),lon:slice(94,109)})
            subset=xr.Dataset(coords={n:clipped[n].load() for n in clipped.coords},attrs=ds.attrs)
            for n in ['tws','std_tws','std_tws_grid']:
                values=np.stack([clipped[n].isel(time=i).values for i in range(clipped.sizes['time'])])
                subset[n]=xr.DataArray(values,dims=clipped[n].dims,attrs=clipped[n].attrs)
        else:
            subset=ds.sel({lat:slice(24,2),lon:slice(94,109)}).load()
        out=root/f'G3P_v1.12_{compartment}_Thailand_buffer_monthly_200204_202309.nc'
        subset.to_netcdf(out)
        meta={'source_url':url,'archive_member':name,'doi':'10.5880/G3P.2024.001','subset_bbox':[94,2,109,24],'subset_file':str(out),'attributes':dict(ds.attrs),'variables':{n:dict(ds[n].attrs) for n in ds.variables}}
        (root/f'G3P_{compartment}_provenance.json').write_text(json.dumps(meta,indent=2,default=str),encoding='utf-8')
        print(compartment,subset,flush=True)
