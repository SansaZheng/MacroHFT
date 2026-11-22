"""Read worker state; this file is sent over SSH stdin by the controller."""
import json,pathlib,os,sys
root=pathlib.Path(sys.argv[1]);answer={}
for name in sys.argv[2:]:
 folder=root/'results'/name
 info={'root':str(root),'completed':(folder/'completed.json').exists()}
 status=folder/'worker-status.json'
 if status.exists():
  info.update(json.loads(status.read_text()))
  pid=info.get('training_pid')
  if pid:
   p=pathlib.Path('/proc')/str(pid)/'cmdline'
   info['training_alive']=p.exists() and str(root).encode() in p.read_bytes()
 log=folder/'train.log'
 if log.exists():
  with log.open('rb') as f:
   f.seek(max(0,log.stat().st_size-3000));info['recent_log']=f.read().decode(errors='replace')
 rows=folder/'validation.jsonl'
 if rows.exists():
  values=[json.loads(x) for x in rows.read_text().splitlines()]
  info['epochs_validated']=len(values);info['latest_validation']=values[-1] if values else None
 answer[name]=info
print(json.dumps(answer))
