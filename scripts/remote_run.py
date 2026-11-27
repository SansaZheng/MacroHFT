"""Create an isolated remote run from committed code and verified, pinned assets."""
import argparse
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
from assets import ROOT, read, safe, save, select, verify_file, storage_root


def prepare(manifest, asset_root, work):
    required=['eth-prepared','feature-definitions','released-experts']
    selected=select(manifest,required)
    for a in selected:
        for f in a['files']:verify_file(safe(asset_root,a['id']+'/'+f['path']),f)
    if any(work.iterdir()):raise ValueError('Run directory must be empty; preserve previous runs')
    sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    # Archive current committed code only. Never copy .git, virtualenvs or untracked files.
    archive=subprocess.check_output(['git','archive',sha],cwd=ROOT)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        for member in tar.getmembers():
            safe(work,member.name)
            if member.issym() or member.islnk() or not (member.isfile() or member.isdir()):
                raise ValueError('Unexpected archive entry')
        tar.extractall(work)
    for a in selected:
        for f in a['files']:
            if f.get('role') == 'documentation': continue
            target=safe(work,f['runtime_path']);target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists():raise ValueError('Code tree unexpectedly contains an asset')
            target.symlink_to(safe(asset_root,a['id']+'/'+f['path']))
    save(work/'run-inputs.json',{'code_commit':sha,'assets':[{k:a[k] for k in ['id','repo_id','repo_type','revision']} for a in selected]})
    return sha


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',default=ROOT/'assets/manifest.json',type=Path)
    p.add_argument('--asset-root');p.add_argument('--work-dir',required=True)
    p.add_argument('--check-only',action='store_true')
    p.add_argument('--variant',choices=['reference','combined','action_memory','cost_aligned'],default='reference')
    p.add_argument('--seed',type=int,default=12345);p.add_argument('--epochs',type=int,default=1)
    p.add_argument('--device',default='cpu')
    a=p.parse_args();work=storage_root(a.work_dir,'MACROHFT_WORK_DIR')
    prepare(read(a.manifest),storage_root(a.asset_root,'MACROHFT_ASSET_ROOT'),work)
    if a.check_only:
        subprocess.run([sys.executable,str(work/'tests/test_reproduction.py')],cwd=work,check=True)
    else:
        # Original runner already uses --skip_test. No held-out evaluation is exposed here.
        subprocess.run([sys.executable,str(work/'scripts/run_experiment.py'),'--variant',a.variant,
                        '--seed',str(a.seed),'--epochs',str(a.epochs),'--device',a.device],cwd=work,check=True)
