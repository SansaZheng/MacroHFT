"""Prepare private workers; no mutation of their existing environments."""
import concurrent.futures,hashlib,json,os,pathlib,shlex,subprocess,sys,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
PLAN=json.loads((ROOT/'scripts/cluster_plan.json').read_text())
RESULT=ROOT/'results/cluster';RESULT.mkdir(exist_ok=True)
INIT=r'''
import pathlib,os,shutil,sys,json
root=pathlib.Path(sys.argv[1])
if not str(root).startswith(('/date/zyy/','/data/zyy/')):raise SystemExit('Invalid storage root')
parent=root.parent
if not parent.exists():parent.mkdir()
if not os.access(parent,os.W_OK):raise SystemExit('Parent is not writable')
if shutil.disk_usage(parent).free<60*1024**3:raise SystemExit('Require 60 GiB free space')
if root.exists() and not (root/'.macrohft-project').exists():raise SystemExit('Existing unmarked directory: preserved')
root.mkdir(mode=0o700,exist_ok=True)
if root.stat().st_uid!=os.getuid():raise SystemExit('Project not owned by current user')
marker=root/'.macrohft-project'
if marker.exists() and marker.read_text().strip()!='macrohft-2026-10-02':raise SystemExit('Different project marker')
marker.write_text('macrohft-2026-10-02\n')
for name in ['tmp','cache','results','scripts','incoming']:(root/name).mkdir(exist_ok=True)
print(json.dumps({'uid':os.getuid(),'root':str(root),'free_bytes':shutil.disk_usage(root).free}))
'''
def prepare(item):
 host,entry=item;dest=entry['root'];log=RESULT/f'setup-{host}.log';start=time.time()
 try:
  with log.open('a') as out:
   subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10',host,'python3','-',dest],input=INIT,text=True,stdout=out,stderr=subprocess.STDOUT,check=True,timeout=30)
   for artifact in ['runtime-isolated.tar.gz','worker-source.tar.gz']:
    subprocess.run(['rsync','-a','--bwlimit=60000',str(ROOT/'cluster'/artifact),f'{host}:{dest}/incoming/'],stdout=out,stderr=subprocess.STDOUT,check=True,timeout=600)
   expected={name:hashlib.sha256((ROOT/'cluster'/name).read_bytes()).hexdigest() for name in ['runtime-isolated.tar.gz','worker-source.tar.gz']}
   verify='import hashlib,json,pathlib,sys; r=pathlib.Path(sys.argv[1]); e=json.loads(sys.argv[2]); assert all(hashlib.sha256((r/"incoming"/n).read_bytes()).hexdigest()==v for n,v in e.items()); print("archive hashes verified")'
   subprocess.run(['ssh',host,'python3','-c',shlex.quote(verify),shlex.quote(dest),shlex.quote(json.dumps(expected))],stdout=out,stderr=subprocess.STDOUT,check=True,timeout=60)
   command=f'cd {shlex.quote(dest)} && mkdir -p .venv && tar -xzf incoming/runtime-isolated.tar.gz -C .venv && PYTHONNOUSERSITE=1 .venv/bin/python .venv/bin/conda-unpack && tar -xzf incoming/worker-source.tar.gz && PYTHONNOUSERSITE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 TMPDIR={shlex.quote(dest)}/tmp .venv/bin/python -I tests/test_reproduction.py > results/setup-tests.log 2>&1 && .venv/bin/python -I -m pip freeze > results/environment.txt'
   subprocess.run(['ssh',host,command],stdout=out,stderr=subprocess.STDOUT,check=True,timeout=600)
   final=r'''import pathlib,json,shutil,sys,os,platform,datetime
r=pathlib.Path(sys.argv[1]);text=(r/'results/setup-tests.log').read_text();assert 'Ran 10 tests' in text and 'OK' in text.splitlines();assert shutil.disk_usage(r).free>60*1024**3
import importlib
modules={name:str(pathlib.Path(importlib.import_module(name).__file__).resolve()) for name in ['numpy','pandas','torch','scipy','sklearn','pyarrow','numba','tensorboard','gym','yaml','joblib']}
assert all(path.startswith(str(r/'.venv')+'/') for path in modules.values()),modules
info={'module_paths':modules,'status':'verified','host':os.uname().nodename,'root':str(r),'python':sys.version,'platform':platform.platform(),'free_bytes':shutil.disk_usage(r).free,'verified_at':datetime.datetime.now().astimezone().isoformat(),'tests':10}
(r/'results/setup-verified.json').write_text(json.dumps(info,indent=2));print(json.dumps(info))'''
   verified=subprocess.check_output(['ssh',host,f'{dest}/.venv/bin/python','-I','-',dest],input=final,text=True,timeout=30)
   data=json.loads(verified);data['elapsed_seconds']=time.time()-start;data['alias']=host
   (RESULT/f'setup-{host}.json').write_text(json.dumps(data,indent=2));return data
 except Exception as exc:
  data={'status':'failed','host':host,'error':repr(exc),'log':str(log)};(RESULT/f'setup-{host}.json').write_text(json.dumps(data,indent=2));return data

if __name__=='__main__':
 workers=[(h,e) for h,e in PLAN['hosts'].items() if not e.get('adopt_existing')]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  for result in pool.map(prepare,workers):print(json.dumps(result),flush=True)
