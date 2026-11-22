"""Cost transport diagnostic. Not an original successor-feature theorem or full RL agent."""
import numpy as np
from sklearn.neighbors import NearestNeighbors


def causal_features(frame):
    """Features at closed bar t use observations no later than t."""
    import pandas as pd
    close = frame.close.astype(float)
    returns = np.log(close).diff()
    volume = np.log1p(frame.volume.astype(float))
    x = pd.DataFrame(index=frame.index)
    for h in [5, 15, 60]:
        x[f'return_{h}'] = np.log(close / close.shift(h))
    for h in [15, 60]:
        x[f'vol_{h}'] = returns.rolling(h, min_periods=h).std()
    x['range'] = (frame.high - frame.low) / close
    x['volume_z'] = (volume - volume.rolling(60).mean()) / volume.rolling(60).std().clip(lower=1e-8)
    x['imbalance'] = 2 * frame.taker_base / frame.volume.clip(lower=1e-8) - 1
    return x.replace([np.inf, -np.inf], np.nan)


def round_trip_basis(entry, exit):
    """Gross P&L and traded notional per unit of entry-price exposure."""
    ratio = np.asarray(exit) / np.asarray(entry)
    return ratio - 1, 1 + ratio


class TransportMemory:
    def __init__(self, k=32, nominal_fee=0.0005, support_quantile=0.95):
        self.k, self.nominal_fee, self.support_quantile = k, nominal_fee, support_quantile

    def fit(self, x, gross, turnover, maturity):
        x = np.asarray(x, float)
        if len(x) <= self.k or not np.isfinite(x).all():
            raise ValueError('Insufficient or nonfinite training memory')
        self.mean, self.scale = x.mean(0), x.std(0).clip(min=1e-8)
        self.x = (x - self.mean) / self.scale
        self.gross, self.turnover = np.asarray(gross), np.asarray(turnover)
        self.maturity = np.asarray(maturity)
        if any(len(z) != len(x) for z in [self.gross, self.turnover, self.maturity]):
            raise ValueError('Memory lengths differ')
        self.nn = NearestNeighbors(n_neighbors=self.k + 1, n_jobs=1).fit(self.x)
        distances, _ = self.nn.kneighbors(self.x)
        # Exclude the self-neighbor; threshold learned only from training states.
        self.radius = np.quantile(distances[:, -1], self.support_quantile)
        return self

    def query(self, x, query_times, fee, penalty=1.0):
        if fee < 0 or not np.isfinite(fee):
            raise ValueError('Fee must be finite and nonnegative')
        # This prototype freezes memory before validation. Refuse rather than silently
        # retrieve any episode whose rewards have not matured before the query.
        if np.max(self.maturity) >= np.min(query_times):
            raise ValueError('Unmatured or future memory would leak into decisions')
        x = (np.asarray(x) - self.mean) / self.scale
        distances, ix = self.nn.kneighbors(x, n_neighbors=self.k)
        weights = 1 / (distances + 1e-3)
        weights /= weights.sum(1, keepdims=True)
        gross, turn = self.gross[ix], self.turnover[ix]
        rewards = gross - fee * turn
        transported = (weights * rewards).sum(1)
        scalar = (weights * (gross - self.nominal_fee * turn)).sum(1)
        effective_n = 1 / np.square(weights).sum(1)
        variance = (weights * np.square(rewards - transported[:, None])).sum(1)
        # Heuristic dispersion penalty: NOT a calibrated confidence bound under drift.
        score = transported - penalty * np.sqrt(variance / effective_n)
        supported = distances[:, -1] <= self.radius
        return dict(scalar=scalar, transported=transported, conservative=score,
                    supported=supported, effective_n=effective_n)


def evaluate_blocks(frame, starts, actions, horizon, fee, capital=100000., exposure=.25):
    """Long/flat disjoint round trips with fixed units and actual cash accounting."""
    starts, actions = np.asarray(starts, int), np.asarray(actions, bool)
    if len(starts) != len(actions) or np.any(np.diff(starts) < horizon):
        raise ValueError('Blocks overlap or actions mismatch')
    units = exposure * capital / float(frame.open.iloc[starts[0] + 1])
    cash, costs, turnover, executed = capital, 0., 0., 0
    equity, times = [capital], [frame.time.iloc[starts[0]]]
    blocked = 0
    for t, active in zip(starts, actions):
        entry, exit = float(frame.open.iloc[t + 1]), float(frame.open.iloc[t + horizon + 1])
        if active and cash < units * entry * (1 + fee):
            active = False; blocked += 1
        if active:
            cash -= units * entry * (1 + fee)
            costs += units * (entry + exit) * fee
            turnover += units * (entry + exit)
            executed += 1
        for j in range(t + 1, t + horizon + 1):
            equity.append(cash + (units * frame.close.iloc[j] if active else 0.))
            times.append(frame.time.iloc[j])
        if active:
            cash += units * exit * (1 - fee)
        equity.append(cash); times.append(frame.time.iloc[t + horizon + 1])
    equity = np.asarray(equity, float)
    drawdown = 1 - equity / np.maximum.accumulate(equity)
    import pandas as pd
    series = pd.Series(equity, index=pd.to_datetime(times, utc=True))
    daily = series.resample('1D').last().dropna().pct_change().dropna()
    return {'return_pct':100 * (cash / capital - 1), 'max_drawdown_pct':100 * float(drawdown.max()),
            'daily_sharpe_365':float(daily.mean()/daily.std(ddof=1)*np.sqrt(365)) if len(daily)>1 and daily.std(ddof=1)>0 else None,
            'cost_usd':costs, 'turnover_over_initial_capital':turnover/capital,
            'participation':executed/len(starts), 'executed_round_trips':executed,
            'cash_constraint_blocks':blocked, 'blocks':len(starts),
            'metric_basis':'fixed initial cash; next-bar open; two-sided costs; intra-block marked equity; fixed unit exposure'}
