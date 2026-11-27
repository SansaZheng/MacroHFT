# Delayed feedback mechanism screen — 2026-11-27

Status: diagnostic baseline implemented and tested; no new RL method or market
advantage established. Local execution: Codex, standard library only. No Gemini
or Claude invocation, no lab training, no market-data download. The protocol
file was recorded before the first run; this is not external preregistration.

Two fixed predictors output +1 and -1. Targets begin near +1 with Gaussian
noise (SD 0.1). After step 400, all cells or only context=1/action=1 change to
-1; the recurrent case switches that cell back at step 800. Context/action
labels are observable and sampled independently; they are not latent-regime
labels or policy decisions. The labels arrive after 1, 16 or 64 steps.

The conditional gate is a simple contextual delayed expert-weighting baseline.
It stores immutable pre-outcome forecasts, compares clipped squared errors only
at label availability, and discounts each observation by its prediction age.
Its neutral prior returns when evidence becomes stale. Global weighting uses
the identical rule and parameters with all keys pooled. Neither is claimed new.

20 seeds x 4 scenarios x 3 delays = 240 synthetic streams, each with five
predictors (1,200 score rows). Nine causal/invariance tests passed. Execution
was 8.773 seconds; every row and source/protocol hash is retained.

## All scenario means (MSE; lower is better)

| Scenario | Delay | Global weighting | Conditional weighting | Conditional − global |
|---|---:|---:|---:|---:|
| stationary | 1 | 0.010713 | 0.013086 | +0.002373 |
| stationary | 16 | 0.023160 | 0.025571 | +0.002410 |
| stationary | 64 | 0.062735 | 0.065636 | +0.002901 |
| local_switch | 1 | 0.671521 | 0.065428 | -0.606093 |
| local_switch | 16 | 0.683969 | 0.089268 | -0.594701 |
| local_switch | 64 | 0.723543 | 0.171732 | -0.551811 |
| global_switch | 1 | 0.216287 | 0.220682 | +0.004395 |
| global_switch | 16 | 0.278617 | 0.283116 | +0.004499 |
| global_switch | 64 | 0.478495 | 0.485957 | +0.007462 |
| recurring | 1 | 0.345164 | 0.117679 | -0.227485 |
| recurring | 16 | 0.357612 | 0.154443 | -0.203169 |
| recurring | 64 | 0.397186 | 0.278381 | -0.118805 |

## Decision and limits

Conditioning helps on the deliberately local and recurrent drift constructions,
but is worse on every stationary and global-switch mean. Splitting evidence
across four keys increases cold-start cost and estimation sparsity. Delay hurts
both rules. The generator was constructed to test these properties, so a large
local-drift gain is a sanity result, not evidence of real-market prediction.

The single-key test establishes that this gate collapses exactly to the global
baseline when conditioning disappears. It does not establish an advantage over
an equivalent contextual online expert weighting method. A fresh methodology
claim would need more than this rule. No calibrated uncertainty guarantee,
causal explanation of the historical combined failure, or trading gain follows.

Before RL integration: define a common value-target horizon; log forecasts
before outcome arrival; audit selected-action feedback and censoring; avoid
model-update leakage in bootstrap targets; and match costs, exposure and search
budget. Original ETH final results are now observed and cannot be reused as an
unseen selection set. The reserved 2026 market periods remain unaccessed.

中文：已实现并验证“只能用已到达反馈”的对照组件。局部变化的合成场景受益，
但稳定及全局变化场景更差。该实验支持检查局部失效和反馈时间，不能证明交易
收益，也不能作为新算法的创新性证据。保留全部结果，不挑选有利条件。
