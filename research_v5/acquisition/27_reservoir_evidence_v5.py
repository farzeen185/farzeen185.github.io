"""Independent reservoir evidence: acquisition and explicit provenance."""
from pathlib import Path
import requests, json, zipfile, hashlib
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'shared_data/reservoir_independent'; P.mkdir(exist_ok=True)
record=requests.get('https://zenodo.org/api/records/14844580',timeout=60);record.raise_for_status();j=record.json()
(P/'zenodo_record.json').write_text(json.dumps(j,indent=2),encoding='utf-8')
entry=next(x for x in j['files'] if x['key'].startswith('MSEA-Res'))
f=P/'MSEA-Res_database_v2.zip'
if not f.exists():
    with requests.get(entry['links']['self'],stream=True,timeout=180) as r:
        r.raise_for_status()
        with f.open('wb') as out:
            for b in r.iter_content(1024*1024):out.write(b)
assert f.stat().st_size==entry['size']
z=zipfile.ZipFile(f)
(P/'inventory.json').write_text(json.dumps(z.namelist(),indent=2),encoding='utf-8')
(P/'provenance.json').write_text(json.dumps({'doi':'10.5281/zenodo.14844580','paper':'10.5194/essd-17-2693-2025','sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size,'source':entry['links']['self'],'license':j['metadata'].get('license'),'acquired':'2026-10-25'},indent=2),encoding='utf-8')
print('Downloaded',f.stat().st_size,flush=True)
print('\n'.join(z.namelist()[:65]),flush=True)
