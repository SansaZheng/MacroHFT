"""Array-backed equivalent of the authors' training environment.

Keep the original cash-accounting, initial-position, fee, and terminal mark-to-
market conventions, including their limitations. This is a runtime change.
"""
import numpy as np
try:
    from numba import njit
except ImportError:
    def njit(*args,**kwargs):
        return lambda fn: fn


@njit(cache=True)
def teacher_table(prices,holding,fee,gamma=0.99):
    q=np.zeros((len(prices),2,2))
    for t in range(len(prices)-2,-1,-1):
        for previous in range(2):
            for action in range(2):
                if action>previous:
                    buy=(action-previous)*holding*prices[t]*(1+fee)
                    reward=prices[t+1]*(action*holding)-(prices[t]*(previous*holding)+buy)
                else:
                    sell=(previous-action)*holding*prices[t]*(1-fee)
                    reward=prices[t+1]*(action*holding)+sell-prices[t]*(previous*holding)
                q[t,previous,action]=reward+gamma*max(q[t+1,action,0],q[t+1,action,1])
    return q


class ArrayTrainingEnv:
    def __init__(self,df,tech_indicator_list,tech_indicator_list_trend,clf_list,transcation_cost=0.0002,back_time_length=1,max_holding_number=0.2,initial_action=0,alpha=0,teacher_cost=0.001):
        if back_time_length!=1: raise ValueError('Only the released back_time_length=1 protocol is supported')
        self.single=df[tech_indicator_list].to_numpy()
        self.trend=df[tech_indicator_list_trend].to_numpy()
        self.regime=df[clf_list].to_numpy()
        self.prices=df.close.to_numpy()
        self.initial_action=initial_action
        self.max_holding_number=max_holding_number
        self.comission_fee=transcation_cost
        self.q_table=teacher_table(self.prices,max_holding_number,teacher_cost)

    def observation(self,action):
        i=self.m-1
        return self.single[i:i+1],self.trend[i:i+1],self.regime[i],{'previous_action':action,'q_value':self.q_table[i,action]}

    def reset(self):
        self.m=1
        self.previous_position=self.initial_action*self.max_holding_number
        self.position=self.previous_position
        self.sell_money_memory=[]
        self.needed_money_memory=[]
        self.comission_fee_history=[]
        self.reward_history=[0.]
        return self.observation(self.initial_action)

    def step(self,action):
        old=self.previous_position
        position=self.max_holding_number*action
        i=self.m-1
        previous_price=self.prices[i]
        current_price=self.prices[i+1]
        if old>=position:
            size=old-position
            cash=size*previous_price*(1-self.comission_fee)
            self.sell_money_memory.append(cash)
            self.needed_money_memory.append(0.)
            reward=current_price*position+cash-previous_price*old
        else:
            size=position-old
            cash=size*previous_price*(1+self.comission_fee)
            self.sell_money_memory.append(0.)
            self.needed_money_memory.append(cash)
            reward=current_price*position-cash-previous_price*old
        self.comission_fee_history.append(self.comission_fee*size*previous_price)
        self.reward_history.append(reward)
        self.position=position
        self.previous_position=position
        self.m+=1
        done=self.m==len(self.prices)
        if done:
            true_money=np.asarray(self.sell_money_memory)-np.asarray(self.needed_money_memory)
            self.required_money=-np.min(np.cumsum(true_money))
            self.final_balance=np.sum(true_money)+current_price*position
        x,c,r,info=self.observation(action)
        return x,c,r,reward,done,info
