# Method review update — 2026-11-23

Executor: Codex. Primary-source pages checked today. This is an abstract-level
update, not a completed implementation comparison or an external-model review.
Recent-search window: 2025-11-23 to 2026-11-23; foundational work is marked.

| Primary work | Date / status | Verified scope | Consequence (our inference) |
|---|---|---|---|
| [META](https://arxiv.org/abs/2609.28771) | Submitted September 23, 2026; arXiv reports AACL-IJCNLP Findings acceptance | Financial multi-agent decisions with episodic retrieval and regime-conditioned signal reuse | Memory retrieval plus regime-aware fusion alone is not a new contribution. |
| [MOIRA v2](https://arxiv.org/abs/2605.01954v2) | Submitted May 3; revised October 16, 2026; preprint | Hierarchical LLM policies for pair selection/execution, using trajectory and episode feedback under delay | Hierarchy, memory and delayed feedback as broad ingredients are already occupied. Numerical RL and pair-trading tasks are not interchangeable baselines. |
| [Optimism and Delays](https://proceedings.mlr.press/v206/howson23a.html) | AISTATS 2023; foundational | General episodic-RL updates with delayed information and regret analysis | Updating only after information arrives is a causality requirement, not itself a novel algorithm. |

The next hypothesis must therefore be narrower: can action-specific, locally
matched **out-of-sample prediction residuals** determine when retrieved value
estimates should be discounted after a change in conditional returns? Every
residual must use a prediction recorded before its outcome; delayed outcomes
must enter at their availability time. Maintain the original cost accounting
and policy class while testing this mechanism, so improved returns cannot be
attributed solely to fee changes or less trading.

This is a research question, not an implemented or verified new method. Before
promoting it, compare no-memory, fixed-distance gating, recency decay and simple
delayed online expert weighting under equal search budgets. Include matched
turnover/exposure controls, opposite and recurrent regime changes, and horizons
with different feedback delays. A negative or activity-only result rejects the
hypothesis. No bound for arbitrary market drift is claimed.

The existing 84-setting pilot and its negative/mixed activity controls remain
archived. No new held-out results, ten-baseline coverage or novelty certification
are implied by this literature update.

中文：最新文献进一步排除了把“记忆、层级结构、延迟反馈”拼接起来就视为创新。
下一步应验证更具体的残差驱动记忆可靠性机制，并与简单在线重加权公平比较。
在旧实验回收、方法实现及完整验证完成之前，尚不能认定达到 CCF A 投稿水平。
