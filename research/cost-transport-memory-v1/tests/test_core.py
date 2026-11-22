import pathlib,sys,unittest
import numpy as np
import pandas as pd
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'src'))
from memory import causal_features,round_trip_basis,TransportMemory,evaluate_blocks


class CausalAccountingTests(unittest.TestCase):
    def test_future_mutation_cannot_change_prior_features(self):
        rng=np.random.default_rng(7);p=100*np.exp(np.cumsum(rng.normal(0,.001,140)))
        f=pd.DataFrame({'close':p,'high':p*1.01,'low':p*.99,'volume':rng.uniform(1,10,140),'taker_base':1.})
        before=causal_features(f)
        f.loc[90:,['close','high','low','volume','taker_base']]*=100
        pd.testing.assert_frame_equal(before.iloc[:90],causal_features(f).iloc[:90])

    def test_transport_equals_direct_two_sided_fee_accounting(self):
        entry=np.array([100.,80.,200.]);exit=np.array([120.,70.,200.])
        gross,turn=round_trip_basis(entry,exit)
        for fee in [0,.0002,.002,.01]:
            direct=(exit*(1-fee)-entry*(1+fee))/entry
            np.testing.assert_allclose(gross-fee*turn,direct,atol=1e-15)

    def make_memory(self):
        return TransportMemory(k=2).fit(np.arange(8).reshape(4,2),np.full(4,.003),np.full(4,2.),np.arange(4))

    def test_memory_rejects_future_reward_access(self):
        with self.assertRaisesRegex(ValueError,'future memory'):
            self.make_memory().query([[2.,3.]],[3],.001)

    def test_transport_responds_to_cost_but_stale_scalar_does_not(self):
        m=self.make_memory();low=m.query([[2.,3.]],[8],0);high=m.query([[2.,3.]],[8],.01)
        self.assertGreater(low['transported'][0],0)
        self.assertLess(high['transported'][0],0)
        np.testing.assert_allclose(low['scalar'],high['scalar'])

    def test_cash_and_long_accounting_known_answer(self):
        f=pd.DataFrame({'time':pd.date_range('2026-01-01',periods=4,freq='min',tz='UTC'),
                        'open':[9.,10.,11.,12.],'close':[9.5,11.,11.5,12.]})
        long=evaluate_blocks(f,[0],[1],2,.01,capital=100,exposure=.25)
        self.assertAlmostEqual(long['return_pct'],4.45)
        self.assertAlmostEqual(long['cost_usd'],.55)
        self.assertEqual(evaluate_blocks(f,[0],[0],2,.01,100,.25)['return_pct'],0)

    def test_overlapping_execution_is_rejected(self):
        with self.assertRaises(ValueError):evaluate_blocks(None,[0,1],[1,1],2,.01)


if __name__=='__main__':unittest.main()
