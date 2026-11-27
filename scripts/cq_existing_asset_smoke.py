"""Qualify a clean code checkout using a project-owned interpreter without modifying it."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


def main():
    out=Path(os.environ['CQ_OUTPUT_DIR']).resolve();out.mkdir(parents=True,exist_ok=True)
    code=os.environ['SOURCE_COMMIT'];python=Path('/date/zyy/macrohft-reproduction/.venv/bin/python')
    if not python.is_file():raise FileNotFoundError('Authorized project interpreter unavailable')
    started=time.monotonic();clean=out/'clean-code'
    env=dict(os.environ,HF_HOME=str(out/'hf-home'),HF_HUB_CACHE=str(out/'cache/hub'),HF_XET_CACHE=str(out/'cache/xet'),
             HF_HUB_DISABLE_IMPLICIT_TOKEN='1',PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1')
    env.pop('HF_TOKEN',None);env.pop('HUGGING_FACE_HUB_TOKEN',None)
    def mark(n,t):
        (out/'progress.log').write_text(f'{n}/4 {t}\n');print(f'{n}/4 {t}',flush=True)
    def run(cmd,cwd=out):
        with (out/'smoke.log').open('a') as log:
            subprocess.run([str(x) for x in cmd],cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
    mark(0,'fresh pinned GitHub checkout')
    run(['git','init','-q',clean]);run(['git','remote','add','origin','https://github.com/SuuTTT/MacroHFT.git'],clean)
    run(['git','fetch','--depth=1','--filter=blob:none','origin',code],clean);run(['git','checkout','--detach','FETCH_HEAD'],clean)
    actual=subprocess.check_output(['git','rev-parse','HEAD'],cwd=clean,text=True).strip()
    if actual!=code:raise ValueError('Code identity mismatch')
    mark(1,'inspect existing official client capabilities without installation')
    probe="import json,inspect,sys,importlib.metadata as m;import huggingface_hub as h;api=h.HfApi;names=['upload_folder','auth_check','get_paths_info','repo_info','create_repo','list_models','list_datasets','whoami'];print(json.dumps({'python':sys.version,'huggingface_hub':h.__version__,'api_parameters':{n:list(inspect.signature(getattr(api,n)).parameters) if hasattr(api,n) else None for n in names},'packages':{n:m.version(n) for n in ['huggingface_hub','fsspec','filelock','typing_extensions','tqdm']}}))"
    details=json.loads(subprocess.check_output([str(python),'-c',probe],env=env,text=True,timeout=30))
    params=details['api_parameters']
    details['upload_api_compatible']=all(params.values()) and 'write' in params['auth_check'] and 'parent_commit' in params['upload_folder']
    (out/'environment.json').write_text(json.dumps(details,indent=2)+'\n')
    run([python,'scripts/verify_source.py','--expected-commit',code],clean)
    run([python,'scripts/check_git_policy.py'],clean)
    run([python,'-m','unittest','discover','-s','tests','-p','test_assets.py'],clean)
    mark(2,'selective pinned download into an empty job-specific cache')
    run([python,'scripts/assets.py','--manifest','assets/transport-fixture.json','fetch','--asset','hf-transport-fixture','--root',out/'assets','--cache-dir',out/'cache/hub'],clean)
    run([python,'scripts/assets.py','--manifest','assets/transport-fixture.json','verify','--asset','hf-transport-fixture','--root',out/'assets'],clean)
    run([python,'scripts/assets.py','--manifest','assets/transport-fixture.json','stream-verify','--asset','hf-transport-fixture'],clean)
    mark(3,'minimal deterministic execution')
    run([python,'-m','unittest','discover','-s','research/delayed-memory-validity-v2/tests','-p','test_*.py'],clean)
    if json.loads((out/'assets/hf-transport-fixture/config.json').read_text()).get('model_type')!='bert':raise ValueError('Fixture parse failure')
    receipt={'complete':True,'source_commit':code,'clean_github_checkout':True,'client_environment':details,
             'existing_environment_modified':False,'private_project_assets_verified':False,'credentials_used':False,
             'elapsed_seconds':time.monotonic()-started,'fixture_manifest':json.loads((clean/'assets/transport-fixture.json').read_text())}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    for name in ['clean-code','cache','assets','hf-home']:
        p=out/name
        if p.is_dir() and not p.is_symlink():shutil.rmtree(p)
    mark(4,'remote selective transfer and execution verified')


if __name__=='__main__':
    try:main()
    except Exception:
        log=Path(os.environ['CQ_OUTPUT_DIR'])/'smoke.log'
        if log.is_file():print(log.read_text(errors='replace')[-8000:],file=sys.stderr,flush=True)
        raise
