# RL integration audit — two kinds of stale information

This is a source-based diagnosis, not an experimentally established failure
cause. Inspected published vendor source at main db7ee166fdc7e601a3b95a2dd18e6260180ae335.

1. `high_level.py:372` queries memory during **training**. `act_test` mixes the
   six expert Q-values with the learned hyper-agent but does not query episodic
   memory. Adding online memory adaptation at test time changes the protocol;
   it is not a drop-in replacement for the existing memory regularizer.
2. The stored value is a one-step bootstrapped estimate formed using the current
   online network. The optimizer's TD target separately uses a target network
   and double-Q action selection. Both are estimates, not realized long-horizon
   ground truth. A gate must not treat self-generated bootstrap disagreement as
   an unbiased realized prediction error.
3. `memory.re_encode` refreshes stored hidden representations, but leaves stored
   Q labels unchanged. In addition, the queried `q_memory` is copied into replay
   transitions and reused later. Representation age, value-target model version
   and market/event age are distinct sources of staleness.

The causal ledger prototype covers outcome availability and immutable forecasts
only. It does not solve target-network version drift, selective actions, replay
reuse, or identify which of the two combined modifications caused the negative
historical result. Those conclusions require separate interventions.

Next discriminating training-only study: retain the original action support,
teacher fee, observation set and evaluation protocol. Log memory target age,
source network versions, nearest-neighbor distance and paired Bellman residuals
on a validation-only chronological window. Compare (a) no memory penalty,
(b) original frozen targets, (c) recency weighting, (d) synchronized target
refresh using stored reward/next-state/terminal data, and (e) conditional
reliability. Refresh is an essential simple baseline, not itself claimed novel.
No final-test access until the new selection protocol is frozen; never reuse
the now-observed 2023 ETH final period as unseen validation for this decision.

中文：原代码的记忆主要影响训练损失，并不在测试阶段直接检索。下一步需要区分
市场变化、表征更新和自举目标版本变化；简单增加“延迟残差门控”不能证明改进
了原方法，也不能直接解释 combined 的失败。
