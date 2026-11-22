"""Distribute fixed trials, adopt existing workers, and retain sealed test selection."""
import argparse,concurrent.futures,datetime,fcntl,hashlib,json,math,os,pathlib,shlex,signal,subprocess,sys,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
PLAN=json.loads((ROOT/'scripts/cluster_plan.json').read_text())
RESULT=ROOT/'results'
VARIANTS=PLAN['variants'];SEEDS=PLAN['seeds']
STATUS={'pid':os.getpid(),'phase':'cluster_starting','started_at':datetime.datetime.now().astimezone().isoformat(),'device':'cpu','workers':10,'jobs':{},'selection':None,'plan_revision':PLAN['revision']}
ADOPTED={};SYNCED=set();CANCELLED=set();OWNERSHIP=False


def atomic(path,data):
 path=pathlib.Path(path);tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(data,indent=2));tmp.replace(path)


def write():
 STATUS['updated_at']=datetime.datetime.now().astimezone().isoformat();atomic(RESULT/'pipeline-status.json',STATUS)


def alive(pid,needle):
 p=pathlib.Path('/proc')/str(pid)/'cmdline'
 return p.exists() and needle.encode() in p.read_bytes()


def remote_python(host,code,args=(),timeout=60):
 command='python3 - '+ ' '.join(shlex.quote(str(x)) for x in args)
 r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10',host,command],input=code,text=True,capture_output=True,timeout=timeout,check=True)
 return json.loads(r.stdout)


def choose_candidate(scores):
 if set(scores)!=set(VARIANTS) or not all(math.isfinite(v) for v in scores.values()):raise ValueError('Incomplete or nonfinite validation scores')
 return max([v for v in VARIANTS if v!='reference'],key=lambda v:scores[v])


def adopt_old(pid,recover=False):
 old=json.loads((RESULT/'pipeline-status.json').read_text())
 if old['pid']!=pid or old['phase']!='training_candidates':raise RuntimeError('Old coordinator changed; inspect before handoff')
 if recover:
  handoff=json.loads((RESULT/'cluster/handoff.json').read_text())
  if handoff['old_status']!=old:raise RuntimeError('Handoff snapshot changed')
  if alive(pid,str(ROOT)) or alive(handoff['new_controller_pid'],str(ROOT)):raise RuntimeError('A previous coordinator is still alive')
  for key,child in handoff['adopted_pids'].items():
   if not alive(child,str(ROOT/'scripts/run_experiment.py')):raise RuntimeError(f'Adopted trial {key} is no longer alive')
   proc=pathlib.Path('/proc')/str(child)
   args=(proc/'cmdline').read_bytes().split(bytes([0]));variant,seed=key.rsplit('-seed',1)
   if proc.stat().st_uid!=os.getuid() or args[args.index(b'--variant')+1].decode()!=variant or args[args.index(b'--seed')+1].decode()!=seed:raise RuntimeError('Adopted trial ownership/arguments mismatch')
  ADOPTED.update(handoff['adopted_pids'])
  atomic(RESULT/'cluster/handoff-recovery.json',{'previous_handoff':handoff,'new_controller_pid':os.getpid(),'timestamp':datetime.datetime.now().astimezone().isoformat()})
  return
 if not alive(pid,str(ROOT/'scripts/experiment_pipeline.py')):raise RuntimeError('Old coordinator identity mismatch')
 if pathlib.Path('/proc',str(pid)).stat().st_uid!=os.getuid():raise RuntimeError('Coordinator ownership mismatch')
 expected={f'{v}-seed12345' for v in VARIANTS}
 if set(old['jobs'])!=expected:raise RuntimeError('Unexpected old workers; refusing handoff')
 for key,j in old['jobs'].items():
  if j['status']=='completed':
   if not (RESULT/key/'completed.json').exists():raise RuntimeError('Completed trial artifact missing')
   continue
  if j['status']!='running' or not alive(j['pid'],str(ROOT/'scripts/run_experiment.py')):raise RuntimeError('Existing training worker identity mismatch')
  ADOPTED[key]=j['pid']
 atomic(RESULT/'cluster/handoff.json',{'old_status':old,'adopted_pids':ADOPTED,'new_controller_pid':os.getpid(),'timestamp':datetime.datetime.now().astimezone().isoformat(),'action':'Terminate only the scheduling parent; preserve existing training children'})
 os.kill(pid,signal.SIGTERM)
 for _ in range(50):
  if not alive(pid,str(ROOT/'scripts/experiment_pipeline.py')):break
  time.sleep(0.1)
 else:raise RuntimeError('Old coordinator did not exit; no forced kill attempted')
 for key,pid in ADOPTED.items():
  if not alive(pid,str(ROOT/'scripts/run_experiment.py')):raise RuntimeError(f'Adopted worker {key} unexpectedly disappeared')


