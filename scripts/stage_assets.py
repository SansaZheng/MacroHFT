"""Stage explicitly selected legacy assets on a remote disk without altering originals."""
import argparse
import gzip
import hashlib
import os
from pathlib import Path
import shutil
import sys
import urllib.request
from assets import read, safe, validate, verify_file, storage_root


def stage(manifest, ids, legacy_root, destination):
    selected=[a for a in manifest['assets'] if a['id'] in ids]
    if len(selected)!=len(set(ids)): raise ValueError('Unknown/duplicate asset selection')
    count=0
    for a in selected:
        for f in a['files']:
            if f.get('sha256') is None: raise ValueError('Inventory/hash pending: '+f['path'])
            source=safe(legacy_root,f['source_path']);target=safe(destination,f['path'])
            verify_file(source,f)
            if target.exists():verify_file(target,f)
            else:
                target.parent.mkdir(parents=True,exist_ok=True)
                # Copy rather than link mutable legacy checkpoints into the upload staging tree.
                with source.open('rb') as inp,target.open('xb') as out:shutil.copyfileobj(inp,out,1024**2)
                verify_file(target,f)
            count+=1
    return count


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',default=str(Path(__file__).resolve().parents[1]/'assets/manifest.json'))
    p.add_argument('--asset',action='append',required=True)
    p.add_argument('--legacy-root',required=True);p.add_argument('--root',required=True)
    a=p.parse_args()
    print({'staged_files':stage(validate(read(a.manifest)),a.asset,Path(a.legacy_root),storage_root(a.root,'MACROHFT_STAGE_ROOT'))})
