"""Resumable authenticated-free Zenodo byte-range acquisition and Thai extraction."""
from pathlib import Path
import concurrent.futures, json, math, time, zlib
import requests

ROOT=Path(__file__).resolve().parent
SOURCE='https://zenodo.org/records/15149480/files/data.zip?download=1'
START=2145362150
END=3587444108
CHUNK=16*1024*1024
CACHE=ROOT/'download_parts'; CACHE.mkdir(exist_ok=True)

def acquire(i):
    lo=START+i*CHUNK; hi=min(END-1,lo+CHUNK-1)
    target=CACHE/f'{i:04d}.part'
    if target.exists() and target.stat().st_size==hi-lo+1: return target
    for attempt in range(8):
        try:
            temporary=target.with_suffix('.tmp')
            with requests.get(SOURCE+f'&range_part={i}',headers={'Range':f'bytes={lo}-{hi}'},timeout=(20,180),stream=True) as r:
                if r.status_code!=206:
                    raise RuntimeError(f'HTTP{r.status_code}')
                with temporary.open('wb') as out:
                    for block in r.iter_content(64*1024): out.write(block)
            if temporary.stat().st_size!=hi-lo+1:
                raise RuntimeError(f'Wrong range length {temporary.stat().st_size}')
            temporary.replace(target)
            print(f'Downloaded chunk {i+1}',flush=True); return target
        except Exception as e:
            print(f'Retry {i} {attempt}: {e}',flush=True); time.sleep(min(30,attempt*3+2))
    raise RuntimeError(f'Chunk {i} failed')

def main():
    n=math.ceil((END-START)/CHUNK)
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        list(pool.map(acquire,range(n)))
    parquet=ROOT/'grow_timeseries_global.parquet'
    if not parquet.exists():
        d=zlib.decompressobj(-15)
        with parquet.with_suffix('.tmp').open('wb') as out:
            for i in range(n):
                with (CACHE/f'{i:04d}.part').open('rb') as part:
                    while block:=part.read(256*1024):
                        out.write(d.decompress(block))
                if d.eof: break
            out.write(d.flush())
        parquet.with_suffix('.tmp').replace(parquet)
    import pandas as pd
    import pyarrow.parquet as pq
    metadata=pd.read_csv('P:/twsa/Thailand_Objective3/data/groundwater/GROW/GROW_Thailand_attributes.csv',dtype={'GROW_ID':str})
    metadata.to_csv(ROOT/'GROW_Thailand_attributes.csv',index=False)
    ids=set(metadata.GROW_ID)
    p=pq.ParquetFile(parquet); print('Schema',p.schema,flush=True)
    matches=[]
    import pyarrow as pa
    import pyarrow.compute as pc
    for batch in p.iter_batches(batch_size=10000):
        if 'GROW_ID' in batch.schema.names:
            selected=batch.filter(pc.is_in(batch.column('GROW_ID'),value_set=pa.array(sorted(ids)))).to_pandas()
        else:
            raise RuntimeError(f'Unexpected schema {batch.schema.names}')
        if len(selected): matches.append(selected)
    result=pd.concat(matches,ignore_index=True)
    result.to_csv(ROOT/'GROW_Thailand_timeseries_raw.csv',index=False)
    depth_col='groundwater_depth_from_ground_elevation_m'
    if depth_col not in result:
        raise RuntimeError(f'Expected observed depth column absent: {result.columns.tolist()}')
    valid=result[result[depth_col].notna()].copy()
    normalized=pd.DataFrame({'well_id':valid.GROW_ID.astype(str),'date':pd.to_datetime(valid['date']).dt.strftime('%Y-%m-%d'),'depth_to_water_m':pd.to_numeric(valid[depth_col]),'interval':valid['interval'],'source':'GROW / IGRAC / Thai Ministry of Natural Resources and Environment','value_status':'observed aggregate, not gap-filled'})
    normalized=normalized.merge(metadata[['GROW_ID','latitude','longitude','provider_ground_elevation_m_asl']].rename(columns={'GROW_ID':'well_id'}),on='well_id',validate='many_to_one')
    normalized['groundwater_level_m_asl']=normalized.provider_ground_elevation_m_asl-normalized.depth_to_water_m
    normalized['groundwater_head_anomaly_m']=-normalized.depth_to_water_m+normalized.groupby('well_id').depth_to_water_m.transform('mean')
    normalized.sort_values(['well_id','date']).to_csv(ROOT/'GROW_Thailand_observations.csv',index=False)
    normalized[normalized.interval=='YS'].to_csv(ROOT/'GROW_Thailand_annual_observations.csv',index=False)
    normalized[normalized.interval=='MS'].to_csv(ROOT/'GROW_Thailand_monthly_observations.csv',index=False)
    coverage=normalized.groupby('well_id').agg(records=('date','count'),start=('date','min'),end=('date','max'),interval=('interval','first'))
    coverage.to_csv(ROOT/'GROW_Thailand_observed_coverage.csv')
    (ROOT/'provenance.json').write_text(json.dumps({'source':SOURCE,'zenodo_record':15149480,'well_metadata_license':'CC BY 4.0 (Thai metadata)','package_license_notice':'CC BY-NC-SA 4.0 per Zenodo description; retain package notice when redistributing','reference_point':'Water depth [from the ground surface]','units':'m','wells':len(metadata),'measurement_rows':len(result),'columns':result.columns.tolist()},indent=2))
    print(f'COMPLETE {len(result)} Thai measurements',flush=True)

if __name__=='__main__': main()
