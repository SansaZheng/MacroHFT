"""Bounded read-only recovery of six completed trials; never evaluates a policy."""
import hashlib
import json
import os
from pathlib import Path
import signal
import socket

ROOT = Path('/date/zyy/macrohft-reproduction')
LIMIT = 16 * 1024**2


def expired(*args):
    raise TimeoutError('legacy read exceeded ten seconds')


def main():
    if socket.gethostname().split('.')[0] != 'c225':
        raise RuntimeError('This recovery requires the c225-local legacy root')
    out = Path(os.environ['CQ_OUTPUT_DIR'])
    out.mkdir(parents=True, exist_ok=True)
    signal.signal(signal.SIGALRM, expired)
    names = ['results/final-summary.json', 'results/selection-frozen.json',
             'results/data-audit.json', 'results/pipeline-status.json',
             'scripts/run_experiment.py', 'scripts/fast_evaluation.py',
             'scripts/cached_experts.py', 'scripts/array_environment.py',
             'vendor/MacroHFT/RL/agent/high_level.py',
             'vendor/MacroHFT/RL/util/memory.py',
             'vendor/MacroHFT/env/high_level_env.py']
    arrays = []
    for variant in ['reference', 'combined']:
        for seed in [12345, 2024, 42]:
            folder = f'results/{variant}-seed{seed}'
            names += [folder+'/'+n for n in ['config.json', 'completed.json',
                      'validation.jsonl', 'test/metrics.json', 'test.log']]
            names.append(f'vendor/MacroHFT/result/high_level/ETHUSDT/{variant}/seed_{seed}/best_model.pkl')
            # Record trajectory identities without copying large arrays to the Mac.
            for n in ['action.npy', 'reward.npy', 'final_balance.npy', 'require_money.npy', 'commission_fee_history.npy']:
                arrays.append(folder+'/test/'+n)
    records = {}; copied = 0
    for index, name in enumerate(names+arrays):
        (out/'progress.log').write_text(f'{index}/{len(names+arrays)} recovering {name}\n')
        source = ROOT/name
        try:
            signal.alarm(10)
            if not source.resolve().is_relative_to(ROOT.resolve()):
                raise ValueError('Resolved source escapes authorized root')
            before = source.stat()
            if before.st_size > LIMIT: raise ValueError('Per-file size bound exceeded')
            data = source.read_bytes(); after = source.stat()
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise ValueError('Source changed while reading')
            if len(data) != before.st_size: raise ValueError('Partial source read')
            record = {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                      'mtime_ns': after.st_mtime_ns, 'copied': name in names}
            if name in names:
                copied += len(data)
                if copied > 64*1024**2: raise ValueError('Total copy bound exceeded')
                target = out/'files'/name; target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists(): raise FileExistsError('Preserve existing output')
                target.write_bytes(data)
            records[name] = record
        except Exception as exc:
            records[name] = {'error': type(exc).__name__+': '+str(exc)}
        finally:
            signal.alarm(0)
    result = {'collection_complete': True, 'host': socket.gethostname(),
              'root': str(ROOT), 'declared_commit': os.environ['SOURCE_COMMIT'],
              'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'read_only_legacy': True, 'training_performed': False,
              'new_market_evaluations': 0, 'files': records, 'copied_bytes': copied}
    (out/'receipt.json').write_text(json.dumps(result, indent=2)+'\n')
    (out/'progress.log').write_text(f'{len(records)}/{len(names+arrays)} complete\n')
    print(json.dumps({'collected': sum('error' not in r for r in records.values()),
                      'errors': sum('error' in r for r in records.values())}))


if __name__ == '__main__': main()
