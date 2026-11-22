"""Own one trial in a private project directory; never change external jobs."""
import argparse,datetime,fcntl,hashlib,json,os,pathlib,shutil,subprocess,sys,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--variant',required=True,choices=['reference','combined','action_memory','cost_aligned']);p.add_argument('--seed',required=True,type=int);args=p.parse_args()
if not str(ROOT).startswith(('/date/zyy/','/data/zyy/')):raise SystemExit('Project must be under /date/zyy or /data/zyy')
if ROOT.stat().st_uid!=os.getuid():raise SystemExit('Project ownership mismatch')
folder=ROOT/'results'/f'{args.variant}-seed{args.seed}';folder.mkdir(parents=True,exist_ok=True)
lock=(folder/'worker.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
status={'host':os.uname().nodename,'root':str(ROOT),'wrapper_pid':os.getpid(),'variant':args.variant,'seed':args.seed,'started_at':datetime.datetime.now().astimezone().isoformat(),'status':'starting'}
def write():
 t=folder/'worker-status.tmp';t.write_text(json.dumps(status,indent=2));t.replace(folder/'worker-status.json')
try:
 if (folder/'completed.json').exists():
  status['status']='completed_existing';write();sys.exit(0)
 if (folder/'train.log').exists() or (folder/'validation.jsonl').exists():raise RuntimeError('Existing partial trial preserved; explicit recovery required')
 if shutil.disk_usage(ROOT).free<60*1024**3:raise RuntimeError('Insufficient storage headroom: require 60 GiB free')
 env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',PYTHONNOUSERSITE='1',TMPDIR=str(ROOT/'tmp'),PIP_CACHE_DIR=str(ROOT/'cache/pip'))
 (ROOT/'tmp').mkdir(exist_ok=True)
 command=[sys.executable,'-u',str(ROOT/'scripts/run_experiment.py'),'--variant',args.variant,'--seed',str(args.seed),'--device','cpu']
 with (folder/'train.log').open('x') as log:
  child=subprocess.Popen(command,cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
  status.update(status='running',training_pid=child.pid,command=command);write()
  code=child.wait()
 status.update(status='completed' if code==0 and (folder/'completed.json').exists() else 'failed',exit_code=code,finished_at=datetime.datetime.now().astimezone().isoformat());write()
 if status['status']!='completed':sys.exit(code or 1)
except Exception as exc:
 status.update(status='failed',error=repr(exc));write();raise
