"""Reject tracked binary assets, caches, credentials and oversized generated files."""
from pathlib import Path
import subprocess
import sys
BAD={'.feather','.parquet','.arrow','.npy','.npz','.pkl','.pt','.pth','.ckpt','.safetensors','.bin','.zip','.gzpart','.log','.png'}
paths=subprocess.check_output(['git','ls-files','-z']).decode().split('\0')
errors=[]
for name in filter(None,paths):
 p=Path(name)
 if p.suffix in BAD or any(x in p.parts for x in ['.venv','venv','.cache','__pycache__']) or p.name in ['.env','token','stored_tokens'] or 'events.out.tfevents' in name:errors.append(name)
 if p.is_file() and p.stat().st_size>2*1024**2:errors.append(name+' exceeds 2 MiB code/evidence limit')
if errors:
 print('\n'.join(errors),file=sys.stderr);sys.exit(1)
print('Git asset policy passed')
