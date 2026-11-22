import os,json,pathlib,signal,hashlib,socket,shutil
root=pathlib.Path('/date/zyy/macrohft-reproduction')
out=pathlib.Path(os.environ['CQ_OUTPUT_DIR'])
def alarm(*args): raise TimeoutError('bounded metadata read timed out')
signal.signal(signal.SIGALRM,alarm)
report={'host':socket.gethostname(),'root':str(root),'read_only_legacy':True,'files':{},'errors':{}}
(out/'progress.log').write_text('0/3 starting legacy inventory\n')
for name in ['results/pipeline-status.json','results/selection-frozen.json','results/final-summary.json','results/data-audit.json']:
 try:
  signal.alarm(5);p=root/name
  if not p.exists():report['files'][name]={'exists':False};continue
  n=p.stat().st_size
  if n>2*1024*1024:report['files'][name]={'exists':True,'bytes':n,'skipped':'size cap'};continue
  raw=p.read_bytes();report['files'][name]={'exists':True,'bytes':n,'sha256':hashlib.sha256(raw).hexdigest(),'data':json.loads(raw)}
 except Exception as e:report['errors'][name]=type(e).__name__+': '+str(e)
 finally:signal.alarm(0)
(out/'progress.log').write_text('1/3 result metadata checked\n')
try:
 signal.alarm(5);report['root_exists']=root.exists();report['free_bytes']=shutil.disk_usage(root).free if root.exists() else None;report['venv_python_exists']=(root/'.venv/bin/python').exists()
except Exception as e:report['errors']['root']=str(e)
finally:signal.alarm(0)
(out/'progress.log').write_text('2/3 storage checked\n')
report['matching_process_pids']=[]
for p in pathlib.Path('/proc').iterdir():
 if p.name.isdigit() and int(p.name)!=os.getpid():
  try:
   if p.stat().st_uid==os.getuid() and b'macrohft' in (p/'cmdline').read_bytes().lower():report['matching_process_pids'].append(int(p.name))
  except OSError:pass
report['inventory_complete']=True
(out/'inventory.json').write_text(json.dumps(report,indent=2))
(out/'progress.log').write_text('3/3 inventory complete\n')
print(json.dumps({'inventory_complete':True,'legacy_final_summary_exists':report['files'].get('results/final-summary.json',{}).get('exists'),'errors':report['errors']}))
