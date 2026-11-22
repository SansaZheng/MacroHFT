# Cost-transported memory: diagnostic, assumptions and research gap

Status: implemented component prototype, not a new full RL algorithm. The six released MacroHFT experts are not used in this pilot. A separate integration and equal-budget retraining study is required.

For a fixed, price-taking trajectory, store gross marked P&L G and traded notional U, both normalized by entry exposure. Linear two-sided fee c gives R(c) = G − cU. For one long round trip with entry p and exit p′, G = p′/p − 1 and U = 1 + p′/p. This identity follows directly from cash accounting. It is a special case of successor-feature reward decomposition, not an original contribution. It does not transfer optimal actions, nonlinear execution dynamics, or market impact.

The prototype retains only training trajectories whose exit precedes every validation query. Features use closed bars only. Standardization and the support threshold are fitted on training states. It retrieves k=32 neighbors, revalues each trajectory at the queried fee, and computes a weighted mean. A separate guarded variant subtracts one heuristic standard error and rejects queries whose k-th neighbor exceeds the training 95th-percentile radius. Serial dependence and concept drift invalidate an iid confidence interpretation: the guard is not a calibrated confidence bound and gives no profit/safety guarantee.

Execution is explicit: a decision after bar t closes executes at bar t+1 open, holds 60 minutes, and liquidates at the next block boundary. Units are fixed at 25% of initial USD 100,000 capital divided by the first execution price. Purchases require sufficient cash; no borrowing is silently introduced. Every entry and exit pays fees. Return uses fixed initial capital; drawdown uses marked bar-close equity plus exit equity. No queue, spread, latency beyond the one-bar decision convention, or nonlinear impact is modeled. These assumptions are more auditable than same-close fills but not evidence of realistic HFT execution.

The three memory variants isolate stale scalar labels, cost transport, and support/dispersion rejection. Cash, repeated long blocks, momentum and reversal are diagnostic controls. They are not seven literature baselines. A policy can appear safer simply by not trading, so participation and the cash control are mandatory.

## What an original extension would still need

1. Establish that memory failure is caused by identifiable conditional-distribution or execution changes, not just weak predictive features. Covariate novelty is insufficient when the same feature state acquires a new return law.
2. Learn or test transportability using only matured feedback. A gate cannot know an unobserved regime change immediately; any theorem must state its information, drift and boundedness assumptions.
3. Integrate the mechanism into MacroHFT's expert mixing and Bellman targets, with checkpointed replay/memory/optimizer/RNG and per-run isolation. No such integration is claimed here.
4. Compare with the closest successor-feature and nonstationary-RL approaches under matching observations, costs, budgets and dates. Reject the proposal if its advantage disappears with equal participation or realistic execution.
5. Provide independent unseen-period, unseen-asset and cost/latency stress evaluation. Retain every failed candidate and freeze the final protocol before test access.

中文：这不是“已改进成功”的方法论文，而是用来否证错误研究方向的实验组件。代数上正确的成本换算，并不等于能预测收益，也不等于方法创新。
