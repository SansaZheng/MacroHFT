"""Verify fetched Git objects against the archive SHA-256 manifest without checkout.

Use a fresh bare clone of the remote to establish retrieval, not the producer's
working tree. Decompressed originals are checked by restore_archive.py before
push; identical remote part hashes establish identical stored gzip streams.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


def verify(repo, ref):
    if not re.fullmatch(r'[0-9a-f]{40}', ref):
        raise ValueError('Use an exact full commit SHA')
    base = ['git', '--git-dir='+str(repo)]
    actual = subprocess.check_output(base+['rev-parse', ref+'^{commit}'], text=True).strip()
    if actual != ref: raise ValueError('Commit mismatch')
    manifest = json.loads(subprocess.check_output(base+['show',ref+':data-archive/manifest.json']))
    objects = []; pending = []; originals = 0; original_bytes = 0
    for entry in manifest['files']:
        if entry['storage']=='pending': pending.append(entry['path']); continue
        originals += 1; original_bytes += entry['size']
        if entry['storage']=='git': objects.append(entry)
        elif entry['storage']=='gzip-parts': objects.extend(entry['parts'])
        else: raise ValueError('Unknown storage')
    verified_bytes = 0
    for i, entry in enumerate(objects):
        p=subprocess.Popen(base+['cat-file','blob',ref+':'+entry['path']],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        h=hashlib.sha256(); n=0
        for block in iter(lambda:p.stdout.read(1024**2),b''):
            h.update(block); n += len(block)
        error=p.stderr.read(); rc=p.wait()
        if rc or n!=entry['size'] or h.hexdigest()!=entry['sha256']:
            raise ValueError('Invalid remote object '+entry['path']+': '+error.decode(errors='replace')[:200])
        verified_bytes += n
        if (i+1)%50==0: print(f'{i+1}/{len(objects)} Git objects verified',flush=True)
    return {'commit':ref,'verified_git_objects':len(objects),'verified_stored_bytes':verified_bytes,
            'represented_original_files':originals,'represented_original_bytes':original_bytes,
            'pending_files':len(pending),'complete_local_snapshot':manifest.get('complete_local_snapshot',False) and not pending,
            'remote_training_artifacts_retrieved':manifest['remote_training_artifacts_retrieved'],
            'verification':'SHA-256 of actual objects from a separate Git clone; no training or evaluation'}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--git-dir',type=Path,required=True)
    ap.add_argument('--commit',required=True);ap.add_argument('--receipt',type=Path)
    a=ap.parse_args();result=verify(a.git_dir,a.commit)
    if a.receipt:a.receipt.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)
