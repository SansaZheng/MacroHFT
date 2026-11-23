"""Run the existing ten numerical regression tests on synthetic inputs only.

The code checkout is read-only; packages, fixture data and test side effects
live exclusively under CQ_OUTPUT_DIR. This is not a trading experiment.
"""
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import time
import traceback
from urllib.request import urlopen


def bootstrap_pip(python, root, tmp, env, log):
    """Install pinned pip in the private venv without relying on distro ensurepip."""
    meta = json.loads((root/'bootstrap-provenance.json').read_text())
    with urlopen(meta['url'], timeout=30) as response:
        data = response.read(meta['size']+1)
    if len(data) != meta['size'] or hashlib.sha256(data).hexdigest() != meta['sha256']:
        raise ValueError('Official bootstrap bytes do not match the pinned digest')
    script = tmp/'get-pip.py';script.write_bytes(data)
    subprocess.run([python, str(script), 'pip=='+meta['pip_version'], '--no-cache-dir',
                    '--index-url', 'https://pypi.org/simple'], env=env, stdout=log,
                   stderr=subprocess.STDOUT, check=True, timeout=120)


def inner(root, out):
    import numpy as np
    import pandas as pd
    import torch
    runtime = out/'runtime'
    shutil.copytree(root/'vendor', runtime/'vendor')
    shutil.copytree(root/'tests', runtime/'tests', ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copytree(root/'scripts', runtime/'scripts', ignore=shutil.ignore_patterns('__pycache__'))
    repo = runtime/'vendor/MacroHFT'
    weights = sorted((repo/'result/low_level/ETHUSDT/best_model').glob('*/*/best_model.pkl'))
    if len(weights) != 6: raise RuntimeError('Exactly six released expert weights are required')
    names = np.load(repo/'data/feature_list/single_features.npy', allow_pickle=True).tolist()
    trend = np.load(repo/'data/feature_list/trend_features.npy', allow_pickle=True).tolist()
    rng = np.random.default_rng(23112026)
    frame = pd.DataFrame({name: rng.normal(0, .1, 2048) for name in sorted(set(names+trend))})
    frame['close'] = 100 + np.cumsum(rng.normal(0, .05, len(frame)))
    frame['slope_360'] = rng.normal(0, .01, len(frame))
    frame['vol_360'] = rng.uniform(.0001, .01, len(frame))
    folder = repo/'data/ETHUSDT/whole'; folder.mkdir(parents=True)
    frame.to_feather(folder/'val.feather')
    frame.iloc[:64].to_feather(folder/'train.feather')
    (out/'progress.log').write_text('3/5 synthetic fixtures ready; running ten regression tests\n')
    start = time.monotonic()
    run = subprocess.run([sys.executable, str(runtime/'tests/test_reproduction.py')],
                         cwd=runtime, capture_output=True, text=True, timeout=180)
    (out/'runtime-tests.log').write_text(run.stdout+run.stderr)
    if run.returncode or 'Ran 10 tests' not in run.stderr or '\nOK\n' not in run.stderr:
        raise RuntimeError('Runtime regression tests failed; inspect runtime-tests.log')
    peak = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    fixture = {'synthetic': True, 'seed': 23112026, 'validation_fixture_rows': 2048,
               'training_fixture_rows': 64, 'market_data_used': False,
               'sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.glob('*.feather')}}
    (out/'synthetic-fixture.json').write_text(json.dumps(fixture, indent=2)+'\n')
    # Preserve tiny synthetic fixtures as evidence, not model-training data.
    shutil.copytree(folder, out/'synthetic-fixtures')
    receipt = {'runtime_tests_passed': True, 'runtime_test_count': 10,
               'declared_commit': os.environ['SOURCE_COMMIT'], 'source_manifest_verified': True,
               'canonical_source_commit': '1dfae1699e62b57f4647eac7bf6751caf63c7cd6',
               'python': sys.version, 'torch': torch.__version__, 'numpy': np.__version__,
               'pandas': pd.__version__, 'test_elapsed_seconds': time.monotonic()-start,
               'test_child_peak_rss_bytes': peak if sys.platform=='darwin' else peak*1024,
               'synthetic_inputs_only': True, 'official_expert_checkpoints': len(weights),
               'training_performed': False, 'market_test_evaluations': 0,
               'limitation': 'Synthetic numerical regression qualification on Kaggle CPU; not a lab environment qualification or performance reproduction'}
    (out/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    (out/'progress.log').write_text('4/5 runtime regression passed; collecting environment\n')


def main():
    root = Path(__file__).resolve().parents[1]
    out = Path(os.environ['CQ_OUTPUT_DIR']).resolve(); out.mkdir(exist_ok=True, parents=True)
    if '--inner' in sys.argv:
        inner(root, out); return
    manifest = json.loads((root/'code-manifest.json').read_text())
    for name, expected in manifest['sha256'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest() != expected:
            raise RuntimeError('Source hash mismatch: '+name)
    (out/'source-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    for name in ['env', 'tmp', 'pip-cache', 'runtime', 'synthetic-fixtures']:
        if (out/name).exists(): raise FileExistsError('Preserve existing output: '+name)
    (out/'progress.log').write_text('0/5 source hashes verified; creating isolated environment\n')
    tmp = out/'tmp';tmp.mkdir(exist_ok=True)
    env = dict(os.environ, TMPDIR=str(tmp), PIP_CACHE_DIR=str(out/'pip-cache'),
               OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
               NUMEXPR_NUM_THREADS='1', PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1')
    python = str(out/'env/bin/python')
    commands = [
        [python, '-m', 'pip', 'install', '--no-cache-dir', '--index-url', 'https://pypi.org/simple', 'setuptools==80.9.0', 'wheel==0.45.1'],
        [python, '-m', 'pip', 'install', '--no-cache-dir', '--index-url', 'https://download.pytorch.org/whl/cpu', 'torch==2.8.0'],
        [python, '-m', 'pip', 'install', '--no-cache-dir', '--index-url', 'https://pypi.org/simple', '-r', str(root/'requirements-runtime-smoke.txt')]]
    try:
        with (out/'environment-build.log').open('w') as log:
            subprocess.run([sys.executable, '-m', 'venv', '--copies', '--without-pip', str(out/'env')], env=env,
                           stdout=log, stderr=subprocess.STDOUT, check=True, timeout=60)
            bootstrap_pip(python, root, tmp, env, log)
            for i, command in enumerate(commands):
                subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=150)
                (out/'progress.log').write_text(f'{i+1}/5 dependency stage complete\n')
        with (out/'runner.log').open('w') as log:
            subprocess.run([python, str(Path(__file__).resolve()), '--inner'], env=env,
                           stdout=log, stderr=subprocess.STDOUT, check=True, timeout=240)
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc())
        for name in ['environment-build.log', 'runner.log', 'runtime-tests.log']:
            p = out/name
            if p.exists(): print(name+'\n'+p.read_text(errors='replace')[-8000:], file=sys.stderr, flush=True)
        raise
    finally:
        try:
            if Path(python).exists():
                freeze = subprocess.run([python, '-m', 'pip', 'freeze'], env=env, text=True,
                                        capture_output=True, timeout=30)
                (out/'environment-freeze.txt').write_text(freeze.stdout+freeze.stderr)
        finally:
            # Also clean partially built venv symlinks if bootstrap or freeze fails.
            for name in ['env', 'tmp', 'pip-cache', 'runtime']:
                p = out/name
                if p.is_dir(): shutil.rmtree(p)
    (out/'progress.log').write_text('5/5 runtime qualification complete\n')


if __name__ == '__main__': main()
