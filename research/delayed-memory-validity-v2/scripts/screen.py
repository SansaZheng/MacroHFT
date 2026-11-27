"""Frozen, small synthetic diagnostic. Outcome scoring is isolated from gate state."""
import csv
import hashlib
import json
from pathlib import Path
import random
import statistics
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from gate import DelayedGate


def run(scenario, delay, seed, cfg):
    rng=random.Random(seed); local=DelayedGate();global_gate=DelayedGate(conditional=False)
    gates=[global_gate,local]; queue={};errors={name:[] for name in cfg['baselines']}
    for t in range(cfg['steps']):
        # Only matured outcomes enter either method; no outcome is passed to issue().
        for records,y in queue.pop(t,[]):
            for gate,p in zip(gates,records):gate.settle(p.identifier,y,t)
        context,action=rng.randrange(2),rng.randrange(2)
        changed=t>=cfg['switch_at']
        if scenario=='stationary': changed=False
        if scenario=='local_switch':changed=changed and context==1 and action==1
        if scenario=='recurring':changed=cfg['switch_at']<=t<2*cfg['switch_at'] and context==1 and action==1
        y=(-1 if changed else 1)+rng.gauss(0,cfg['noise_sd'])
        records=[g.issue(t,t+delay,context,action,1.,-1.) for g in gates]
        queue.setdefault(t+delay,[]).append((records,y))
        predictions=[1.,-1.,0.,records[0].value,records[1].value]
        for name,pred in zip(cfg['baselines'],predictions):errors[name].append((pred-y)**2)
    return [{'scenario':scenario,'delay':delay,'seed':seed,'method':name,
             'mse':statistics.mean(e),'post_switch_mse':statistics.mean(e[cfg['switch_at']:])}
            for name,e in errors.items()]


def main():
    root=Path(__file__).resolve().parents[1]
    raw=(root/'protocol.json').read_bytes();cfg=json.loads(raw)
    # Fail rather than silently run different parameters from the registered design.
    assert (cfg['half_life'],cfg['temperature'],cfg['loss_clip'])==(64,.1,4)
    start=time.monotonic();rows=[]
    for scenario in cfg['scenarios']:
        for delay in cfg['delays']:
            for seed in cfg['seeds']:rows.extend(run(scenario,delay,seed,cfg))
    out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
    with (out/'synthetic-scores.csv').open('x') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    summary=[]
    for scenario in cfg['scenarios']:
        for delay in cfg['delays']:
            cell=[r for r in rows if r['scenario']==scenario and r['delay']==delay]
            means={name:statistics.mean(r['mse'] for r in cell if r['method']==name) for name in cfg['baselines']}
            local={r['seed']:r['mse'] for r in cell if r['method']=='conditional_delayed_weight'}
            global_={r['seed']:r['mse'] for r in cell if r['method']=='global_delayed_weight'}
            diffs=[local[s]-global_[s] for s in cfg['seeds']]
            summary.append({'scenario':scenario,'delay':delay,'mean_mse':means,
                            'paired_local_minus_global_mean':statistics.mean(diffs),
                            'paired_difference_sample_sd':statistics.stdev(diffs)})
    receipt={'synthetic_only':True,'market_evaluations':0,'training_performed':False,
             'protocol_sha256':hashlib.sha256(raw).hexdigest(),'rows':len(rows),
             'elapsed_seconds':time.monotonic()-start,'summary':summary,
             'source_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in root.rglob('*.py')},
             'limitation':'Constructed two-predictor toy with observed context/action and synthetic labels; no claim of RL performance or novelty.'}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'rows':len(rows),'elapsed_seconds':receipt['elapsed_seconds'],'summary':summary},indent=2))


if __name__=='__main__':main()
