"""Hash selected existing c225 assets in bounded memory; never copies/evaluates them."""
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import time


def expired(*_):raise TimeoutError('per-file hash deadline')


def main():
    if socket.gethostname().split('.')[0]!='c225':raise ValueError('c225 inputs required')
    base=Path('/date/zyy/macrohft-reproduction');out=Path(os.environ['CQ_OUTPUT_DIR'])
    out.mkdir(parents=True,exist_ok=True);signal.signal(signal.SIGALRM,expired)
    manifest=json.loads((Path(__file__).resolve().parents[1]/'assets/manifest.json').read_text())
    selected=[a for a in manifest['assets'] if a['id']!='cost-memory-data']
    entries=[(a['id'],f) for a in selected for f in a['files']]
    records=[];started=time.monotonic()
    for i,(asset,f) in enumerate(entries):
        (out/'progress.log').write_text(f'{i}/{len(entries)} hashing {asset}\n')
        r={'asset':asset,'path':f['path'],'source_path':f['source_path']}
        try:
            signal.alarm(60)
            p=base/f['source_path']
            if not p.resolve().is_relative_to(base.resolve()):raise ValueError('Unsafe source')
            before=p.stat();h=hashlib.sha256()
            with p.open('rb') as stream:
                for chunk in iter(lambda:stream.read(1024**2),b''):h.update(chunk)
            after=p.stat()
            if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise ValueError('Source changed')
            r.update(size=after.st_size,sha256=h.hexdigest())
            r['matches_manifest']=(f.get('sha256') is None or f['sha256']==r['sha256']) and (f.get('size') is None or f['size']==r['size'])
        except Exception as e:r['error']=type(e).__name__
        finally:signal.alarm(0)
        records.append(r)
    report={'complete':True,'source_commit':os.environ['SOURCE_COMMIT'],'root':str(base),'files':records,
            'bytes_read':sum(r.get('size',0) for r in records),'elapsed_seconds':time.monotonic()-started,
            'training_or_evaluation':False,'originals_modified':False}
    (out/'hashes.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'progress.log').write_text(f'{len(records)}/{len(entries)} complete\n')
    print(json.dumps({'complete':True,'checked':len(records),'errors':sum('error' in r for r in records),'mismatches':sum(r.get('matches_manifest') is False for r in records)}))

if __name__=='__main__':main()
