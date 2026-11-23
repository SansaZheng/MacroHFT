"""Read every unique blob in specified published snapshots without storing data.

This tool never deletes files. Git object IDs come from the local tree; bytes
come from immutable GitHub commit URLs. SHA-256 is also recorded for each blob.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
from urllib.parse import quote
from urllib.request import urlopen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--commit', action='append', required=True)
    ap.add_argument('--receipt', type=Path, required=True)
    args = ap.parse_args()
    snapshots = {}; objects = {}
    for commit in args.commit:
        if not re.fullmatch('[0-9a-f]{40}', commit):
            raise ValueError('An immutable full commit is required')
        rows = subprocess.check_output(['git', 'ls-tree', '-r', '-l', '-z', commit])
        entries = []
        for row in rows.split(b'\0'):
            if not row: continue
            meta, path = row.split(b'\t', 1)
            mode, kind, oid, size = meta.decode().split()
            if kind != 'blob' or mode not in {'100644', '100755'}:
                raise ValueError('Unsupported tree entry; inspect before cleanup')
            entry = {'path': path.decode(), 'git_blob': oid, 'size': int(size)}
            entries.append(entry)
            objects.setdefault(oid, dict(entry, commit=commit))
        snapshots[commit] = entries

    def check(entry):
        url = ('https://raw.githubusercontent.com/SansaZheng/MacroHFT/' +
               entry['commit'] + '/' + quote(entry['path'], safe='/'))
        for attempt in range(3):
            try:
                git_hash = hashlib.sha1(('blob '+str(entry['size'])+'\0').encode())
                sha256 = hashlib.sha256(); size = 0
                with urlopen(url, timeout=30) as response:
                    for chunk in iter(lambda: response.read(1024**2), b''):
                        size += len(chunk); git_hash.update(chunk); sha256.update(chunk)
                if size != entry['size'] or git_hash.hexdigest() != entry['git_blob']:
                    raise ValueError('Remote bytes mismatch: '+entry['path'])
                return dict(entry, sha256=sha256.hexdigest())
            except Exception:
                if attempt == 2: raise
                time.sleep(attempt+1)

    verified = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        for index, entry in enumerate(pool.map(check, objects.values()), 1):
            verified.append(entry)
            if index % 50 == 0:
                print(f'{index}/{len(objects)} remote blobs verified', flush=True)
    receipt = {'client_date': '2026-11-24',
               'checked_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'repository': 'SansaZheng/MacroHFT', 'snapshots': snapshots,
               'verification': 'Every unique blob freshly streamed from immutable GitHub URLs; size and Git blob hash match the published tree',
               'verified_blobs': len(verified),
               'verified_bytes': sum(x['size'] for x in verified),
               'blobs': verified}
    args.receipt.write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps({k: receipt[k] for k in ['verified_blobs', 'verified_bytes']}))


if __name__ == '__main__':
    main()
