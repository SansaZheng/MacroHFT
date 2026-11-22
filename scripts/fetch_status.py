"""Refresh the local status snapshot from the authorized experiment server."""
import datetime
import json
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]
REMOTE=r'''
import json,pathlib,datetime
root=pathlib.Path('/date/zyy/macrohft-reproduction')
p=root/'results/pipeline-status.json'
status=json.loads(p.read_text())
status['verified_at']=datetime.datetime.now().astimezone().isoformat()
proc=pathlib.Path('/proc')/str(status['pid'])/'cmdline'
status['coordinator_alive']=proc.exists() and str(root).encode() in proc.read_bytes()
for key,job in status['jobs'].items():
 if job.get('log') and job.get('host','c225')=='c225':
  log=pathlib.Path(job['log'])
  job['recent_log']=log.read_text()[-2200:] if log.exists() else ''
  pid=job.get('pid')
  if pid:
   proc=pathlib.Path('/proc')/str(pid)/'cmdline'
   job['process_alive']=proc.exists() and str(root).encode() in proc.read_bytes()
artifacts={}
for name in ['selection-frozen.json','final-summary.json']:
 p=root/'results'/name
 if p.exists():artifacts[name]=json.loads(p.read_text())
print(json.dumps({'status':status,'artifacts':artifacts}))
'''
r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','c225','/date/zyy/macrohft-reproduction/.venv/bin/python','-'],input=REMOTE,text=True,capture_output=True,check=True,timeout=60)
payload=json.loads(r.stdout)
(ROOT/'results/pipeline-status.json').write_text(json.dumps(payload['status'],indent=2))
for name,data in payload['artifacts'].items():
 (ROOT/'results'/name).write_text(json.dumps(data,indent=2))
print(json.dumps(payload['status'],indent=2))
