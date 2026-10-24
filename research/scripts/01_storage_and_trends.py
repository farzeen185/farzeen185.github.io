"""Objective 1: full compartment balance, basin/time/grid Sen and MK analyses.
New products are isolated under analysis_v3; existing Objective 1 is preserved.
"""
import json,warnings
import numpy as np
import pandas as pd
import xarray as xr
import rasterio
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from research_common import ROOT,OBJ1,output,region_weights,weighted_series,trend_statistics,bh_fdr

dates=pd.date_range('2002-04-01','2024-09-01',freq='MS');core=ROOT/'Thailand_Objective2/data'
with xr.open_dataset(core/'GRACE_TWSA_Monthly_2002_2024.nc') as d:
    if d.twsa.attrs.get('units')!='cm':raise ValueError('GRACE cm source required')
    grace=d.twsa.sortby('lat',ascending=False).sortby('lon').reindex(time=dates).load()*10
grace.attrs={'units':'mm','conversion':'source cm × 10','nominal_grid':'0.25 degree sampling; effective GRACE resolution much coarser'}
def g3p(name,var):
    p=ROOT/'shared_data/surface_water'/f'G3P_v1.12_{name}_Thailand_buffer_monthly_200204_202309.nc'
    with xr.open_dataset(p) as d:
        a=d[var].load();attrs=a.attrs
    if attrs.get('units')!='mm':raise ValueError(f'{name}: expected mm')
    a=a.assign_coords(time=pd.DatetimeIndex(a.time.values).to_period('M').to_timestamp()).sortby('lat').sortby('lon')
    # Aligned 0.5deg parent cells divide exactly into four0.25deg cells.
    # Replication preserves parent state/area integrals and avoids linear interpolation
    # eroding coastal coverage when one neighboring ocean cell is missing.
    a=a.interp(lat=grace.lat,lon=grace.lon,method='nearest').reindex(time=dates)
    a.attrs={**attrs,'regrid':'aligned coarse-cell replication; no extra spatial information; ocean/missing values preserved'}
    return a
sws=g3p('SWS','sws');rzsm=g3p('RZSM','rzsm');nativegw=g3p('GWSA','gwsa')
parts={}
compact=ROOT/'shared_data/GLDAS/GLDAS_NOAH_monthly_storage_200204_202409_Thailand.nc'
if compact.exists():
    with xr.open_dataset(compact) as d:
        d=d.sortby('lat',ascending=False).sortby('lon').reindex(time=dates)
        for name in ['SoilMoi0_10cm_inst','SoilMoi10_40cm_inst','SoilMoi40_100cm_inst','SoilMoi100_200cm_inst','CanopInt_inst','SWE_inst','NOAH_TWS']:parts[name]=d[name].values
else:
    with rasterio.open(core/'GLDAS_NOAH/GLDAS_NOAH_Monthly_Storage_2002_2024_Thailand.tif') as r:
        if r.shape!=grace.shape[1:]:raise ValueError('GLDAS grid mismatch')
        for b,label in enumerate(r.descriptions,1):
            yy,mm,name=label.split('_',2);date=pd.Timestamp(int(yy),int(mm),1)
            if name not in parts:parts[name]=np.full(grace.shape,np.nan)
            if date in dates:parts[name][dates.get_loc(date)]=r.read(b,masked=True).filled(np.nan)
def array(z):return xr.DataArray(z,dims=grace.dims,coords=grace.coords,attrs={'units':'mm','unit_evidence':'NASA GLDAS component kg m-2 equivalent mm; local export scale checked by sum identity'})
soil=array(sum(parts[n] for n in parts if n.startswith('SoilMoi')));canopy=array(parts['CanopInt_inst']);snow=array(parts['SWE_inst']);noah=array(parts['NOAH_TWS'])
err=float(np.nanmax(abs((soil+canopy+snow-noah).values)))
if err>.05:raise ValueError('GLDAS component balance failed')
joint=np.isfinite(grace)&np.isfinite(soil)&np.isfinite(canopy)&np.isfinite(snow)&np.isfinite(sws)
reference=(grace.time.dt.year>=2004)&(grace.time.dt.year<=2009)&joint
def rebase(a,ref=None):
    ref=reference if ref is None else ref
    z=a-a.where(ref).mean('time',skipna=True);z.attrs={**a.attrs,'units':'mm','reference':'2004–2009 valid reference months; common component mask for groundwater balance'};return z
