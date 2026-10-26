"""Verify inputs or reproduce the publication extension on Windows/Linux."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,sys,time
P=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--mode',choices=['check','full','verify'],default='full');ap.add_argument('--work-dir',type=Path,default=P/'work');a=ap.parse_args();work=a.work_dir.resolve()
 if work==P or work in P.parents:raise ValueError('Use a separate work directory')
 manifest=json.loads((P/'input_manifest.json').read_text())
 for f in manifest['files']:
  src=P/'inputs'/f['path'];assert src.is_file() and sha(src)==f['sha256'],f['path']
 print('Frozen inputs verified:',len(manifest['files']),flush=True)
 if a.mode=='check':return
 if a.mode=='full':
  for f in manifest['files']:
   dst=work/f['path'];dst.parent.mkdir(parents=True,exist_ok=True)
   if dst.exists():assert sha(dst)==f['sha256'],'Existing work input differs: '+str(dst)
   else:shutil.copy2(P/'inputs'/f['path'],dst)
  env=os.environ.copy();env.update(TWSA_RESEARCH_ROOT=str(work),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',MPLBACKEND='Agg',PYTHONHASHSEED='0')
  subprocess.run([sys.executable,str(P/'scripts/57_enso_publication_analysis.py')],cwd=work,env=env,check=True)
 import pandas as pd
 checks=[]
 for p in sorted((P/'reference').glob('*.csv')):
  expected=pd.read_csv(p,dtype={'region':str});actual=pd.read_csv(work/'Thailand_Publication_v6/tables'/p.name,dtype={'region':str});pd.testing.assert_frame_equal(actual,expected,check_exact=False,rtol=1e-7,atol=1e-8);checks.append({'file':p.name,'rows':len(actual),'passed':True})
 receipt={'passed':True,'python':sys.version,'input_files':len(manifest['files']),'comparisons':checks,'source_sha256':sha(P/'scripts/57_enso_publication_analysis.py'),'scope':'Publication extension; original hydrological analyses are separately rebuilt by research_v5.'};out=work/'run_logs_v6';out.mkdir(parents=True,exist_ok=True);(out/'receipt.json').write_text(json.dumps(receipt,indent=2));print('Publication extension reproduced and all six reference tables matched.',flush=True)
if __name__=='__main__':main()