def query_host(item):
 host,entry=item;names=[f'{v}-seed{s}' for v,s in entry['jobs']]
 if host=='c225':
  r=subprocess.run([sys.executable,str(ROOT/'scripts/cluster_query.py'),str(ROOT),*names],capture_output=True,text=True,check=True,timeout=30)
  data=json.loads(r.stdout)
  for name,j in data.items():
   pid=ADOPTED.get(name);j.update(training_pid=pid,training_alive=bool(pid and alive(pid,str(ROOT/'scripts/run_experiment.py'))))
   j['status']='completed' if j['completed'] else 'running' if j['training_alive'] else 'failed'
  return host,data
 code=(ROOT/'scripts/cluster_query.py').read_text()
 return host,remote_python(host,code,[entry['root'],*names])


def sync_job(host,entry,key):
 if key in SYNCED:return
 if host!='c225':
  variant,seed=key.rsplit('-seed',1)
  paths=[(f'results/{key}',f'results/{key}'),(f'vendor/MacroHFT/result/high_level/ETHUSDT/{variant}/seed_{seed}',f'vendor/MacroHFT/result/high_level/ETHUSDT/{variant}/seed_{seed}')]
  for src,dst in paths:
   target=ROOT/dst;target.mkdir(parents=True,exist_ok=True)
   subprocess.run(['rsync','-a','--bwlimit=60000',f'{host}:{entry["root"]}/{src}/',str(target)+'/'],check=True,timeout=180)
 SYNCED.add(key)


def validation_scores():
 scores={}
 for variant in VARIANTS:
  file=RESULT/f'{variant}-seed12345'/'validation.jsonl'
  rows=[json.loads(x) for x in file.read_text().splitlines()]
  if len(rows)!=15:raise RuntimeError(f'{variant}: expected 15 epochs, got {len(rows)}')
  scores[variant]=max(r['return_pct'] if r['return_pct'] is not None else 0.0 for r in rows)
 return scores


def freeze_selection():
 scores=validation_scores();chosen=choose_candidate(scores)
 selection={'selected_variant':chosen,'validation_return_pct':scores,'criterion':'maximum full-validation return over 15 epochs on seed 12345 only; tie order combined, action_memory, cost_aligned','test_used_for_selection':False,'additional_seed_scores_used_for_selection':False,'seeds':SEEDS,'frozen_at':datetime.datetime.now().astimezone().isoformat()}
 for v in ['reference',chosen]:
  checkpoint=ROOT/f'vendor/MacroHFT/result/high_level/ETHUSDT/{v}/seed_12345/best_model.pkl'
  selection[v+'_checkpoint_sha256']=hashlib.sha256(checkpoint.read_bytes()).hexdigest()
 if (RESULT/'selection-frozen.json').exists():raise RuntimeError('A selection already exists; do not overwrite it')
 atomic(RESULT/'selection-frozen.json',selection);STATUS['selection']=selection;STATUS['phase']='waiting_for_selected_seeds';write()
 return chosen


def cancel_unused(key,job,chosen):
 if key in CANCELLED or job.get('completed'):return
 variant,seed=key.rsplit('-seed',1)
 if variant in ('reference',chosen) or int(seed)==12345:raise RuntimeError('Refusing cancellation of a required trial')
 code=r'''
import json,os,pathlib,signal,sys
root=pathlib.Path(sys.argv[1]);key=sys.argv[2];chosen=sys.argv[3]
variant,seed=key.rsplit('-seed',1)
assert variant not in ('reference',chosen) and seed in ('2024','42')
folder=root/'results'/key
if (folder/'completed.json').exists():print(json.dumps({'cancelled':False,'already_completed':True}));sys.exit(0)
j=json.loads((folder/'worker-status.json').read_text());pid=j['training_pid'];proc=pathlib.Path('/proc')/str(pid)
if not proc.exists():print(json.dumps({'cancelled':False,'already_exited':True}));sys.exit(0)
args=(proc/'cmdline').read_bytes().split(bytes([0]));assert proc.stat().st_uid==os.getuid()
assert str(root/'scripts/run_experiment.py').encode() in args
assert args[args.index(b'--variant')+1].decode()==variant
assert args[args.index(b'--seed')+1].decode()==seed
(folder/'cancel-request.json').write_text(json.dumps({'reason':'Unselected speculative seed; validation selection frozen before test','selected_variant':chosen,'pid':pid}))
os.kill(pid,signal.SIGTERM)
print(json.dumps({'cancelled':True,'pid':pid}))
'''
 result=remote_python(job['host'],code,[job['root'],key,chosen]);CANCELLED.add(key)
 STATUS['jobs'][key].update(status='cancelled_unselected',cancellation=result)