tws=rebase(grace,(grace.time.dt.year>=2004)&(grace.time.dt.year<=2009)&np.isfinite(grace))
tws_balance=rebase(grace);sms=rebase(soil);cws=rebase(canopy);swe=rebase(snow);swa=rebase(sws)
gw=(tws_balance-sms-swa-cws-swe).where(joint);gw.attrs={'units':'mm','equation':'GWSA = TWSA_common_reference − SMSA − SWSA − canopy anomaly − snow anomaly','limitation':'G3P SWS filtered250km; GLDAS compartments/local GRACE filtering not fully matched. Model-derived compartment estimate, not direct groundwater observation.'}
filtered_reference=np.isfinite(grace)&np.isfinite(rzsm)&np.isfinite(sws)&np.isfinite(canopy)&np.isfinite(snow)
gwfiltered=(tws_balance-rebase(rzsm)-swa-cws-swe).where(filtered_reference);gwfiltered.attrs={**gw.attrs,'soil_source':'G3P filtered root-zone anomaly; fourlayers','purpose':'soil-compartment sensitivity; native filter does not necessarily match local GRACE'}
ng=rebase(nativegw);ng.attrs={**ng.attrs,'purpose':'alternative GRACE/compartment product, not independent observation; native definition omits canopy'}
ds=xr.Dataset({'TWSA':tws,'TWSA_GWS_reference':tws_balance,'GWSA':gw,'GWSA_filtered_soil_sensitivity':gwfiltered,'G3P_GWSA_benchmark':ng,'SMSA':sms,'SWSA':swa,'CanopyA':cws,'SWEA':swe,'GLDAS_land_storage_anomaly':rebase(noah)})
ds.attrs={'storage_balance':'Full five-compartment equation; no zero surface-water assumption','period_TWS':'April2002–September2024','period_GWS':'April2002–September2023, true missing months retained','spatial_support':'nominal0.25deg grid; basin estimates share coarser GRACE information','baseline':'2004–2009 joint observed monthly reference','source_surface_water':'G3P v1.12/LISFLOOD-GloFAS4,250km filter, river+lake+reservoir','limitations':'No causal human attribution from residual alone; compartment filtering mismatch retained as structural uncertainty'}
ds.to_netcdf(output(OBJ1,'netcdf','Thailand_TWSA_GWSA_components.nc'))
regions=region_weights(grace.lat,grace.lon);frames=[];rows=[];coverage=[]
for code,name,w in regions:
    frame=pd.DataFrame({'date':dates,'region':code,'region_name':name})
    for var in ds:
        # Export compartment means on the same cells/months as groundwater so
        # the regional five-compartment balance can be reproduced from the CSV.
        field=ds[var].where(ds.GWSA.notnull()) if var in ['TWSA_GWS_reference','SMSA','SWSA','CanopyA','SWEA'] else ds[var]
        v,c=weighted_series(field,w,threshold=.3);frame[var]=v;frame[var+'_area_fraction']=c
        coverage.append({'region':code,'region_name':name,'variable':var,'mean_fraction':float(np.mean(c)),'min_fraction':float(np.min(c)),'months_at_least30percent':int(np.sum(c>=.3))})
        if var in ['TWSA','GWSA','GWSA_filtered_soil_sensitivity','G3P_GWSA_benchmark']:
            with warnings.catch_warnings():warnings.simplefilter('ignore');stats=trend_statistics(v,dates,bootstrap=300)
            rows.append({'region':code,'region_name':name,'variable':var,**stats})
    frames.append(frame);print('Regional trends:',name,flush=True)
