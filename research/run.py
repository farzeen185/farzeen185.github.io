"""Portable entry point; keeps recomputed outputs separate from frozen references."""
import argparse,hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path

PACKAGE=Path(__file__).resolve().parent
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=['check','smoke','full','verify'],default='full')
    parser.add_argument('--work-dir',type=Path,default=PACKAGE/'work')
    args=parser.parse_args();work=args.work_dir.resolve()
    manifest=json.loads((PACKAGE/'input_manifest.json').read_text(encoding='utf-8'))
    for item in manifest['files']:
        p=PACKAGE/item['path']
        if not p.is_file() or sha(p)!=item['sha256']:raise RuntimeError('Missing or changed input: '+item['path'])
    print(f"Verified {len(manifest['files'])} supplied inputs ({manifest['total_bytes']/1e6:.1f} MB).",flush=True)
    if args.mode=='check':return
    if work==PACKAGE or work in PACKAGE.parents:raise ValueError('Choose a separate work directory, not the package or repository root.')
    work.mkdir(parents=True,exist_ok=True)
    if args.mode!='verify':
        for item in manifest['files']:
            target=work/item['path'];target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists():
                if sha(target)!=item['sha256']:raise RuntimeError('Work input changed; use a new work directory: '+str(target))
            else:shutil.copy2(PACKAGE/item['path'],target)
    (work/'reports').mkdir(exist_ok=True);logs=work/'run_logs';logs.mkdir(exist_ok=True)
    env=os.environ.copy();env.update(TWSA_RESEARCH_ROOT=str(work),TWSA_PACKAGE_ROOT=str(PACKAGE),PYTHONHASHSEED='0',MPLBACKEND='Agg',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    steps={'smoke':['smoke_check.py','00_groundwater_indices.py'],
           'full':['smoke_check.py','01_storage_and_trends.py','00_groundwater_indices.py','06_naturalized_attribution.py','07_climate_emulators.py','08_attribution_evidence.py','09_research_release.py','export_dashboard.py','validate_reproduction.py'],
           'verify':['validate_reproduction.py']}[args.mode]
    receipt={'mode':args.mode,'python':sys.version,'inputs_verified':len(manifest['files']),'steps':[],'passed':False}
    receipt_path=logs/f'{args.mode}_receipt.json';started=time.time()
    for name in steps:
        print('\nRunning '+name,flush=True);start=time.time()
        with (logs/(name+'.log')).open('w',encoding='utf-8') as log:
            process=subprocess.Popen([sys.executable,'-u',str(PACKAGE/'scripts'/name)],cwd=work,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
            for line in process.stdout:print(line,end='',flush=True);log.write(line);log.flush()
            code=process.wait()
        receipt['steps'].append({'script':name,'sha256':sha(PACKAGE/'scripts'/name),'exit_code':code,'seconds':round(time.time()-start,2)})
        receipt_path.write_text(json.dumps(receipt,indent=2),encoding='utf-8')
        if code:raise RuntimeError(f'{name} failed; see {logs/(name+".log")}')
    receipt.update(passed=True,seconds=round(time.time()-started,2));receipt_path.write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(f'\n{args.mode} completed in {receipt["seconds"]:.1f} seconds. Results: {work}',flush=True)
if __name__=='__main__':main()
