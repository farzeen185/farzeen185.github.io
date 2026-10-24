"""Discover publisher-provided naturalized/anthropogenic WaterGAP output."""
import json,re
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'shared_data/WaterGAP';OUT.mkdir(exist_ok=True)
api='https://api.gude.uni-frankfurt.de/api'
records={}
for scenario,doi in [('natural','10.25716/GUDE.1TWP-GNQP'),('human','10.25716/GUDE.14B4-KQ6R')]:
    r=requests.get('https://doi.org/'+doi,timeout=40);r.raise_for_status()
    (OUT/(scenario+'_record.html')).write_text(r.text,encoding='utf-8')
    ids=list(dict.fromkeys(re.findall(r'/researchdata/([a-f0-9-]{36})',r.text)))
    assert len(ids)==1,ids
    item=requests.get(api+'/core/items/'+ids[0],timeout=30);item.raise_for_status();item=item.json()
    bundles=requests.get(api+'/core/items/'+ids[0]+'/bundles?size=100',timeout=30);bundles.raise_for_status()
    files=[]
    for bundle in bundles.json()['_embedded']['bundles']:
        if bundle['name']!='ORIGINAL':continue
        u=bundle['_links']['bitstreams']['href']+'?size=1000'
        result=requests.get(u,timeout=30);result.raise_for_status()
        for b in result.json()['_embedded']['bitstreams']:
            files.append({'name':b['name'],'id':b['uuid'],'bytes':b['sizeBytes'],'checksum':b.get('checkSum'),'url':b['_links']['content']['href']})
    records[scenario]={'doi':doi,'record_url':r.url,'uuid':ids[0],'metadata':item.get('metadata'),'files':files}
    print(scenario,item['name'],'files',len(files),flush=True)
    for f in files:
        if any(v in f['name'] for v in ['_tws_','_groundwstor_','_soil_','_canop_','_snow_','_prec_','_potevap_','_anag_']):print(f['name'],f['bytes'],f['id'],flush=True)
(OUT/'publisher_inventory.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
