"""Restart only ENOSPC-failed trials; preserve frozen selection and sealed test."""
import datetime, fcntl, hashlib, json, os, pathlib, subprocess, time
import cluster_controller as c

HOST = 'c224'
ENTRY = {'root': '/date/zyy/macrohft-cluster', 'jobs': [['reference', 42], ['combined', 42]]}
NAMES = ['reference-seed42', 'combined-seed42']
AUDIT = c.RESULT / 'recovery-20261002'

# This remote guard can signal only exact, owned trial processes in this project.
GUARD = r'''
import pathlib,json,shutil,os,signal,sys
r=pathlib.Path(sys.argv[1]);names=json.loads(sys.argv[2]);preflight=sys.argv[3]=='preflight'
assert r.stat().st_uid==os.getuid()
assert (r/'.macrohft-project').read_text().strip()=='macrohft-2026-10-02'
free=shutil.disk_usage(r).free/1024**3
if preflight:
 assert free>200, 'Require 200 GiB free at recovery launch'
 assert all(not (r/'results'/n).exists() for n in names), 'Preserve existing trial outputs'
 print(json.dumps({'free_gib':free,'preflight':'passed'}));sys.exit(0)
events=[]
for name in names:
 folder=r/'results'/name;marker=folder/'storage-paused.json'
 if (folder/'completed.json').exists():continue
 status=folder/'worker-status.json'
 if not status.exists():continue
 j=json.loads(status.read_text());pid=j.get('training_pid');proc=pathlib.Path('/proc')/str(pid)
 if not proc.exists():continue
 args=(proc/'cmdline').read_bytes().split(bytes([0]));v,seed=name.rsplit('-seed',1)
 assert proc.stat().st_uid==os.getuid()
 assert str(r/'scripts/run_experiment.py').encode() in args
 assert args[args.index(b'--variant')+1].decode()==v and args[args.index(b'--seed')+1].decode()==seed
 if free<60 and not marker.exists():
  marker.write_text(json.dumps({'pid':pid,'free_gib':free}))
  os.kill(pid,signal.SIGSTOP);events.append({'trial':name,'action':'paused','pid':pid})
 elif free>=120 and marker.exists():
  assert json.loads(marker.read_text())['pid']==pid
  os.kill(pid,signal.SIGCONT);marker.unlink();events.append({'trial':name,'action':'resumed','pid':pid})
print(json.dumps({'free_gib':free,'events':events,'paused':[n for n in names if (r/'results'/n/'storage-paused.json').exists()]}))
'''


def main():
    assert str(c.ROOT) == c.PLAN['coordinator_root']
    AUDIT.mkdir(exist_ok=True)
    lock = (c.RESULT/'pipeline.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    old = json.loads((c.RESULT/'pipeline-status.json').read_text())
    assert old['phase'] == 'failed' and not c.alive(old['pid'], str(c.ROOT))
    selection_file = c.RESULT/'selection-frozen.json'
    selection_hash = hashlib.sha256(selection_file.read_bytes()).hexdigest()
    selected = json.loads(selection_file.read_text())
    assert selected['selected_variant'] == 'combined' and not selected['test_used_for_selection']
    assert not (c.RESULT/'final-summary.json').exists()
    for variant in ['reference', 'combined']:
        for seed in c.SEEDS:
            folder = c.RESULT/f'{variant}-seed{seed}'
            assert not (folder/'test/metrics.json').exists() and not (folder/'test.log').exists()
            if seed != 42:
                assert (folder/'completed.json').exists()
                rows = [json.loads(x) for x in (folder/'validation.jsonl').read_text().splitlines()]
                assert len(rows) == 15
                assert (c.ROOT/f'vendor/MacroHFT/result/high_level/ETHUSDT/{variant}/seed_{seed}/best_model.pkl').exists()
    assert not (AUDIT/'launch.json').exists(), 'Recovery was already launched; inspect instead of duplicating'
    c.atomic(AUDIT/'failed-controller-status.json', old)
    capacity = c.remote_python(HOST, GUARD, [ENTRY['root'], json.dumps(NAMES), 'preflight'])
    c.atomic(AUDIT/'preflight.json', capacity)
    # Both destination paths are fresh; failed c203 artifacts remain in place and archived.
    launched = c.remote_python(HOST, (c.ROOT/'scripts/cluster_launch.py').read_text(),
                               [ENTRY['root'], json.dumps(ENTRY['jobs'])])
    c.atomic(AUDIT/'launch.json', launched)
    c.STATUS.clear()
    c.STATUS.update(old)
    c.STATUS.pop('error', None)
    c.STATUS.update(pid=os.getpid(), phase='recovery_training', selection=selected,
                    recovery_started_at=datetime.datetime.now().astimezone().isoformat(),
                    recovery_host=HOST, storage_monitor_interval_seconds=30,
                    recovery_reason='Both c203 seed-42 trials failed with ENOSPC; fresh 15-epoch restarts on c224')
    c.OWNERSHIP = True
    c.write()
    while True:
        try:
            guard = c.remote_python(HOST, GUARD, [ENTRY['root'], json.dumps(NAMES), 'monitor'])
            data = c.remote_python(HOST, (c.ROOT/'scripts/cluster_query.py').read_text(), [ENTRY['root'], *NAMES])
            c.STATUS['storage_monitor'] = {**guard, 'checked_at': datetime.datetime.now().astimezone().isoformat()}
            c.STATUS['phase'] = 'paused_storage' if guard['paused'] else 'recovery_training'
            for name, job in data.items():
                job.update(host=HOST, log=f'{ENTRY["root"]}/results/{name}/train.log',
                           pid=job.get('training_pid'), process_alive=job.get('training_alive',False))
                c.STATUS['jobs'][name] = job
                if job.get('completed'):
                    assert job['epochs_validated'] == 15
                    c.sync_job(HOST, ENTRY, name)
            c.STATUS.pop('recovery_connection_error', None)
        except (subprocess.SubprocessError, OSError) as exc:
            c.STATUS['recovery_connection_error'] = repr(exc)
            c.write(); time.sleep(30); continue
        c.write()
        if all(name in c.SYNCED for name in NAMES): break
        failed = [name for name in NAMES if c.STATUS['jobs'][name].get('status') == 'failed']
        if failed: raise RuntimeError(f'Recovery trial failed: {failed}; artifacts preserved')
        time.sleep(30)
    assert hashlib.sha256(selection_file.read_bytes()).hexdigest() == selection_hash
    c.evaluate_final('combined')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        if c.OWNERSHIP:
            c.STATUS.update(phase='failed', error=repr(exc)); c.write()
        else:
            AUDIT.mkdir(exist_ok=True)
            c.atomic(AUDIT/'start-error.json', {'error':repr(exc)})
        raise