series=pd.concat(frames,ignore_index=True);series.to_csv(output(OBJ1,'tables','basin_storage_timeseries.csv'),index=False)
trends=pd.DataFrame(rows)
for var,g in trends.groupby('variable'):
    i=g[g.region!='TH'].index;trends.loc[i,'mk_seasonal_q_FDR']=bh_fdr(trends.loc[i,'mk_seasonal_p'])
trends.to_csv(output(OBJ1,'tables','basin_TWSA_GWSA_Sen_MannKendall.csv'),index=False)
pd.DataFrame(coverage).to_csv(output(OBJ1,'tables','basin_component_coverage.csv'),index=False)
# Grid-level statistics retain original storage resolution labels, no disaggregation claim.
grid={};gridrows=[]
for var in ['TWSA','GWSA']:
    z=ds[var].values;statsarrays={n:np.full(z.shape[1:],np.nan) for n in ['sen_slope_mm_year','mk_original_p','mk_seasonal_p']}
    for row,col in np.argwhere(np.isfinite(z).sum(axis=0)>=24):
        with warnings.catch_warnings():warnings.simplefilter('ignore');st=trend_statistics(z[:,row,col],dates)
        for n in statsarrays:statsarrays[n][row,col]=st.get(n,np.nan)
    statsarrays['mk_seasonal_q_FDR']=bh_fdr(statsarrays['mk_seasonal_p'].ravel()).reshape(z.shape[1:])
    for n,a in statsarrays.items():grid[var+'_'+n]=(('lat','lon'),a)
    print('Grid trend complete:',var,flush=True)
grid=xr.Dataset(grid,coords={'lat':grace.lat,'lon':grace.lon},attrs={'significance':'seasonal MK p; FDR by storage variable; serial dependence not removed in grid p-values','slope':'seasonal Sen median same-calendar-month slopes in mm/year'})
grid.to_netcdf(output(OBJ1,'netcdf','spatial_Sen_MannKendall.nc'))
geo=gpd.read_file(core/'BASINS/MainBasin_ONWR_Law_WGS84.shp').to_crs(4326);geo['region']=geo.MB_CODE.astype(str).str.zfill(2)
plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False})
for var in ['TWSA','GWSA']:
    table=trends[(trends.variable==var)&(trends.region!='TH')];mapdata=geo.merge(table,on='region',how='left');bound=max(abs(table.sen_slope_mm_year.min()),abs(table.sen_slope_mm_year.max()))
    fig,ax=plt.subplots(figsize=(6,9));mapdata.plot(column='sen_slope_mm_year',cmap='RdBu',vmin=-bound,vmax=bound,ax=ax,edgecolor='#555555',linewidth=.35,legend=True,legend_kwds={'label':'Seasonal Sen slope (mm/year)','shrink':.65});ax.set_aspect('equal');ax.set(xlabel='Longitude (°E)',ylabel='Latitude (°N)',title=var+' basin storage trends');fig.tight_layout();fig.savefig(output(OBJ1,'figures',var+'_basin_Sen_trend.png'),dpi=320);plt.close(fig)
    fig,ax=plt.subplots(figsize=(11,5));n=series[series.region=='TH'];ax.plot(pd.to_datetime(n.date),n[var],color='#168080');ax.set_ylabel(var+' (mm)');fig.tight_layout();fig.savefig(output(OBJ1,'figures',var+'_national_timeseries.png'),dpi=320);plt.close(fig)
status={'regions':len(regions),'component_balance_max_GLDASError_mm':err,'baseline':'2004–2009 joint valid months','TWS_end':'2024-09','GWS_end':'2023-09','SWS_source':'G3P v1.12/LISFLOOD-GloFAS4','grid_significance':'Seasonal MK with FDR; no complete serial-correlation correction','regional_uncertainty':'300 calendar-year block bootstrap seasonal Sen intervals','GWS_limit':'all compartments included, but model errors and filtering mismatch remain'}
output(OBJ1,'logs','objective1_status.json').write_text(json.dumps(status,indent=2),encoding='utf-8');print(json.dumps(status,indent=2),flush=True)
