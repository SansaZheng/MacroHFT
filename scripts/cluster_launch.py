"""Launch two assigned trials using only the private project runtime."""
import json,os,pathlib,shutil,subprocess,sys
root=pathlib.Path(sys.argv[1]);jobs=json.loads(sys.argv[2]);output={}
if root.stat().st_uid!=os.getuid():raise SystemExit('Wrong project owner')
if (root/'.macrohft-project').read_text().strip()!='macrohft-2026-10-02':raise SystemExit('Wrong project marker')
if shutil.disk_usage(root).free<60*1024**3:raise SystemExit('Less than 60 GiB free')
if not (root/'results/setup-verified.json').exists():raise SystemExit('Worker tests not verified')
for variant,seed in jobs:
 if variant not in ['reference','combined','action_memory','cost_aligned'] or seed not in [12345,2024,42]:raise SystemExit('Unregistered trial')
 name=f'{variant}-seed{seed}';folder=root/'results'/name;folder.mkdir(parents=True,exist_ok=True)
 record=folder/'launch.json'
 if (folder/'completed.json').exists():output[name]={'status':'completed_existing'};continue
 if record.exists():
  old=json.loads(record.read_text());p=pathlib.Path('/proc')/str(old['pid'])/'cmdline'
  if p.exists() and str(root).encode() in p.read_bytes():output[name]=old;continue
  raise SystemExit(f'Prior launch record exists for {name}; refusing to overwrite or relaunch')
 with (folder/'wrapper.log').open('a') as log:
  child=subprocess.Popen(['nice','-n','10',str(root/'.venv/bin/python'),'-u',str(root/'scripts/cluster_worker.py'),'--variant',variant,'--seed',str(seed)],cwd=root,env={**os.environ,'PYTHONNOUSERSITE':'1'},stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 info={'pid':child.pid,'root':str(root),'status':'launched','variant':variant,'seed':seed}
 record.write_text(json.dumps(info,indent=2));output[name]=info
print(json.dumps(output))
