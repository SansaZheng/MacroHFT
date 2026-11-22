"""Prepare official ETH splits with an algebraically equivalent rolling filter."""
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt, correlate

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / 'vendor/MacroHFT'
sys.path.insert(0, str(REPO))
from preprocess.decomposition import chunk, label_slope, label_volatility, get_slope_window


def rolling_slope(close, window=360):
    # The fixed-window filter and OLS slope are linear. Compute its coefficients
    # once rather than fitting sklearn on every one of 900,000 windows.
    b, a = butter(1, 0.05, btype='low')
    x = np.arange(window, dtype=float)
    x -= x.mean()
    weights = (x / (x @ x)) @ filtfilt(b, a, np.eye(window), axis=0)
    result = np.full(len(close), np.nan)
    result[window-1:] = correlate(np.asarray(close), weights, mode='valid', method='direct')
    return result


def main():
    os.chdir(REPO)
    frames = [pd.read_feather(f'data/ETHUSDT/df_{s}.feather') for s in ('train','val','test')]
    report = {'source_commit': '31e5ef41f93b2aea6e63e6ae2267675c997a8e54', 'splits': {}}
    for name, df in zip(('train','val','test'), frames):
        assert df.timestamp.is_monotonic_increasing and not df.timestamp.duplicated().any()
        assert (df.timestamp.diff().dropna() == pd.Timedelta(minutes=1)).all()
        assert np.isfinite(df.select_dtypes('number').values).all()
        p = Path(f'data/ETHUSDT/df_{name}.feather')
        report['splits'][name] = {'rows':len(df), 'start':str(df.timestamp.iloc[0]), 'end':str(df.timestamp.iloc[-1]), 'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
        for folder in (name, 'whole'):
            Path(f'data/ETHUSDT/{folder}').mkdir(exist_ok=True)
    assert frames[0].timestamp.iloc[-1] < frames[1].timestamp.iloc[0] < frames[2].timestamp.iloc[0]
    assert frames[1].timestamp.iloc[-1] < frames[2].timestamp.iloc[0]
    chunk(*frames)
    label_slope(*frames)
    label_volatility(*frames)
    for name, df in zip(('train','val','test'), frames):
        slope = rolling_slope(df.close)
        errs = []
        for i in np.linspace(359,len(df)-1,20,dtype=int):
            ref = get_slope_window(df.close.iloc[i-359:i+1])
            errs.append(abs(slope[i]-ref))
        assert max(errs) < 1e-9, max(errs)
        df['slope_360'] = slope
        df['return'] = df.close.pct_change().fillna(0)
        df['vol_360'] = df['return'].rolling(360).std()
        df = df.dropna().reset_index(drop=True).iloc[1:].reset_index(drop=True)
        df.to_feather(f'data/ETHUSDT/whole/{name}.feather')
        report['splits'][name].update(prepared_rows=len(df),prepared_start=str(df.timestamp.iloc[0]),max_slope_error=max(errs))
        print(name, report['splits'][name], flush=True)
    (ROOT/'results/data-audit.json').write_text(json.dumps(report,indent=2))

if __name__ == '__main__':
    main()
