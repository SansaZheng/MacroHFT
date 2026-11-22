"""Bounded, read-only inventory of an explicitly authorized legacy project."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import socket
import time


def alarm(*_):
    raise TimeoutError('metadata operation exceeded five seconds')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True)
    args = ap.parse_args()
    root = Path(args.root)
    if str(root) not in {'/date/zyy/macrohft-reproduction',
                         '/date/zyy/macrohft-cluster', '/data/zyy/macrohft-cluster'}:
        raise SystemExit('Root is outside the authorized legacy project list')
    out = Path(os.environ['CQ_OUTPUT_DIR'])
    out.mkdir(parents=True, exist_ok=True)
    signal.signal(signal.SIGALRM, alarm)
    started = time.monotonic()
    result = {'host': socket.gethostname(), 'root': str(root), 'files': {},
              'read_only_legacy': True, 'inventory_complete': False}
    names = ['results/pipeline-status.json', 'results/selection-frozen.json',
             'results/final-summary.json', 'results/data-audit.json',
             'results/setup-verified.json']
    for i, name in enumerate(names):
        (out/'progress.log').write_text(f'{i}/{len(names)+1} checking {name}\n')
        try:
            signal.alarm(5)
            p = root / name
            if not p.exists():
                result['files'][name] = {'exists': False}
                continue
            st = p.stat()
            if st.st_size > 2 * 1024**2:
                result['files'][name] = {'exists': True, 'size': st.st_size, 'skipped': 'size bound'}
                continue
            data = p.read_bytes()
            result['files'][name] = {'exists': True, 'size': len(data),
                                     'sha256': hashlib.sha256(data).hexdigest(),
                                     'content': json.loads(data)}
        except Exception as e:
            result['files'][name] = {'error': type(e).__name__ + ': ' + str(e)}
        finally:
            signal.alarm(0)
    try:
        signal.alarm(5)
        result['root_exists'] = root.exists()
        if root.exists():
            st = root.stat(); result['root_uid'] = st.st_uid
            result['same_owner'] = st.st_uid == os.getuid()
            st = os.statvfs(root); result['free_bytes'] = st.f_bavail * st.f_frsize
        result['python_exists'] = (root/'.venv/bin/python').exists()
        result['git_metadata_exists'] = (root/'vendor/MacroHFT/.git').exists()
    except Exception as e:
        result['root_error'] = type(e).__name__ + ': ' + str(e)
    finally:
        signal.alarm(0)
    result['inventory_complete'] = True
    result['elapsed_seconds'] = time.monotonic() - started
    result['max_rss_kib_linux'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    (out/'inventory.json').write_text(json.dumps(result, indent=2)+'\n')
    (out/'progress.log').write_text(f'{len(names)+1}/{len(names)+1} complete\n')
    print(json.dumps({'inventory_complete': True, 'root_exists': result.get('root_exists')}))


if __name__ == '__main__':
    main()
