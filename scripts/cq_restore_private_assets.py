"""Qualify actual private HF pins from a clean GitHub checkout on c225."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

from assets import read, save, validate, safe, verify_file


def main():
    if socket.gethostname().split('.')[0] != 'c225':
        raise ValueError('Qualification uses the original c225 interpreter read-only')
    out=Path(os.environ['CQ_OUTPUT_DIR']).resolve()
    work=Path(os.environ['MACROHFT_RESTORE_ROOT']).resolve()
    if not str(work).startswith('/date/zyy/macrohft-assets/') or work.exists():
        raise ValueError('Choose a new authorized remote restore directory')
    out.mkdir(parents=True,exist_ok=True);work.mkdir(parents=True)
    code=os.environ['SOURCE_COMMIT'];started=time.monotonic()
    env=dict(os.environ,HF_HUB_CACHE=str(work/'cache/hub'),HF_XET_CACHE=str(work/'cache/xet'),
             MACROHFT_HF_CACHE=str(work/'cache/hub'),MACROHFT_ASSET_ROOT=str(work/'assets'),
             PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
    # The existing qualified client environment is host-local and is never modified.
    transfer=Path(os.environ['MACROHFT_TRANSFER_PYTHON'])
    numerical=Path('/date/zyy/macrohft-reproduction/.venv/bin/python')
    clean=work/'clean-code';log=work/'private-process.log'
    def mark(n,stage):
        (out/'progress.log').write_text(f'{n}/5 {stage}\n')
        print(json.dumps({'stage':stage}),flush=True)
    def run(cmd,cwd=work,timeout=1200):
        with log.open('a') as stream:
            subprocess.run([str(x) for x in cmd],cwd=cwd,env=env,stdout=stream,
                           stderr=subprocess.STDOUT,check=True,timeout=timeout)
    mark(0,'fetch exact GitHub code into an empty working directory')
    run(['git','init','-q',clean]);run(['git','remote','add','origin','https://github.com/SansaZheng/MacroHFT.git'],clean)
    run(['git','fetch','--depth=1','--filter=blob:none','origin',code],clean)
    run(['git','checkout','--detach','FETCH_HEAD'],clean)
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=clean,text=True).strip()!=code:
        raise ValueError('Clean code commit mismatch')
    run([numerical,'scripts/verify_source.py','--expected-commit',code],clean)
    manifest=validate(read(clean/'assets/manifest.json'),require_pins=True)
    if any(a['status']!='verified' for a in manifest['assets']):raise ValueError('Unverified private assets')
    run([transfer,'-c',"import huggingface_hub as h; assert h.__version__=='1.8.0'"],clean)
    mark(1,'selective private downloads at immutable manifest revisions')
    selected=[]
    for a in manifest['assets']:
        if a['id'] not in ['eth-prepared','feature-definitions'] and a['repo_type']!='model':continue
        files=[f for f in a['files'] if f.get('role')!='documentation' and
               not (a['id']=='eth-prepared' and '/test/' in f['path'])]
        cmd=[transfer,'scripts/assets.py','fetch','--asset',a['id']]
        for f in files:cmd.extend(['--file',f['path']])
        run(cmd,clean)
        selected.append(dict(a,files=files))
    mark(2,'verify original server backup against all uploaded payload identities')
    backups=[]
    for a in manifest['assets']:
        legacy=Path('/date/zyy/macrohft-reproduction')
        if a['id']=='cost-memory-data':
            legacy=Path(os.environ['MACROHFT_MIGRATION_ROOT'])/'historical-originals'
        for f in a['files']:
            if f.get('role')=='documentation':continue
            verify_file(safe(legacy,f['source_path']),f)
            backups.append({'asset':a['id'],'path':f['source_path'],'size':f['size'],'sha256':f['sha256']})
    save(out/'independent-backup.json',{'verified':True,'files':backups,'originals_deleted':False})
    mark(3,'run numerical reproduction checks against recovered validation data and experts')
    run([numerical,'scripts/remote_run.py','--work-dir',work/'runtime-check','--check-only'],clean)
    # Check every retained model is a finite tensor state dictionary, without evaluating a test period.
    model_paths=[str(safe(work/'assets',a['id']+'/'+f['path'])) for a in selected
                 if a['repo_type']=='model' for f in a['files']]
    save(work/'model-paths.json',model_paths)
    inspect_script="""import json,sys,torch,importlib.metadata as m
from pathlib import Path
paths=json.loads(Path(sys.argv[1]).read_text());checked=[]
for p in paths:
 state=torch.load(p,map_location='cpu',weights_only=True)
 assert isinstance(state,dict) and state
 assert all(isinstance(t,torch.Tensor) and torch.isfinite(t).all().item() for t in state.values())
 checked.append({'path':p,'tensors':len(state),'parameters':sum(t.numel() for t in state.values())})
Path(sys.argv[2]).write_text(json.dumps({'models':checked,'packages':{n:m.version(n) for n in ['torch','numpy','pandas','pyarrow','gym','scipy']}},indent=2)+'\\n')
"""
    run([numerical,'-c',inspect_script,work/'model-paths.json',out/'model-runtime.json'],clean)
    mark(4,'record exact recovered files and successful runtime evidence')
    text=log.read_text(errors='replace')
    if 'Ran 10 tests' not in text or '\nOK\n' not in text:
        raise ValueError('Numerical check receipt missing')
    save(out/'receipt.json',{'complete':True,'source_commit':code,'clean_github_checkout':True,
         'private_project_assets_verified':True,'numerical_tests_passed':10,'models_loaded':len(model_paths),
         'independent_backup_files':len(backups),'downloaded_files':sum(len(a['files']) for a in selected),
         'downloaded_bytes':sum(f['size'] for a in selected for f in a['files']),
         'selected_assets':[{k:a[k] for k in ['id','repo_id','repo_type','revision']} for a in selected],
         'test_split_downloaded':False,'training_or_held_out_evaluation_performed':False,
         'existing_environment_modified':False,'originals_deleted':False,
         'remote_work_directory':str(work),'elapsed_seconds':time.monotonic()-started})
    mark(5,'private pinned restore and numerical reproduction check passed')


if __name__=='__main__':
    try:main()
    except Exception as exc:
        out=Path(os.environ['CQ_OUTPUT_DIR']);out.mkdir(parents=True,exist_ok=True)
        failure={'complete':False,'error_type':type(exc).__name__}
        save(out/'failure.json',failure);print(json.dumps(failure),flush=True);sys.exit(1)
