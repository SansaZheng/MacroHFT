"""Verify recovered historical summaries and (optionally) per-trial CQ files."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics


def verify(inventory_path, collection=None):
    inventory=json.loads(inventory_path.read_text())
    entries=inventory['files']; entry=entries['results/final-summary.json']
    summary=entry['content']
    raw=json.dumps(summary,indent=2).encode()
    assert len(raw)==entry['size'] and hashlib.sha256(raw).hexdigest()==entry['sha256']
    rows=summary['test_results']
    keys={(r['variant'],r['seed']) for r in rows}
    expected={(v,s) for v in ['reference','combined'] for s in [12345,2024,42]}
    assert len(rows)==6 and keys==expected
    for row in rows:
        assert math.isclose(row['return_pct'],100*row['profit']/row['required_capital'],abs_tol=1e-12)
    for variant in ['reference','combined']:
        values=[r['return_pct'] for r in rows if r['variant']==variant]
        agg=summary['aggregate'][variant]
        assert math.isclose(statistics.mean(values),agg['mean_return_pct'],abs_tol=1e-12)
        assert math.isclose(statistics.stdev(values),agg['sample_std_return_pct'],abs_tol=1e-12)
    result={'summary_bytes_match_inventory':True,'six_unique_trials':True,
            'return_arithmetic_and_aggregates_match':True,
            'individual_trial_files_verified':False,'new_market_evaluations':0}
    if collection:
        receipt=json.loads((collection/'receipt.json').read_text())
        assert receipt['training_performed'] is False and receipt['new_market_evaluations']==0
        verified=[]
        for name,record in receipt['files'].items():
            if record.get('copied'):
                data=(collection/'files'/name).read_bytes()
                assert len(data)==record['size'] and hashlib.sha256(data).hexdigest()==record['sha256'],name
                verified.append(name)
        assert (collection/'files/results/final-summary.json').read_bytes()==raw
        frozen=json.loads((collection/'files/results/selection-frozen.json').read_text())
        assert frozen==summary['selection']
        for row in rows:
            v,s=row['variant'],row['seed']
            name=f'results/{v}-seed{s}/test/metrics.json'
            metrics=json.loads((collection/'files'/name).read_text())
            assert metrics=={k:val for k,val in row.items() if k not in {'variant','seed'}},name
            name=f'vendor/MacroHFT/result/high_level/ETHUSDT/{v}/seed_{s}/best_model.pkl'
            assert name in verified,name
            if s==12345:assert receipt['files'][name]['sha256']==frozen[v+'_checkpoint_sha256']
        result.update(individual_trial_files_verified=True,copied_files_verified=len(verified),
                      frozen_seed12345_checkpoint_hashes_match=True,
                      collector_errors={k:v for k,v in receipt['files'].items() if 'error' in v})
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('inventory',type=Path)
    parser.add_argument('--collection',type=Path)
    args=parser.parse_args();print(json.dumps(verify(args.inventory,args.collection),indent=2))
