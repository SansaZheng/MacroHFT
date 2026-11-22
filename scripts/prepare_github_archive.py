"""Build a Git archive without altering legacy evidence or using paid storage.

Large immutable files are gzip streams split into <=32 MiB Git objects. The
manifest records hashes of both the original bytes and every uploaded part.
Environments, nested Git databases and third-party paper PDFs are not copied.
"""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile

SKIP_DIRS = {'.git', '.venv', '__pycache__', 'publication', '.pytest_cache'}
PART_BYTES = 32 * 1024**2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', type=Path, required=True)
    ap.add_argument('--destination', type=Path, required=True)
    ap.add_argument('--metadata-only', action='store_true')
    ap.add_argument('--skip-unavailable', action='store_true',
                    help='Record unhydrated macOS files as pending instead of blocking')
    args = ap.parse_args()
    source, dest = args.source.resolve(), args.destination.resolve()
    if source == dest or not (dest / '.git').exists():
        raise SystemExit('Destination must be a separate initialized Git checkout')
    manifest = {'schema': 1, 'source_scope': 'local MacroHFT project snapshot',
                'remote_training_artifacts_retrieved': False, 'files': [], 'excluded': [],
                'complete_local_snapshot': not args.metadata_only}
    paths = []
    for root, dirs, files in os.walk(source):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in sorted(files):
            p = Path(root) / name
            rel = p.relative_to(source).as_posix()
            if p.is_symlink() or name == '.DS_Store' or name.startswith('.env') or name.startswith('archive-preparation'):
                manifest['excluded'].append({'path': rel, 'reason': 'environment, metadata or symlink'})
                continue
            if rel.startswith('paper/MacroHFT-KDD2024'):
                manifest['excluded'].append({'path': rel, 'reason': 'third-party paper; linked in provenance document'})
                continue
            archive_rel = {'README.md': 'docs/legacy/README-20261002.md',
                           'scripts/restore_archive.py': 'docs/legacy-tooling/restore_archive-v1.py',
                           'tests/test_archive.py': 'docs/legacy-tooling/test_archive-v1.py',
                           'scripts/prepare_github_archive.py': 'docs/legacy-tooling/prepare_github_archive-v1.py'}.get(rel, rel)
            paths.append((p, archive_rel, p.stat().st_size))
    for i, (p, rel, size) in enumerate(paths):
        if args.skip_unavailable and getattr(p.stat(), 'st_flags', 0) & 0x40000000:
            manifest['files'].append({'path': rel, 'size': size, 'storage': 'pending',
                                      'reason': 'iCloud data not locally materialized'})
            manifest['complete_local_snapshot'] = False
            continue
        if args.metadata_only and (size > 4 * 1024**2 or p.suffix in {'.feather', '.pt', '.pth', '.zip', '.npz'}):
            manifest['files'].append({'path': rel, 'size': size, 'storage': 'pending'})
            continue
        if shutil.disk_usage(dest).free < 2 * 1024**3:
            raise SystemExit('Archive stopped: preserve at least 2 GiB local free space')
        h = hashlib.sha256()
        if size <= 40 * 1024**2:
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp = tempfile.mkstemp(prefix='.archive-', dir=target.parent)
            with os.fdopen(fd, 'wb') as out, p.open('rb') as inp:
                for chunk in iter(lambda: inp.read(1024**2), b''):
                    h.update(chunk)
                    out.write(chunk)
            if Path(tmp).stat().st_size != size:
                os.unlink(tmp)
                raise RuntimeError('Source size changed or partial read: ' + rel)
            os.replace(tmp, target)
            record = {'path': rel, 'size': target.stat().st_size, 'sha256': h.hexdigest(), 'storage': 'git'}
        else:
            parts_dir = dest / 'data-archive' / hashlib.sha256(rel.encode()).hexdigest()[:20]
            parts_dir.mkdir(parents=True, exist_ok=True)
            # Stream compression and splitting: never hold a dataset in memory.
            class SplitWriter:
                def __init__(self):
                    self.parts = []; self.handle = None; self.size = 0; self.hasher = None
                def close_part(self):
                    if self.handle:
                        self.handle.close()
                        self.parts.append({'path': str(self.path.relative_to(dest)),
                                           'size': self.size, 'sha256': self.hasher.hexdigest()})
                        self.handle = None
                def write(self, data):
                    original_len = len(data)
                    while data:
                        if self.handle is None:
                            self.path = parts_dir / ('part-%04d.gzpart' % len(self.parts))
                            self.handle = self.path.open('wb'); self.size = 0; self.hasher = hashlib.sha256()
                        block, data = data[:PART_BYTES-self.size], data[PART_BYTES-self.size:]
                        self.handle.write(block); self.hasher.update(block); self.size += len(block)
                        if self.size == PART_BYTES: self.close_part()
                    return original_len
                def flush(self):
                    if self.handle: self.handle.flush()
            writer = SplitWriter()
            with gzip.GzipFile(filename='', mode='wb', fileobj=writer, compresslevel=1, mtime=0) as out, p.open('rb') as inp:
                for chunk in iter(lambda: inp.read(1024**2), b''):
                    h.update(chunk); out.write(chunk)
            writer.close_part()
            record = {'path': rel, 'size': size, 'sha256': h.hexdigest(),
                      'storage': 'gzip-parts', 'parts': writer.parts}
        manifest['files'].append(record)
        print(f'{i+1}/{len(paths)} {rel} {size}', flush=True)
    (dest / 'data-archive').mkdir(exist_ok=True)
    (dest / 'data-archive/manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'files': len(manifest['files']), 'complete': manifest['complete_local_snapshot']}), flush=True)


if __name__ == '__main__':
    main()
