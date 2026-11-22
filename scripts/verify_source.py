"""Bind a vendored runtime to its actual project commit, not upstream Git metadata."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


def verify(root, expected_commit):
    root = Path(root).resolve()
    if not re.fullmatch(r'[0-9a-f]{40}', expected_commit):
        raise ValueError('A full project commit SHA is required')
    def git(*args):
        return subprocess.check_output(['git', '-C', str(root), *args])
    if Path(git('rev-parse', '--show-toplevel').decode().strip()).resolve() != root:
        raise ValueError('Project root must be the actual Git root')
    if git('rev-parse', 'HEAD').decode().strip() != expected_commit:
        raise ValueError('Project commit does not match the CQ specification')
    raw = (root / 'code-provenance.json').read_bytes()
    if raw != git('show', expected_commit + ':code-provenance.json'):
        raise ValueError('Code manifest differs from the pinned commit')
    manifest = json.loads(raw)
    for name, expected in manifest['sha256'].items():
        path = root / name
        if Path(name).is_absolute() or path.resolve().is_relative_to(root) is False or path.is_symlink():
            raise ValueError('Unsafe source path: ' + name)
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Source hash mismatch: ' + name)
    actual_sources = set()
    for folder in manifest['source_roots']:
        base = root / folder
        if not base.resolve().is_relative_to(root):
            raise ValueError('Unsafe source root')
        actual_sources.update(p.relative_to(root).as_posix() for p in base.rglob('*')
                              if p.is_file() and p.suffix in {'.py', '.sh'})
    if not actual_sources.issubset(manifest['sha256']):
        raise ValueError('Unmanifested executable source: ' + str(sorted(actual_sources - manifest['sha256'].keys())))
    return {'project_commit': expected_commit, 'verified_files': len(manifest['sha256']),
            'upstream_commit': manifest['upstream_commit'],
            'vendor_git_metadata_required': False, 'training_performed': False}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--expected-commit', required=True)
    ap.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args()
    print(json.dumps(verify(args.root, args.expected_commit)))
