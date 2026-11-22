"""Bounded public-data diagnostic. Never downloads or evaluates sealed test months."""
import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']: os.environ[key]='1'
import hashlib, io, json, pathlib, shutil, sys, time, urllib.request, zipfile
import numpy as np
import pandas as pd
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from memory import TransportMemory, causal_features, round_trip_basis, evaluate_blocks
P = json.loads((ROOT/'protocol.json').read_text())
COLUMNS = ['timestamp','open','high','low','close','volume','close_time','quote_volume','trades','taker_base','taker_quote','ignore']


def fetch(symbol, month):
    assert month in P['training_months'] + P['validation_months']
    assert month not in P['sealed_future_test_months']
    folder = ROOT/'data';folder.mkdir(exist_ok=True)
    filename = f'{symbol}-1m-{month}.zip';path = folder/filename
    base = f'https://data.binance.vision/data/spot/monthly/klines/{symbol}/1m/{filename}'
    expected = urllib.request.urlopen(base+'.CHECKSUM',timeout=30).read().decode().split()[0]
    if not path.exists():
        if shutil.disk_usage(ROOT).free < P['compute']['minimum_local_free_gib']*1024**3:
            raise RuntimeError('Local free-space floor reached; no large download')
        payload = urllib.request.urlopen(base,timeout=60).read(25000001)
        if len(payload)>25000000:raise RuntimeError('Unexpected archive size')
        if sum(p.stat().st_size for p in folder.glob('*.zip'))+len(payload)>P['compute']['maximum_download_bytes']:
            raise RuntimeError('Download budget exceeded')
        assert hashlib.sha256(payload).hexdigest()==expected,'Checksum mismatch'
        tmp=path.with_suffix('.tmp');tmp.write_bytes(payload);tmp.replace(path)
    digest=hashlib.sha256(path.read_bytes()).hexdigest();assert digest==expected
    with zipfile.ZipFile(path) as z:
        names=z.namelist();assert len(names)==1 and names[0].endswith('.csv')
        frame=pd.read_csv(z.open(names[0]),header=None,names=COLUMNS)
    # Binance spot switched from milliseconds to microseconds on 2025-01-01.
    unit='us' if frame.timestamp.median()>10**14 else 'ms'
    frame['time']=pd.to_datetime(frame.timestamp,unit=unit,utc=True)
    assert frame.time.is_unique and frame.time.is_monotonic_increasing
    assert (frame.time.dt.strftime('%Y-%m')==month).all()
    assert np.isfinite(frame[['open','high','low','close','volume']].to_numpy()).all()
    assert (frame[['open','high','low','close']]>0).all().all()
    return frame,dict(symbol=symbol,month=month,url=base,sha256=digest,rows=len(frame),timestamp_unit=unit,
                     first=str(frame.time.iloc[0]),last=str(frame.time.iloc[-1]),bytes=path.stat().st_size)


def blocks(frame, features):
    h=P['horizon_minutes'];starts=np.arange(60,len(frame)-h-1,h)
    good=np.isfinite(features.iloc[starts].to_numpy()).all(1)
    # No block may bridge a missing bar; no fabricated forward-filled prices.
    ts=frame.time.astype('int64').to_numpy()
    for n,t in enumerate(starts):good[n]&=np.all(np.diff(ts[t:t+h+2])==60_000_000_000)
    return starts[good]


def main():
    out=ROOT/'results';out.mkdir(exist_ok=True)
    if (out/'pilot.json').exists():raise RuntimeError('Pilot already exists; register a new version before rerunning')
    manifest=[];rows=[];start=time.time()
    for symbol in P['symbols']:
        frames={}
        for month in P['training_months']+P['validation_months']:
            frames[month],record=fetch(symbol,month);manifest.append(record)
            (out/'data-manifest.json').write_text(json.dumps(manifest,indent=2))
        train=pd.concat([frames[m] for m in P['training_months']],ignore_index=True)
        val=pd.concat([frames[m] for m in P['validation_months']],ignore_index=True)
        xt,xv=causal_features(train),causal_features(val)
        it,iv=blocks(train,xt),blocks(val,xv);h=P['horizon_minutes']
        gross,turn=round_trip_basis(train.open.iloc[it+1],train.open.iloc[it+h+1])
        model=TransportMemory(P['k'],P['nominal_cost_bps']/10000,P['support_quantile'])
        model.fit(xt.iloc[it],gross,turn,train.time.iloc[it+h+1].astype('int64'))
        for bps in P['evaluation_costs_bps']:
            fee=bps/10000
            q=model.query(xv.iloc[iv],val.time.iloc[iv].astype('int64'),fee,P['uncertainty_penalty'])
            actions={'cash':np.zeros(len(iv),bool),'long_blocks':np.ones(len(iv),bool),
                     'momentum':xv.return_60.iloc[iv].to_numpy()>0,
                     'reversal':xv.return_60.iloc[iv].to_numpy()<0,
                     'scalar_memory':q['scalar']>0,'transport_memory':q['transported']>0,
                     'guarded_transport':(q['conservative']>0)&q['supported']}
            for name,a in actions.items():
                metric=evaluate_blocks(val,iv,a,h,fee,P['capital_usd'],P['fixed_unit_exposure_at_start'])
                rows.append(dict(symbol=symbol,variant=name,cost_bps=bps,split='validation-2026-03',**metric))
        print(json.dumps({'symbol':symbol,'memory_rows':len(it),'validation_blocks':len(iv),'elapsed_s':time.time()-start}),flush=True)
    result={'status':'pilot_completed','scope':P['scope'],'protocol_sha256':hashlib.sha256((ROOT/'protocol.json').read_bytes()).hexdigest(),
            'test_evaluated':False,'seed':'deterministic memory diagnostic; no deep RL training',
            'elapsed_seconds':time.time()-start,'rows':rows}
    (out/'pilot.json').write_text(json.dumps(result,indent=2,allow_nan=False))
    pd.DataFrame(rows).to_csv(out/'pilot.csv',index=False)


if __name__=='__main__':main()
