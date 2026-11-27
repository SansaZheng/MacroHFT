"""Clean CQ checkout + official HF selective transfer qualification (public JSON only)."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


def main():
    root=Path(__file__).resolve().parents[1]
    out=Path(os.environ['CQ_OUTPUT_DIR']).resolve();out.mkdir(parents=True,exist_ok=True)
    commit=os.environ['SOURCE_COMMIT'];started=time.monotonic()
    progress=out/'progress.log'
    def mark(n,text):progress.write_text(f'{n}/5 {text}\n')
    def run(args,cwd=None,env=None):
        with (out/'smoke.log').open('a') as log:
            subprocess.run([str(x) for x in args],cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=420)
    mark(0,'clean pinned GitHub checkout')
    clean=out/'clean-code'
    # New repository and a depth-one fetch; never a full-history clone.
    run(['git','init','-q',clean])
    run(['git','remote','add','origin','https://github.com/SuuTTT/MacroHFT.git'],clean)
    run(['git','fetch','--depth=1','--filter=blob:none','origin',commit],clean)
    run(['git','checkout','--detach','FETCH_HEAD'],clean)
    actual=subprocess.check_output(['git','rev-parse','HEAD'],cwd=clean,text=True).strip()
    if actual!=commit:raise ValueError('Code commit mismatch')
    mark(1,'create isolated transfer client environment')
    # This venv is local to this CQ output and never reused on another host.
    candidates=[sys.executable,'/date/zyy/macrohft-reproduction/.venv/bin/python']
    python=None
    for candidate in candidates:
        if not Path(candidate).exists():continue
        check=subprocess.run([candidate,'-c','import sys;sys.exit(sys.version_info < (3,9))'],capture_output=True)
        if check.returncode==0:python=candidate;break
    if python is None:raise RuntimeError('Python >=3.9 is required')
    run([python,'-m','venv',out/'tool-env'])
    py=out/'tool-env/bin/python'
    env=dict(os.environ,HF_HOME=str(out/'hf-home'),HF_HUB_CACHE=str(out/'cache/hub'),
             HF_XET_CACHE=str(out/'cache/xet'),PIP_CACHE_DIR=str(out/'cache/pip'),
             HF_HUB_DISABLE_IMPLICIT_TOKEN='1',PYTHONDONTWRITEBYTECODE='1')
    env.pop('HF_TOKEN',None);env.pop('HUGGING_FACE_HUB_TOKEN',None)
    run([py,'-m','pip','install','--no-cache-dir','-r',clean/'requirements/assets.txt'],clean,env)
    mark(2,'verify code policy and asset transfer tests')
    run([py,'scripts/verify_source.py','--expected-commit',commit],clean,env)
    run([py,'scripts/check_git_policy.py'],clean,env)
    run([py,'-m','unittest','discover','-s','tests','-p','test_assets.py'],clean,env)
    mark(3,'download one immutable public JSON asset')
    run([py,'scripts/assets.py','--manifest','assets/transport-fixture.json','fetch',
         '--asset','hf-transport-fixture','--root',out/'assets','--cache-dir',out/'cache/hub'],clean,env)
    run([py,'scripts/assets.py','--manifest','assets/transport-fixture.json','verify',
         '--asset','hf-transport-fixture','--root',out/'assets'],clean,env)
    run([py,'scripts/assets.py','--manifest','assets/transport-fixture.json','stream-verify',
         '--asset','hf-transport-fixture'],clean,env)
    mark(4,'minimal deterministic research execution')
    run([py,'-m','unittest','discover','-s','research/delayed-memory-validity-v2/tests','-p','test_*.py'],clean,env)
    config=json.loads((out/'assets/hf-transport-fixture/config.json').read_text())
    if config.get('model_type')!='bert':raise ValueError('Fixture parse failed')
    version=subprocess.check_output([py,'-c','import huggingface_hub;print(huggingface_hub.__version__)'],env=env,text=True).strip()
    receipt={'complete':True,'source_commit':actual,'client_version':version,'clean_git_checkout':True,
             'pinned_fixture_manifest':json.loads((clean/'assets/transport-fixture.json').read_text()),
             'private_project_assets_verified':False,'limitation':'HF project authentication/asset upload pending; this verifies transport and execution plumbing only.',
             'elapsed_seconds':time.monotonic()-started,'credentials_used':False}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    # Remove only disposable directories created by this job; retain receipts and logs.
    for name in ['clean-code','tool-env','hf-home','cache','assets']:
        p=out/name
        if p.is_dir() and not p.is_symlink():shutil.rmtree(p)
    mark(5,'clean remote transport smoke complete')
    print(json.dumps({'complete':True,'client_version':version,'private_project_assets_verified':False}))

if __name__=='__main__':main()
