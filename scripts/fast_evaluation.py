"""Batched evaluation with the same two-action recurrent position policy.

The released subagent subtracts a batch-global advantage mean. Use a per-row
mean to exactly represent its single-observation inference when batching.
This is inference only: training retains the released network's behavior.
"""
import json
from pathlib import Path
import numpy as np
import torch


def subagent_single_equivalent(agent, x, context, previous):
    agent=getattr(agent,"original",agent)
    hidden=agent.fc1(x)
    c=agent.embedding(previous)+agent.fc2(context)
    shift,scale=agent.adaLN_modulation(c).chunk(2,dim=1)
    hidden=agent.norm(hidden)*(1+scale)+shift
    value=agent.value(hidden); advantage=agent.advantage(hidden)
    return value+advantage-advantage.mean(dim=1,keepdim=True)


def policy_table(agent, frame, batch_size=4096):
    experts=[agent.slope_agents[i] for i in range(3)]+[agent.vol_agents[i] for i in range(3)]
    single=frame[agent.tech_indicator_list].to_numpy(dtype=np.float32)
    trend=frame[agent.tech_indicator_list_trend].to_numpy(dtype=np.float32)
    classes=frame[agent.clf_list].to_numpy(dtype=np.float32)
    table=np.empty((len(frame)-1,2),dtype=np.int64)
    with torch.no_grad():
        for start in range(0,len(frame)-1,batch_size):
            end=min(start+batch_size,len(frame)-1)
            x=torch.as_tensor(np.repeat(single[start:end],2,axis=0),device=agent.device)
            c=torch.as_tensor(np.repeat(trend[start:end],2,axis=0),device=agent.device)
            regime=torch.as_tensor(np.repeat(classes[start:end],2,axis=0),device=agent.device)
            prev=torch.arange(2,device=agent.device).repeat(end-start)
            qs=torch.stack([subagent_single_equivalent(e,x,c,prev) for e in experts],dim=1)
            weights=agent.hyperagent(x,c,regime,prev)
            qs=torch.bmm(weights[:,None,:],qs).squeeze(1)
            table[start:end]=qs.argmax(dim=1).cpu().numpy().reshape(-1,2)
    return table


def evaluate(agent,frame):
    table=policy_table(agent,frame)
    actions=np.empty(len(table),dtype=np.int64)
    previous=0
    for i in range(len(table)):
        previous=table[i,previous]
        actions[i]=previous
    price=frame.close.to_numpy(dtype=np.float64)
    delta=np.diff(np.r_[0,actions])*agent.max_holding_number
    fees=np.abs(delta)*price[:-1]*agent.transcation_cost
    cash=-delta*price[:-1]-fees
    balance=np.cumsum(cash)
    required=float(-min(0.,balance.min()))
    final=float(cash.sum()+price[-1]*actions[-1]*agent.max_holding_number)
    rewards=agent.max_holding_number*actions*np.diff(price)-fees
    equity=required+np.r_[0.,np.cumsum(rewards)]
    metrics={'return_pct':100*final/required if required>0 else None,'profit':final,'required_capital':required,'fees':float(fees.sum()),'buys':int((delta>0).sum()),'position_changes':int((delta!=0).sum()),'rows':len(frame),'return_definition':'upstream profit / ex-post maximum cash requirement; terminal position marked to market without liquidation fee'}
    if required>0 and (equity>0).all():
        r=np.diff(equity)/equity[:-1]
        std=float(r.std()); mean=float(r.mean()); downside=r[r<0]
        mdd=float(np.max(1-equity/np.maximum.accumulate(equity)))
        metrics.update(max_drawdown_pct=100*mdd,annual_volatility_pct=100*std*np.sqrt(525600),annual_sharpe=mean/std*np.sqrt(525600) if std else None,annual_calmar=mean*525600/mdd if mdd else None,annual_sortino=mean/downside.std()*np.sqrt(525600) if len(downside)>1 and downside.std() else None)
    return metrics,actions,rewards,fees


def save_evaluation(agent,frame,path,suffix=''):
    path=Path(path);path.mkdir(parents=True,exist_ok=True)
    metrics,actions,rewards,fees=evaluate(agent,frame)
    for name,value in [('action',actions[None,:]),('reward',rewards[None,:]),('final_balance',[metrics['profit']]),('require_money',[metrics['required_capital']]),('commission_fee_history',[metrics['fees']])]:
        np.save(path/f'{name}{suffix}.npy',value)
    (path/'metrics.json').write_text(json.dumps(metrics,indent=2,allow_nan=False))
    return metrics