def evaluate_final(chosen):
 STATUS['phase']='sealed_test_evaluation';write();rows=[]
 for seed in SEEDS:
  for variant in ['reference',chosen]:
   key=f'{variant}-seed{seed}';folder=RESULT/key
   checkpoint=ROOT/f'vendor/MacroHFT/result/high_level/ETHUSDT/{variant}/seed_{seed}/best_model.pkl'
   if (folder/'test/metrics.json').exists():raise RuntimeError(f'{key} test already exists; refusing repeated test')
   command=[sys.executable,'-u',str(ROOT/'scripts/run_experiment.py'),'--variant',variant,'--seed',str(seed),'--evaluate',str(checkpoint),'--split','test']
   with (folder/'test.log').open('x') as log:subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True,cwd=ROOT)
   metrics=json.loads((folder/'test/metrics.json').read_text());rows.append({'variant':variant,'seed':seed,**metrics})
 import numpy as np
 aggregate={}
 for variant in ['reference',chosen]:
  values=np.array([r['return_pct'] if r['return_pct'] is not None else 0.0 for r in rows if r['variant']==variant])
  aggregate[variant]={'mean_return_pct':float(values.mean()),'sample_std_return_pct':float(values.std(ddof=1)),'seed_returns_pct':values.tolist(),'seeds':len(values)}
 summary={'status':'completed','scope':'ETH hyper-agent retraining using six authors-released subagent checkpoints; other markets and from-scratch subagent training remain unreproduced','selection':STATUS['selection'],'published_eth_return_pct':39.28,'test_results':rows,'aggregate':aggregate,'candidate_mean_exceeds_published':aggregate[chosen]['mean_return_pct']>39.28,'candidate_mean_exceeds_reproduced_reference':aggregate[chosen]['mean_return_pct']>aggregate['reference']['mean_return_pct'],'completed_at':datetime.datetime.now().astimezone().isoformat(),'comparability_warning':'Same date splits and simulator fee. Simulator uses ex-post required capital; released expert training provenance and feature generation are not independently reconstructed. New hosts use a private PyTorch 2.8 CPU build; original c225 trials retain their running runtime. Additional seed scores were excluded from candidate selection. Seed dispersion is not statistical significance.'}
 atomic(RESULT/'final-summary.json',summary);STATUS['phase']='completed';write()


def main():
 global OWNERSHIP
 p=argparse.ArgumentParser();p.add_argument('--adopt-coordinator',required=True,type=int);p.add_argument('--recover-handoff',action='store_true');a=p.parse_args()
 if str(ROOT)!=PLAN['coordinator_root']:raise RuntimeError('Wrong coordinator project root')
 for host,entry in PLAN['hosts'].items():
  if host!='c225':
   receipt=json.loads((RESULT/f'cluster/setup-{host}.json').read_text())
   if receipt['status']!='verified':raise RuntimeError(f'{host} has not passed setup tests')
 if (RESULT/'final-summary.json').exists() or (RESULT/'selection-frozen.json').exists():raise RuntimeError('Selection/test already exists; manual recovery required')
 adopt_old(a.adopt_coordinator,a.recover_handoff)
 lock=(RESULT/'pipeline.lock').open('a')
 for attempt in range(100):
  try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);break
  except BlockingIOError:
   if attempt==99:raise
   time.sleep(0.1)
 OWNERSHIP=True
 STATUS['adopted_training_pids']=ADOPTED;STATUS['phase']='distributed_training';write()
 code=(ROOT/'scripts/cluster_launch.py').read_text()
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
  futures={pool.submit(remote_python,h,code,[e['root'],json.dumps(e['jobs'])]):h for h,e in PLAN['hosts'].items() if h!='c225'}
  for future in concurrent.futures.as_completed(futures):
   host=futures[future];atomic(RESULT/f'cluster/launch-{host}.json',future.result())
 chosen=None
 while True:
  with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
   futures={pool.submit(query_host,item):item[0] for item in PLAN['hosts'].items()}
   for future in concurrent.futures.as_completed(futures):
    host=futures[future]
    try:
     _,data=future.result()
     for key,j in data.items():
      j.update(host=host,log=f'{PLAN["hosts"][host]["root"]}/results/{key}/train.log',pid=j.get('training_pid'),process_alive=j.get('training_alive',False))
      if key in CANCELLED:j['status']='cancelled_unselected'
      STATUS['jobs'][key]=j
      if j.get('completed'):sync_job(host,PLAN['hosts'][host],key)
    except Exception as exc:
     STATUS.setdefault('connection_errors',{})[host]={'error':repr(exc),'time':datetime.datetime.now().astimezone().isoformat()}
  write()
  if chosen is None and all(f'{v}-seed12345' in SYNCED for v in VARIANTS):chosen=freeze_selection()
  if chosen is not None:
   for key,j in list(STATUS['jobs'].items()):
    v,seed=key.rsplit('-seed',1)
    if v not in ('reference',chosen) and int(seed)!=12345 and not j.get('completed') and key not in CANCELLED:
     try:cancel_unused(key,j,chosen)
     except Exception as exc:STATUS.setdefault('cancellation_errors',{})[key]=repr(exc)
   required={f'{v}-seed{s}' for s in SEEDS for v in ['reference',chosen]}
   if required<=SYNCED:break
  failures=[key for key,j in STATUS['jobs'].items() if j.get('status')=='failed' and key not in CANCELLED]
  if failures:raise RuntimeError(f'Trials failed; preserve logs for diagnosis: {failures}')
  time.sleep(30)
 evaluate_final(chosen)

if __name__=='__main__':
 try:main()
 except Exception as exc:
  STATUS.update(phase='failed',error=repr(exc))
  if OWNERSHIP:write()
  else:atomic(RESULT/'cluster/start-failure.json',STATUS)
  raise
