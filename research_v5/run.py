"""Rebuild the original scientific inputs, then the extended CSR study."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,sys,time
P=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--mode',choices=['check','full','figures','verify'],default='full');ap.add_argument('--work-dir',type=Path,default=P/'work');ap.add_argument('--reuse-base',action='store_true',help='Reuse an already successfully reproduced v4 work directory.');a=ap.parse_args();work=a.work_dir.resolve()
    if work==P or work in P.parents:raise ValueError('Use a separate work directory.')
    manifest=json.loads((P/'input_manifest.json').read_text())
    for f in manifest['files']:
        source=P/'inputs'/f['path'];assert source.is_file() and sha(source)==f['sha256'],f['path']
    subprocess.run([sys.executable,str(P.parent/'research/run.py'),'--mode','check'],check=True)
    print('Extended inputs verified:',len(manifest['files']),flush=True)
    if a.mode=='check':return
    if a.mode=='full' and not a.reuse_base:subprocess.run([sys.executable,str(P.parent/'research/run.py'),'--mode','full','--work-dir',str(work)],check=True)
    if a.mode=='full':
        receipt=json.loads((work/'run_logs/full_receipt.json').read_text());assert receipt['passed'],'Base reproduction must pass first.'
        for f in manifest['files']:
            dst=work/f['path'];dst.parent.mkdir(parents=True,exist_ok=True)
            if dst.exists():assert sha(dst)==f['sha256'],'Input already differs: '+str(dst)
            else:shutil.copy2(P/'inputs'/f['path'],dst)
    env=os.environ.copy();env.update(TWSA_RESEARCH_ROOT=str(work),TWSA_V5_PACKAGE=str(P),MPLBACKEND='Agg',PYTHONHASHSEED='0',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    logs=work/'run_logs_v5';logs.mkdir(exist_ok=True,parents=True);started=time.time();record={'passed':False,'python':sys.version,'steps':[]}
    steps=(['17_csr_storage_attribution_v5.py','18_attribution_robustness_v5.py','19_climate_tests_v5.py','20_groundwater_network_v5.py','21_figures_synthesis_v5.py','29_reservoir_validation_v5.py'] if a.mode=='full' else [])+(['37_spatiotemporal_figure_revision.py'] if a.mode in ['full','figures'] else [])+['validate_extended.py']
    for name in steps:
        print('Running '+name,flush=True);t=time.time()
        with (logs/(name+'.log')).open('w',encoding='utf-8') as log:
            proc=subprocess.Popen([sys.executable,'-u',str(P/'scripts'/name)],cwd=work,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
            for line in proc.stdout:print(line,end='',flush=True);log.write(line);log.flush()
            code=proc.wait()
        record['steps'].append({'script':name,'sha256':sha(P/'scripts'/name),'exit_code':code,'seconds':round(time.time()-t,2)})
        (logs/'receipt.json').write_text(json.dumps(record,indent=2))
        if code:raise RuntimeError(name+' failed. See '+str(logs))
    record.update(passed=True,seconds=round(time.time()-started,2));(logs/'receipt.json').write_text(json.dumps(record,indent=2));print('Extended reproduction passed.',flush=True)
if __name__=='__main__':main()
