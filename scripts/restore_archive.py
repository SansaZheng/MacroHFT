"""Validate archived bytes and optionally restore large files without overwrites."""
import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile


def safe(root, name):
    p = (root / name).resolve()
    if not p.is_relative_to(root.resolve()):
        raise ValueError('Manifest path escapes root')
    return p


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024**2), b''): h.update(b)
    return h.hexdigest()


class PartsReader(io.RawIOBase):
    def __init__(self, root, parts):
        self.root, self.parts, self.handle = root, iter(parts), None
    def readable(self): return True
    def readinto(self, target):
        while True:
            if self.handle is None:
                part = next(self.parts, None)
                if part is None: return 0
                self.handle = safe(self.root, part['path']).open('rb')
            n = self.handle.readinto(target)
            if n: return n
            self.handle.close(); self.handle = None
    def close(self):
        if self.handle: self.handle.close()
        super().close()


def verify(root, destination=None, allow_partial=False):
    manifest = json.loads((root / 'data-archive/manifest.json').read_text())
    pending = [e['path'] for e in manifest['files'] if e['storage']=='pending']
    complete = manifest.get('complete_local_snapshot', False) and not pending
    if not complete and not allow_partial:
        raise ValueError('Archive is incomplete; some bytes remain pending')
    checked = 0
    for entry in manifest['files']:
        storage = entry['storage']
        if storage == 'pending': continue
        if storage == 'git':
            p = safe(root, entry['path'])
            if p.stat().st_size != entry['size'] or digest(p) != entry['sha256']:
                raise ValueError('Invalid file: ' + entry['path'])
        elif storage == 'gzip-parts':
            for part in entry['parts']:
                p = safe(root, part['path'])
                if p.stat().st_size != part['size'] or digest(p) != part['sha256']:
                    raise ValueError('Invalid part: ' + part['path'])
            tmp = None; out = None
            if destination:
                target = safe(destination, entry['path']); target.parent.mkdir(parents=True, exist_ok=True)
                fd, tmp = tempfile.mkstemp(prefix='.restore-', dir=target.parent); out = os.fdopen(fd,'wb')
            h = hashlib.sha256(); size = 0
            try:
                with io.BufferedReader(PartsReader(root, entry['parts'])) as stream, gzip.GzipFile(fileobj=stream) as f:
                    for chunk in iter(lambda:f.read(1024**2),b''):
                        h.update(chunk); size += len(chunk)
                        if out: out.write(chunk)
                if out: out.close()
                if size != entry['size'] or h.hexdigest() != entry['sha256']:
                    raise ValueError('Invalid reconstructed file: ' + entry['path'])
                if tmp:
                    if target.exists():
                        if digest(target)!=entry['sha256']: raise FileExistsError('Refuse overwrite: '+str(target))
                        os.unlink(tmp)
                    else: os.replace(tmp,target)
                    tmp = None
            finally:
                if out and not out.closed: out.close()
                if tmp and os.path.exists(tmp): os.unlink(tmp)
        else: raise ValueError('Unsupported storage: ' + storage)
        checked += 1
    return {'verified_files':checked,'pending_files':len(pending),'complete_local_snapshot':complete,
            'remote_training_artifacts_retrieved':manifest['remote_training_artifacts_retrieved']}


if __name__ == '__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    ap.add_argument('--destination',type=Path);ap.add_argument('--allow-partial',action='store_true')
    args=ap.parse_args();print(json.dumps(verify(args.root,args.destination,args.allow_partial)))
