"""Reproduce the direct WaterGAP robustness and rainfall-process analysis."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,sys
P=Path(__file__).resolve().parent
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--mode',choices=['check','full','verify'],default='full');ap.add_argument('--work-dir',type=Path,default=Path('output/direct_reproduction'));ap.add_argument('--figures',action='store_true');a=ap.parse_args();work=a.work_dir.resolve()
 if work==P or work in P.parents:raise ValueError('Use a separate work directory')
 manifest=json.loads((P/'input_manifest.json').read_text())
 for f in manifest['files']:
  p=P/'inputs'/f['path'];assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==f['sha256'],f['path']
 print('Verified frozen inputs:',len(manifest['files']),flush=True)
 if a.mode=='check':return
 if a.mode=='full':
  for f in manifest['files']:
   src=P/'inputs'/f['path'];dst=work/f['path'];dst.parent.mkdir(parents=True,exist_ok=True)
   if dst.exists():assert hashlib.sha256(dst.read_bytes()).hexdigest()==f['sha256'],f['path']
   else:shutil.copy2(src,dst)
  env=os.environ.copy();env.update(TWSA_RESEARCH_ROOT=str(work),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',MPLBACKEND='Agg',PYTHONHASHSEED='0')
  for command in [['91_build_robustness_analysis.py','audit','models','wells','reservoir'],['92_rainfall_concentration_analysis.py'],['93_evidence_matrix.py']]+([['94_robustness_figures.py']] if a.figures else []):
   subprocess.run([sys.executable,str(P/'scripts'/command[0]),*command[1:]],cwd=work,env=env,check=True)
 import pandas as pd
 result=[];folder=work/'Thailand_Direct_WaterGAP_Analysis/robustness_extension/tables'
 for expected in sorted((P/'reference').glob('*.csv')):
  x=pd.read_csv(expected,dtype={'region':str});y=pd.read_csv(folder/expected.name,dtype={'region':str});pd.testing.assert_frame_equal(x,y,check_exact=False,rtol=1e-6,atol=1e-7);result.append({'table':expected.name,'rows':len(x),'passed':True})
 receipt={'passed':True,'python':sys.version,'tables':result,'input_files':len(manifest['files']),'scope':'Scientific-input reproduction; raw CHIRPS/ISIMIP retrieval is an optional separate script'};dest=work/'run_logs_v8';dest.mkdir(exist_ok=True);(dest/'receipt.json').write_text(json.dumps(receipt,indent=2));print('All new numerical reference tables reproduced.',flush=True)
if __name__=='__main__':main()
