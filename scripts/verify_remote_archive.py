"""Stream immutable GitHub objects; reuse a previous independently verified snapshot."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import quote
from urllib.request import urlopen


def objects(manifest):
    result = {}
    for e in manifest['files']:
        if e['storage'] == 'git': result[e['path']] = e
        elif e['storage'] == 'gzip-parts':
            result.update((p['path'], p) for p in e['parts'])
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--commit', required=True)
    ap.add_argument('--baseline-receipt', type=Path, required=True)
    ap.add_argument('--receipt', type=Path, required=True)
    a = ap.parse_args()
    if not re.fullmatch('[0-9a-f]{40}', a.commit): raise ValueError('Use a full commit')
    previous = json.loads(a.baseline_receipt.read_text())
    baseline = previous['commit']
    if not re.fullmatch('[0-9a-f]{40}', baseline): raise ValueError('Invalid baseline')
    old = json.loads(subprocess.check_output(['git', 'show', baseline+':data-archive/manifest.json']))
    old_objects = objects(old)
    if len(old_objects) != previous['verified_git_objects']: raise ValueError('Wrong baseline receipt')
    base = 'https://raw.githubusercontent.com/SansaZheng/MacroHFT/'+a.commit+'/'
    with urlopen(base+'data-archive/manifest.json', timeout=60) as r: raw = r.read()
    if raw != subprocess.check_output(['git', 'show', a.commit+':data-archive/manifest.json']):
        raise ValueError('Remote manifest differs from the committed bytes')
    manifest = json.loads(raw)
    current = objects(manifest)
    reused = []
    needed = []
    for name, e in current.items():
        prior = old_objects.get(name)
        same_content = prior and (e['sha256'], e['size']) == (prior['sha256'], prior['size'])
        same_blob = same_content and subprocess.check_output(['git', 'rev-parse', a.commit+':'+name]) == subprocess.check_output(['git', 'rev-parse', baseline+':'+name])
        if same_blob: reused.append(name)
        else: needed.append(e)
    def check(e):
        h = hashlib.sha256(); n = 0
        with urlopen(base+quote(e['path'], safe='/'), timeout=60) as response:
            for block in iter(lambda: response.read(1024**2), b''):
                h.update(block); n += len(block)
        if n != e['size'] or h.hexdigest() != e['sha256']:
            raise ValueError('Remote object mismatch: '+e['path'])
        return n
    fetched_bytes = 0
    with ThreadPoolExecutor(max_workers=4) as pool:
        for i, n in enumerate(pool.map(check, needed), 1):
            fetched_bytes += n
            if i % 25 == 0: print(f'{i}/{len(needed)} new remote objects verified', flush=True)
    entries = [e for e in manifest['files'] if e['storage'] != 'pending']
    receipt = {'commit': a.commit, 'baseline_commit': baseline,
               'baseline_receipt_sha256': hashlib.sha256(a.baseline_receipt.read_bytes()).hexdigest(),
               'verified_git_objects': len(current), 'reused_verified_objects': len(reused),
               'new_remote_objects_verified': len(needed), 'new_remote_bytes_verified': fetched_bytes,
               'represented_files': len(entries), 'represented_bytes': sum(e['size'] for e in entries),
               'pending_files': sum(e['storage']=='pending' for e in manifest['files']),
               'reconstructed_from_upstream': manifest.get('reconstructed_from_upstream', []),
               'complete_local_snapshot': manifest['complete_local_snapshot'],
               'remote_training_artifacts_retrieved': False,
               'verification': 'Immutable remote manifest; new/changed remote objects streamed and hashed; unchanged Git blob IDs and SHA-256 hashes backed by independent bare-clone verification'}
    a.receipt.write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt), flush=True)


if __name__ == '__main__': main()
