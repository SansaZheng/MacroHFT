"""Real-data prefix integration check. NOT a published-result reproduction."""
import argparse
import importlib
import json
import os
from pathlib import Path
import sys
import time
import numpy as np
import pandas as pd
import torch

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
p.add_argument('--variant',choices=['reference','action-memory-cost'],default='reference')
p.add_argument('--rows',type=int,default=4608)
p.add_argument('--fast',action='store_true')
a=p.parse_args()
os.chdir(ROOT/'vendor/MacroHFT')
sys.path.insert(0,str(ROOT/'vendor'))
m=importlib.import_module('MacroHFT.RL.agent.high_level')
if a.fast:
    from array_environment import ArrayTrainingEnv
    m.Training_Env=ArrayTrainingEnv
args=m.parser.parse_args(['--device','cpu','--epoch_number','2','--buffer_size','8192','--skip_test','--exp',f'smoke-{a.variant}'+('-fast' if a.fast else '')])
if a.variant!='reference':
    args.memory_mode='action_conditioned'
    args.teacher_cost=0.0002
m.args=args
torch.set_num_threads(1)
read=pd.read_feather

def prefix(path,*pos,**kw):
    frame=read(path,*pos,**kw)
    if Path(path).name=='test.feather': raise RuntimeError('Test access prohibited in smoke run')
    return frame.iloc[:a.rows if Path(path).name=='train.feather' else 2048].copy()
pd.read_feather=prefix
start=time.perf_counter()
agent=m.DQN(args)
if a.fast:
    from cached_experts import install
    cache=install(agent,pd.read_feather(Path(agent.train_data_path)/'train.feather'))
agent.train()
agent.writer.close()
result={'status':'smoke_passed','not_paper_reproduction':True,'variant':a.variant,'fast_runtime':a.fast,'seed':args.seed,'training_rows':a.rows,'validation_rows':2048,'epochs':2,'seconds':time.perf_counter()-start,'validation_returns':[]}
for epoch in (1,2):
    path=Path(agent.model_path)/f'epoch_{epoch}'/'val'
    final=np.load(path/'final_balance_val.npy').item(); required=np.load(path/'require_money_val.npy').item()
    result['validation_returns'].append({'epoch':epoch,'return_pct':100*final/required if required else None})
(ROOT/f"results/smoke-{a.variant}{'-fast' if a.fast else ''}.json").write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
