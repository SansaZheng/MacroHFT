import copy
import importlib.util
import os
from pathlib import Path
import sys
import unittest
import warnings

import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT/'vendor/MacroHFT'
sys.path.insert(0, str(REPO.parent))
os.chdir(REPO)
from MacroHFT.RL.util.memory import episodicmemory
from MacroHFT.model.net import subagent
from MacroHFT.env.high_level_env import Testing_Env, Training_Env
sys.path.insert(0,str(ROOT/'scripts'))
from fast_evaluation import subagent_single_equivalent, evaluate


class ReproductionTests(unittest.TestCase):
    def test_original_memory_matches_formula(self):
        rng=np.random.default_rng(12)
        m=episodicmemory(20,5,2,2,3,'cpu')
        for i in range(20):
            m.add(rng.normal(size=3), i%2, i, [0,0],[0,0],0)
        q=np.array([[0.2,0.5,0.1]])
        k=np.array([1/(np.sum((q-h)**2)+1e-3) for h in m.buffer['hidden_state']])
        ix=np.argsort(k)[-5:]
        for a in (0,1):
            w=k[ix]*(m.buffer['action'][ix]==a)
            expected=np.dot(w/w.sum(),m.buffer['q_value'][ix]) if w.sum() else np.nan
            np.testing.assert_allclose(m.query(q,a),expected,equal_nan=True)

    def test_action_memory_avoids_wrong_action_neighbors(self):
        for mode in ('original','action_conditioned'):
            m=episodicmemory(6,5,1,1,1,'cpu',mode=mode)
            for i in range(6):
                m.add([i],int(i==5),7 if i==5 else 0,[0],[0],0)
            actual=m.query(np.array([[0.0]]),1)
            if mode=='original': self.assertTrue(np.isnan(actual))
            else: self.assertAlmostEqual(actual,7)

    def test_checkpoint_snapshot_is_independent(self):
        n=torch.nn.Linear(2,2)
        best=copy.deepcopy(n.state_dict()); before=best['weight'].clone()
        with torch.no_grad(): n.weight.add_(1)
        torch.testing.assert_close(best['weight'],before)

    def test_cash_accounting_has_known_answer(self):
        d=pd.DataFrame({'close':[100.,110.,105.,120.], 'x':[0.]*4,'trend':[0.]*4,'slope_360':[0.]*4,'vol_360':[0.]*4})
        e=Testing_Env(d,['x'],['trend'],max_holding_number=1,transcation_cost=0.0002)
        e.reset()
        for a in (1,1,0): e.step(a)
        # Buy at 100, sell at 105; fees 0.02+0.021.
        self.assertAlmostEqual(e.required_money,100.02)
        self.assertAlmostEqual(e.final_balance,4.959)
        self.assertAlmostEqual(sum(e.reward_history),4.959)

    def test_teacher_cost_variant_changes_targets(self):
        d=pd.DataFrame({'close':[100.,100.,101.], 'x':[0.]*3,'trend':[0.]*3,'slope_360':[0.]*3,'vol_360':[0.]*3})
        original=Training_Env(d,['x'],['trend'],max_holding_number=1)
        variant=Training_Env(d,['x'],['trend'],max_holding_number=1,teacher_cost=0.0002)
        self.assertFalse(np.allclose(original.q_table,variant.q_table))

    def test_batch_inference_matches_single_observation(self):
        n=subagent(36,9,2,64).eval()
        n.load_state_dict(torch.load(REPO/'result/low_level/ETHUSDT/best_model/slope/1/best_model.pkl',map_location='cpu',weights_only=True))
        frame=pd.read_feather(REPO/'data/ETHUSDT/whole/val.feather').iloc[:32]
        names=np.load(REPO/'data/feature_list/single_features.npy',allow_pickle=True).tolist()
        names2=np.load(REPO/'data/feature_list/trend_features.npy',allow_pickle=True).tolist()
        x=torch.tensor(frame[names].values,dtype=torch.float32)
        c=torch.tensor(frame[names2].values,dtype=torch.float32)
        prev=torch.arange(32)%2
        with torch.no_grad():
            expected=torch.cat([n(x[i:i+1],c[i:i+1],prev[i:i+1]) for i in range(32)])
            actual=subagent_single_equivalent(n,x,c,prev)
        torch.testing.assert_close(actual,expected,rtol=1e-5,atol=1e-5)
        torch.testing.assert_close(actual.argmax(1),expected.argmax(1))

    def test_frozen_expert_cache_preserves_batch_centering(self):
        from cached_experts import ExpertCache, CachedExpert
        frame=pd.read_feather(REPO/'data/ETHUSDT/whole/train.feather').iloc[:64]
        names=np.load(REPO/'data/feature_list/single_features.npy',allow_pickle=True).tolist()
        names2=np.load(REPO/'data/feature_list/trend_features.npy',allow_pickle=True).tolist()
        experts=[]
        for p in sorted((REPO/'result/low_level/ETHUSDT/best_model').glob('*/*/best_model.pkl')):
            e=subagent(36,9,2,64).eval()
            e.load_state_dict(torch.load(p,map_location='cpu',weights_only=True))
            experts.append(e)
        cache=ExpertCache(experts,frame,names,names2)
        x=torch.tensor(frame[names].values,dtype=torch.float32)
        c=torch.tensor(frame[names2].values,dtype=torch.float32)
        previous=torch.arange(len(frame))%2
        for j,e in enumerate(experts):
            with torch.no_grad():
                expected=e(x,c,previous)
                actual=CachedExpert(e,cache,j)(x,c,previous)
            torch.testing.assert_close(actual,expected,rtol=1e-5,atol=2e-5)
            torch.testing.assert_close(actual.argmax(1),expected.argmax(1))

    def test_fast_evaluator_matches_original_rollout(self):
        import importlib
        m=importlib.import_module('MacroHFT.RL.agent.high_level')
        args=m.parser.parse_args(['--device','cpu','--skip_test','--exp','integration-check'])
        m.args=args
        agent=m.DQN(args)
        frame=pd.read_feather(REPO/'data/ETHUSDT/whole/val.feather').iloc[:2048]
        env=Testing_Env(frame,agent.tech_indicator_list,agent.tech_indicator_list_trend,agent.clf_list,max_holding_number=0.2)
        state,trend,regime,info=env.reset()
        actions=[]
        done=False
        while not done:
            a=agent.act_test(state,trend,regime,info)
            actions.append(a)
            state,trend,regime,r,done,info=env.step(a)
        metrics,fast_actions,rewards,fees=evaluate(agent,frame)
        np.testing.assert_array_equal(fast_actions,actions)
        self.assertAlmostEqual(metrics['profit'],env.final_balance,places=8)
        self.assertAlmostEqual(metrics['required_capital'],env.required_money,places=8)
        np.testing.assert_allclose(rewards,env.reward_history[1:],atol=1e-10)
        agent.writer.close()

    def test_array_environment_matches_original_for_both_initial_positions(self):
        from array_environment import ArrayTrainingEnv
        frame=pd.DataFrame({'close':[100.,110.,105.,120.,90.,95.], 'x':[0.]*6,'trend':[0.]*6,'slope_360':[0.]*6,'vol_360':[0.]*6})
        for initial in (0,1):
            for fee in (0.001,0.0002):
                kwargs=dict(df=frame,tech_indicator_list=['x'],tech_indicator_list_trend=['trend'],clf_list=['slope_360','vol_360'],max_holding_number=0.2,initial_action=initial,teacher_cost=fee)
                original=Training_Env(**kwargs); fast=ArrayTrainingEnv(**kwargs)
                np.testing.assert_allclose(fast.q_table,original.q_table,atol=1e-12)
                original.reset(); fast.reset()
                for a in (1,0,1,1,0):
                    o=original.step(a);f=fast.step(a)
                    for i in range(3): np.testing.assert_array_equal(o[i],f[i])
                    self.assertAlmostEqual(o[3],f[3],places=12)
                    self.assertEqual(o[4],f[4])
                    np.testing.assert_array_equal(o[5]['q_value'],f[5]['q_value'])
                self.assertAlmostEqual(original.final_balance,fast.final_balance,places=12)
                self.assertAlmostEqual(original.required_money,fast.required_money,places=12)

    def test_all_six_official_checkpoints_load(self):
        for p in (REPO/'result/low_level/ETHUSDT/best_model').glob('*/*/best_model.pkl'):
            n=subagent(36,9,2,64)
            n.load_state_dict(torch.load(p,map_location='cpu',weights_only=True))
            with torch.no_grad(): q=n(torch.zeros(1,36),torch.zeros(1,9),torch.zeros(1,dtype=torch.long))
            self.assertTrue(torch.isfinite(q).all())

if __name__=='__main__':
    torch.set_num_threads(1)
    unittest.main()
