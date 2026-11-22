"""Bounded experiment queue. Selection is validation-only; no test-driven retries."""
import fcntl
import concurrent.futures
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

ROOT=Path(__file__).resolve().parents[1]
RESULTS=ROOT/'results'
LOCK=threading.Lock()
SEEDS=[12345,2024,42]
VARIANTS=['reference','combined','action_memory','cost_aligned']
STATUS={'started_at':datetime.datetime.now().astimezone().isoformat(),'pid':os.getpid(),'phase':'training_candidates','workers':2,'device':'cpu','jobs':{},'selection':None}


def write_status():
    target=RESULTS/'pipeline-status.json'
    tmp=target.with_suffix('.tmp')
    tmp.write_text(json.dumps(STATUS,indent=2));tmp.replace(target)


def train(variant,seed):
    key=f'{variant}-seed{seed}'
    folder=RESULTS/key;folder.mkdir(parents=True,exist_ok=True)
    if (folder/'completed.json').exists():
        with LOCK: STATUS['jobs'][key]={'status':'already_completed'};write_status()
        return key
    if (folder/'validation.jsonl').exists():
        raise RuntimeError(f'{key} has partial results; preserve and archive them before an explicit restart')
    command=[sys.executable,'-u',str(ROOT/'scripts/run_experiment.py'),'--variant',variant,'--seed',str(seed),'--device','cpu']
    with (folder/'train.log').open('w') as log:
        child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,cwd=ROOT)
        with LOCK: STATUS['jobs'][key]={'status':'running','pid':child.pid,'log':str(folder/'train.log'),'command':command};write_status()
        code=child.wait()
    with LOCK: STATUS['jobs'][key].update(status='completed' if code==0 else 'failed',exit_code=code);write_status()
    if code: raise RuntimeError(f'{key} failed with exit code {code}')
    return key


def validate_rows(variant,seed):
    rows=[json.loads(x) for x in (RESULTS/f'{variant}-seed{seed}'/'validation.jsonl').read_text().splitlines()]
    if len(rows)!=15: raise RuntimeError(f'Expected 15 validation epochs, got {len(rows)}')
    return rows


def main():
    RESULTS.mkdir(exist_ok=True)
    if (RESULTS/'final-summary.json').exists():
        raise SystemExit('Final results already exist; do not rerun the sealed test automatically.')
    code_files=sorted((ROOT/'scripts').glob('*.py'))+sorted((ROOT/'vendor/MacroHFT').rglob('*.py'))
    manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in code_files}
    (RESULTS/'execution-code-manifest.json').write_text(json.dumps(manifest,indent=2))
    write_status()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda v:train(v,12345),VARIANTS))
    scores={v:max((r['return_pct'] if r['return_pct'] is not None else 0.0) for r in validate_rows(v,12345)) for v in VARIANTS}
    chosen=max([v for v in VARIANTS if v!='reference'],key=lambda v:scores[v])
    selection={'selected_variant':chosen,'validation_return_pct':scores,'criterion':'max full-validation return over 15 epochs; candidate tie order: combined, action_memory, cost_aligned','test_used_for_selection':False,'seeds':SEEDS,'frozen_at':datetime.datetime.now().astimezone().isoformat()}
    for v in ('reference',chosen):
        checkpoint=ROOT/f'vendor/MacroHFT/result/high_level/ETHUSDT/{v}/seed_12345/best_model.pkl'
        selection[v+'_checkpoint_sha256']=hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    (RESULTS/'selection-frozen.json').write_text(json.dumps(selection,indent=2))
    STATUS.update(phase='replication_seeds',selection=selection);write_status()
    jobs=[(v,s) for s in SEEDS[1:] for v in ('reference',chosen)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda job:train(*job),jobs))
    STATUS['phase']='sealed_test_evaluation';write_status()
    results=[]
    for seed in SEEDS:
        for variant in ('reference',chosen):
            checkpoint=ROOT/f'vendor/MacroHFT/result/high_level/ETHUSDT/{variant}/seed_{seed}/best_model.pkl'
            cmd=[sys.executable,'-u',str(ROOT/'scripts/run_experiment.py'),'--variant',variant,'--seed',str(seed),'--evaluate',str(checkpoint),'--split','test']
            folder=RESULTS/f'{variant}-seed{seed}'
            with (folder/'test.log').open('w') as log: subprocess.run(cmd,check=True,stdout=log,stderr=subprocess.STDOUT,cwd=ROOT)
            metric=json.loads((folder/'test/metrics.json').read_text())
            results.append({'variant':variant,'seed':seed,**metric})
    summary={'status':'completed','scope':'ETH hyper-agent retraining using six authors-released subagent checkpoints; other markets and subagent retraining not reproduced','selection':selection,'published_eth_return_pct':39.28,'test_results':results,'completed_at':datetime.datetime.now().astimezone().isoformat()}
    import numpy as np
    summary['aggregate']={}
    for variant in ('reference',chosen):
        values=np.array([r['return_pct'] if r['return_pct'] is not None else 0.0 for r in results if r['variant']==variant])
        summary['aggregate'][variant]={'mean_return_pct':float(values.mean()),'sample_std_return_pct':float(values.std(ddof=1)),'seeds':len(values),'seed_returns_pct':values.tolist()}
    summary['candidate_mean_exceeds_published']=summary['aggregate'][chosen]['mean_return_pct']>39.28
    summary['candidate_mean_exceeds_reproduced_reference']=summary['aggregate'][chosen]['mean_return_pct']>summary['aggregate']['reference']['mean_return_pct']
    summary['comparability_warning']='Same dates and simulator fee; code return uses ex-post required capital, released expert training provenance and original feature generation are not independently reconstructed. Seed dispersion is not statistical significance.'
    (RESULTS/'final-summary.json').write_text(json.dumps(summary,indent=2))
    STATUS['phase']='completed';write_status()

if __name__=='__main__':
    lock_file=(RESULTS/'pipeline.lock').open('a')
    fcntl.flock(lock_file,fcntl.LOCK_EX|fcntl.LOCK_NB)
    try: main()
    except Exception as exc:
        STATUS.update(phase='failed',error=repr(exc));write_status()
        raise
