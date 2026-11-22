"""Post-hoc activity-matched validation diagnostic, not a new model selection round."""
import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='1'
import hashlib,json,pathlib,sys,zipfile
import numpy as np
import pandas as pd
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(R/'scripts'))
from memory import causal_features,round_trip_basis,TransportMemory
from pilot import blocks,COLUMNS
P=json.loads((R/'protocol.json').read_text());manifest=json.loads((R/'results/data-manifest.json').read_text());raw=json.loads((R/'results/pilot.json').read_text());records=[]
plan={'client_date':'2026-10-14','timing':'post-hoc after primary pilot; validation only','purpose':'separate selective trading from simply trading less','random_schedules':500,'seed':1973,'all_symbols_and_costs':True,'not_formal_p_values':True,'test_accessed':False}
output=R/'results/activity-control.json'
if output.exists():raise RuntimeError('Analysis already exists; preserve it')
(R/'results/activity-control-plan.json').write_text(json.dumps(plan,indent=2))
rng=np.random.default_rng(plan['seed'])

def load(symbol,month):
 record=next(x for x in manifest if x['symbol']==symbol and x['month']==month)
 path=R/'data'/f'{symbol}-1m-{month}.zip';assert hashlib.sha256(path.read_bytes()).hexdigest()==record['sha256']
 with zipfile.ZipFile(path) as z:f=pd.read_csv(z.open(z.namelist()[0]),header=None,names=COLUMNS)
 f['time']=pd.to_datetime(f.timestamp,unit=record['timestamp_unit'],utc=True)
 return f

def ret(entry,exit,selected,fee,units):
 cash=P['capital_usd']
 for i in np.flatnonzero(selected):
  if cash>=units*entry[i]*(1+fee):cash+=units*(exit[i]-entry[i]-fee*(entry[i]+exit[i]))
 return 100*(cash/P['capital_usd']-1)

for symbol in P['symbols']:
 train=pd.concat([load(symbol,m) for m in P['training_months']],ignore_index=True)
 val=pd.concat([load(symbol,m) for m in P['validation_months']],ignore_index=True)
 xt,xv=causal_features(train),causal_features(val);it,iv=blocks(train,xt),blocks(val,xv);h=P['horizon_minutes']
 g,u=round_trip_basis(train.open.iloc[it+1],train.open.iloc[it+h+1])
 m=TransportMemory(P['k'],P['nominal_cost_bps']/10000,P['support_quantile']).fit(xt.iloc[it],g,u,train.time.iloc[it+h+1].astype('int64'))
 entry=val.open.iloc[iv+1].to_numpy();exit=val.open.iloc[iv+h+1].to_numpy();units=P['capital_usd']*P['fixed_unit_exposure_at_start']/entry[0]
 traces={'entry':entry,'exit':exit,'decision_timestamps':val.time.iloc[iv].astype('int64').to_numpy()}
 for bps in P['evaluation_costs_bps']:
  q=m.query(xv.iloc[iv],val.time.iloc[iv].astype('int64'),bps/10000,P['uncertainty_penalty']);a=(q['conservative']>0)&q['supported'];traces[f'guarded_actions_{bps}bps']=a
  actual=ret(entry,exit,a,bps/10000,units)
  original=next(x for x in raw['rows'] if x['symbol']==symbol and x['cost_bps']==bps and x['variant']=='guarded_transport')
  assert abs(actual-original['return_pct'])<1e-10
  n=int(a.sum());draw=[]
  for _ in range(plan['random_schedules']):
   random_a=np.zeros(len(a),bool);random_a[rng.choice(len(a),size=n,replace=False)]=True
   draw.append(ret(entry,exit,random_a,bps/10000,units))
  draw=np.asarray(draw)
  records.append({'symbol':symbol,'cost_bps':bps,'trades':n,'guarded_return_pct':actual,'random_median_return_pct':float(np.median(draw)),'random_5th_return_pct':float(np.quantile(draw,.05)),'random_95th_return_pct':float(np.quantile(draw,.95)),'fraction_random_at_least_guarded':float(np.mean(draw>=actual)),'interpretation':'descriptive hindsight activity-matched randomization; not a valid significance test or implementable deployed benchmark'})
 np.savez_compressed(R/f'results/{symbol}-guarded-decision-trace.npz',**traces)
output.write_text(json.dumps({'plan':plan,'rows':records},indent=2));print(pd.DataFrame(records).to_string(index=False,columns=['symbol','cost_bps','trades','guarded_return_pct','random_median_return_pct','fraction_random_at_least_guarded']))
