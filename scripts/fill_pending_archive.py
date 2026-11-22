"""Fill small missing legacy files after iCloud hydration, without replacing archived work."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', type=Path, required=True)
    ap.add_argument('--destination', type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args()
    source, dest = args.source.resolve(), args.destination.resolve()
    aliases = {'docs/legacy/README-20261002.md': 'README.md',
               'docs/legacy-tooling/restore_archive-v1.py': 'scripts/restore_archive.py',
               'docs/legacy-tooling/test_archive-v1.py': 'tests/test_archive.py'}
    path = dest/'data-archive/manifest.json'
    manifest = json.loads(path.read_text())
    completed = []
    with tempfile.TemporaryDirectory(prefix='macrohft-fill-', dir=dest) as tmp:
        for e in manifest['files']:
            if e['storage'] != 'pending': continue
            inp = source/aliases.get(e['path'], e['path']); out = dest/e['path']
            if not inp.resolve().is_relative_to(source) or not out.resolve().is_relative_to(dest):
                raise ValueError('Path outside archive roots')
            if not inp.exists() or inp.is_symlink(): continue
            if getattr(inp.stat(), 'st_flags', 0) & 0x40000000: continue
            if inp.stat().st_size > 40*1024**2: continue
            if shutil.disk_usage(dest).free < 2*1024**3: break
            temp = Path(tmp)/'one-file'
            try:
                subprocess.run([sys.executable, '-c',
                    'import shutil,sys;shutil.copyfile(sys.argv[1],sys.argv[2])', str(inp), str(temp)],
                    check=True, timeout=10, capture_output=True)
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                continue
            raw = temp.read_bytes()
            if len(raw) != inp.stat().st_size: raise ValueError('Partial source read: '+e['path'])
            if out.exists() and out.read_bytes() != raw: raise ValueError('Preserve existing archive: '+e['path'])
            out.parent.mkdir(parents=True, exist_ok=True)
            if not out.exists(): temp.replace(out)
            e.update(storage='git', size=len(raw), sha256=hashlib.sha256(raw).hexdigest())
            e.pop('reason', None)
            completed.append(e['path'])
            print('Recovered '+e['path'], flush=True)
    # Reconstructed source still is not a direct retrieval of legacy bytes.
    manifest['complete_local_snapshot'] = not manifest.get('reconstructed_from_upstream') and not any(e['storage']=='pending' for e in manifest['files'])
    path.write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps({'recovered_files': len(completed), 'pending_files': sum(e['storage']=='pending' for e in manifest['files'])}), flush=True)


if __name__ == '__main__': main()
