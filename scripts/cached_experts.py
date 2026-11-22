"""Cache frozen expert computations without altering their batch centering rule."""
import numpy as np
import torch
from torch import nn


class ExpertCache:
    def __init__(self, experts, frame, features, trend_features, batch_size=2048):
        self.experts=experts
        x=frame[features].to_numpy(dtype=np.float32)
        c=frame[trend_features].to_numpy(dtype=np.float32)
        keys=np.concatenate([x,c],axis=1)
        self.index={row.tobytes():i for i,row in enumerate(keys)}
        self.values=np.empty((len(frame),2,6,3),dtype=np.float32)
        self.last=None
        with torch.no_grad():
            for start in range(0,len(frame),batch_size):
                end=min(start+batch_size,len(frame))
                xx=torch.from_numpy(np.repeat(x[start:end],2,axis=0))
                cc=torch.from_numpy(np.repeat(c[start:end],2,axis=0))
                prev=torch.arange(2).repeat(end-start)
                for j,e in enumerate(experts):
                    conditioning=e.embedding(prev)+e.fc2(cc)
                    shift,scale=e.adaLN_modulation(conditioning).chunk(2,dim=1)
                    h=e.norm(e.fc1(xx))*(1+scale)+shift
                    adv=e.advantage(h)
                    value=e.value(h)
                    raw=value+adv
                    stored=torch.cat([raw,adv.mean(dim=1,keepdim=True)],dim=1)
                    self.values[start:end,:,j]=stored.numpy().reshape(end-start,2,3)

    def lookup(self,x,c,previous):
        if self.last is not None and x is self.last[0] and c is self.last[1] and previous is self.last[2]:
            return self.last[3]
        keys=np.concatenate([x.detach().cpu().numpy(),c.detach().cpu().numpy()],axis=1)
        indices=[self.index.get(row.tobytes(),-1) for row in keys]
        if min(indices)<0:
            self.last=None
            return None
        result=self.values[indices,previous.detach().cpu().numpy()]
        self.last=(x,c,previous,result)
        return result


class CachedExpert(nn.Module):
    def __init__(self,original,cache,index):
        super().__init__()
        self.original=original
        self.cache=cache
        self.index=index

    def forward(self,x,c,previous):
        result=self.cache.lookup(x,c,previous)
        if result is None:
            return self.original(x,c,previous)
        result=torch.from_numpy(result[:,self.index,:]).to(x.device)
        # The official *training* implementation subtracts a global batch mean.
        return result[:,:2]-result[:,2].mean()


def install(agent,frame):
    if agent.device.type!='cpu':
        raise ValueError('Cached CPU runtime requires --device cpu')
    experts=[agent.slope_agents[i] for i in range(3)]+[agent.vol_agents[i] for i in range(3)]
    cache=ExpertCache(experts,frame,agent.tech_indicator_list,agent.tech_indicator_list_trend)
    for i in range(3):
        agent.slope_agents[i]=CachedExpert(experts[i],cache,i)
        agent.vol_agents[i]=CachedExpert(experts[i+3],cache,i+3)
    return cache
