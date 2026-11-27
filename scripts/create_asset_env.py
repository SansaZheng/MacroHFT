"""Create a disposable job-local asset client environment without distro ensurepip."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request

ROOT=Path(__file__).resolve().parents[1]


def create(destination, python=sys.executable):
    destination=Path(destination).resolve()
    if not destination.is_absolute() or destination==ROOT or ROOT in destination.parents:
        raise ValueError('Use an absolute environment directory outside the code checkout')
    if destination.exists():raise FileExistsError('Preserve existing environment; choose a fresh path')
    destination.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run([python,'-m','venv','--copies','--without-pip',str(destination)],check=True,timeout=60)
    env=dict(os.environ,PIP_CACHE_DIR=str(destination/'cache'),PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1')
    env.pop('PYTHONPATH',None);env.pop('PYTHONHOME',None);env.pop('PIP_EXTRA_INDEX_URL',None)
    metadata=json.loads((ROOT/'requirements/bootstrap-pip.json').read_text())
    with urllib.request.urlopen(metadata['url'],timeout=45) as response:content=response.read(metadata['size']+1)
    if len(content)!=metadata['size'] or hashlib.sha256(content).hexdigest()!=metadata['sha256']:
        raise ValueError('Official pip bootstrap identity mismatch')
    script=destination/'get-pip.py';script.write_bytes(content)
    py=destination/'bin/python'
    subprocess.run([str(py),str(script),'pip=='+metadata['pip_version'],'--no-cache-dir','--index-url','https://pypi.org/simple'],env=env,check=True,timeout=180)
    script.unlink()  # only the temporary file created by this invocation
    subprocess.run([str(py),'-m','pip','install','--no-cache-dir','--index-url','https://pypi.org/simple','-r',str(ROOT/'requirements/assets.txt')],env=env,check=True,timeout=240)
    return py


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',required=True);p.add_argument('--python',default=sys.executable)
    a=p.parse_args();print(create(a.root,a.python))
