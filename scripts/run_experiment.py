"""Run a full official hyper-agent training job, with validation-only selection."""
import argparse
import importlib
import json
import os
from pathlib import Path
import sys
import time
import types

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
p.add_argument('--variant',choices=['reference','action_memory','cost_aligned','combined'],default='reference')
p.add_argument('--seed',type=int,default=12345)
p.add_argument('--epochs',type=int,default=15)
p.add_argument('--device',default='cpu')
p.add_argument('--evaluate',type=Path)
p.add_argument('--no_cache',action='store_true')
p.add_argument('--original_environment',action='store_true')
p.add_argument('--split',choices=['val','test'],default='test')
a=p.parse_args()
for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'): os.environ[key]='1'
import torch
import pandas as pd
from fast_evaluation import save_evaluation
os.chdir(ROOT/'vendor/MacroHFT'); sys.path.insert(0,str(ROOT/'vendor'))
m=importlib.import_module('MacroHFT.RL.agent.high_level')
argv=['--device',a.device,'--seed',str(a.seed),'--epoch_number',str(a.epochs),'--skip_test','--exp',a.variant]
if a.variant in ('action_memory','combined'): argv+=['--memory_mode','action_conditioned']
if a.variant in ('cost_aligned','combined'): argv+=['--teacher_cost','0.0002']
args=m.parser.parse_args(argv);m.args=args
if not a.original_environment:
    from array_environment import ArrayTrainingEnv
    m.Training_Env=ArrayTrainingEnv
torch.set_num_threads(1);torch.set_num_interop_threads(1)
agent=m.DQN(args)
log=ROOT/'results'/f'{a.variant}-seed{a.seed}';log.mkdir(parents=True,exist_ok=True)
(log/'config.json').write_text(json.dumps(vars(args),indent=2))
start=time.time()

def val_cluster(self,epoch_path,save_path):
    self.hyperagent.load_state_dict(torch.load(Path(epoch_path)/'trained_model.pkl',map_location=self.device,weights_only=True));self.hyperagent.eval()
    df=pd.read_feather(Path(self.val_data_path)/'val.feather')
    result=save_evaluation(self,df,save_path,'_val')
    print(json.dumps({'event':'validation','epoch_path':str(epoch_path),'elapsed_seconds':time.time()-start,**result}),flush=True)
    with (log/'validation.jsonl').open('a') as f: f.write(json.dumps({'epoch':int(Path(epoch_path).name.split('_')[-1]),**result})+'\n')
    return result['return_pct']/100 if result['return_pct'] is not None else 0.0

agent.val_cluster=types.MethodType(val_cluster,agent)
if a.evaluate:
    agent.hyperagent.load_state_dict(torch.load(a.evaluate.resolve(),map_location=agent.device,weights_only=True));agent.hyperagent.eval()
    result=save_evaluation(agent,pd.read_feather(Path(agent.test_data_path)/f'{a.split}.feather'),log/a.split)
    print(json.dumps(result),flush=True)
else:
    print(json.dumps({'event':'started','variant':a.variant,'seed':a.seed,'epochs':a.epochs,'pid':os.getpid()}),flush=True)
    if not a.no_cache:
        from cached_experts import install
        cache=install(agent,pd.read_feather(Path(agent.train_data_path)/'train.feather'))
        print(json.dumps({'event':'expert_cache_ready','elapsed_seconds':time.time()-start}),flush=True)
    agent.train()
    (log/'completed.json').write_text(json.dumps({'status':'training_completed','elapsed_seconds':time.time()-start,'test_evaluated':False}))
agent.writer.close()
