# Evidence audit: MacroHFT

## Verified sources and artifacts

- Published paper downloaded from the author's NTU page, KDD 2024, DOI 10.1145/3637528.3672064, and arXiv version 2406.14537. Both PDFs and extracted text are saved under `paper/`; the reported ETH results and experiment settings agree.
- Official repository commit `31e5ef41f93b2aea6e63e6ae2267675c997a8e54`.
- Authors' public Google Drive ETH split files, SHA256 and row counts in `results/data-audit.json`.
- Six released ETH checkpoints (three trend and three volatility specialists), all loaded successfully with `weights_only=True`.

## Published benchmark (literature values, not reproduced results)

| Market | MacroHFT TR (%) | ASR | ACR | ASoR | AVOL (%) | MDD (%) |
|---|---:|---:|---:|---:|---:|---:|
| BTC | 3.03 | 0.61 | 2.06 | 0.34 | 18.19 | 5.41 |
| ETH | 39.28 | 3.89 | 8.41 | 2.49 | 20.93 | 9.67 |
| DOT | 13.79 | 0.97 | 2.45 | 0.68 | 40.31 | 15.89 |
| LTC | 18.16 | 1.50 | 3.11 | 0.66 | 29.59 | 14.24 |

ETH EarnHFT TR is 18.02%. The paper describes minute-level cryptocurrency trading, not exchange-latency execution. It compares eight other methods. The release is an ETH demonstration, not the complete four-market baseline experiment suite.

## Data and protocol

Raw train/validation/test counts are 525,600 / 172,800 / 220,320. Timestamps are strictly increasing, unique, minute-spaced, and disjoint; all numeric columns are finite. Published ETH dates match the downloaded splits. Feature lists contain 36 single-period and nine context features. Official whole-series preprocessing drops 360 initial rows per split, leaving 525,240 / 172,440 / 219,960. Equivalent linear-filter preprocessing matches 20 sampled reference windows per split within 1.1e-14 absolute slope error.

Fee 0.02%; long/flat actions, maximum holding 0.2 ETH. The released simulator uses current close for fills, with no slippage and no terminal liquidation fee. Its return is profit divided by ex-post maximum cash requirement, not a declared fixed initial portfolio balance. All-cash paths have undefined upstream capital-normalized return; the evaluation records a null return and treats zero economic profit as zero for model selection. This exception is documented rather than hidden.

## Diagnosed source issues

1. Both trainers store a state dictionary then call `.state_dict()` on that dictionary, which would fail at final saving.
2. The selected dictionary shares tensor storage unless deep-copied, so later optimization can overwrite the supposed best checkpoint.
3. The high-level final test passes a file path into code that appends `/trained_model.pkl`.
4. High-level subagent paths are ETH-specific even when another dataset name is supplied.
5. Demonstrations charge 0.001 while the environment charges 0.0002. Preserved in the reference, changed only in the fee-aligned experiment.
6. Memory chooses five neighbors before masking actions; a lookup can have no matching neighbors. Original behavior falls back to the current bootstrap estimate. Action-conditioned retrieval is a separate method change.
7. Subagent advantage centering uses a batch-global mean. Preserved during training; accelerated inference reproduces single-observation behavior, not the incorrect batch-global inference behavior.
8. Cash requirement computation sums every prefix separately, giving quadratic runtime. Replaced with cumulative sums.
9. Paper equation (9) and code exchange alpha/beta assignments for memory and imitation loss; source behavior is retained. Paper policy dimension 128 also differs from the released subagent head width 256.
10. Complete feature-generation code and checkpoint training logs/seeds are absent from the release. The supplied input feature causality and expert selection cannot be independently certified from these artifacts.

## Implemented method hypotheses

- Action-conditioned nearest-neighbor memory may avoid uninformative bootstrapping when locally nearest experiences use a different action. This can also retrieve more distant, less relevant states and hurt performance.
- Fee-aligned demonstrations may reduce the teacher/student objective mismatch. Lower assumed costs may increase turnover and hurt robustness.
- Their interaction is measured through the combined variant. These are hypotheses, not proven improvements.

## Validation and limitations

Ten tests cover source checkpoint compatibility, snapshot independence, original memory equivalence, action-conditioned retrieval behavior, teacher-cost effects, known cash P&L, one-state versus batched Q evaluation, cached batch-centering, sequential versus fast rollout, and equivalent training environments for both initial positions. Three real-data smoke jobs completed (reference, combined changes, accelerated reference): two epochs on 4,608 training rows and 2,048 validation rows. All returned 4.5818734835% on that short validation prefix. This is neither the paper's test period nor evidence of improvement. Accelerated reference took 90.0 seconds locally versus 194.8 seconds for the direct reference run; this is an uncontrolled timing observation, not a performance benchmark.

The full registered pipeline uses released experts, four initial configurations, then two extra seeds for the chosen candidate and reference, followed by sealed test evaluation. As of this audit, full results are pending. BTC/DOT/LTC data, eight competing baselines, from-scratch expert training, and independent feature reconstruction remain unreproduced. No claim of surpassing the paper is supported.

## 中文解释

官方数据日期与论文一致，六个子智能体检查点可以加载；训练脚本有模型保存和最佳模型快照错误，已修复并测试。提出的两项调整是“先按动作筛选再检索近邻”和“统一示范策略与环境手续费”，效果必须以完整验证/测试实验为准。短序列测试只证明代码能够运行，不是论文结果。公开仓库未提供其他三个币种的数据及完整基线，因此不能把本轮 ETH 超智能体复现实验描述成整篇论文全部复现。

## First full epoch (interim, validation only)

Both seed-12345 runs completed epoch 1 on all 525,240 prepared training rows and evaluated all 172,440 validation rows. Reference validation TR = 16.1582863841%, MDD = 11.6460930931%; combined-method validation TR = 16.4819940444%, MDD = 4.9545339033%. Artifact: `results/first-epoch-validation.json`, traced to the server validation JSONL files. Both runs entered epoch 2. The test set has not been evaluated; these numbers cannot be compared directly with the paper's 39.28% test return.

中文：完整数据第一轮训练已完成，验证收益率为原方法 16.16%、组合调整 16.48%；这只是验证集初步结果，不代表超过论文测试集。后续训练和多种子实验仍在运行。


## Distributed execution update

At 2026-10-02T13:07:20.274722+08:00, the reference and combined seed-12345 runs have completed 15 epochs. Their best full-validation returns are 28.0383373276% and 44.6061500003%, respectively; these are validation-only measurements, not the paper’s June–October test result. The two ablations remain active, so candidate selection is not yet frozen. Eight speculative extra-seed trials now run on five separately verified private worker environments. These additional outcomes are excluded from candidate selection. The final benchmark remains pending.

中文：原始方案与组合调整的最佳完整验证收益率分别为 28.04% 和 44.61%，均不是论文测试集结果。其余消融及新增种子实验仍在运行，候选方法尚未冻结，不能用这些验证收益声称超过论文。


## Storage incident and recovery

On 2026-10-02, c203 exhausted its shared root filesystem despite about 79 GiB available at launch. Both seed-42 jobs failed with ENOSPC after 12/13 validated epochs, and the controller stopped at 17:12 +08. This was discovered at the next user-requested status check, 23:48 +08. Six completed training trials are preserved. The combined candidate was frozen at 15:49 using only original-seed validation; no test evaluation occurred. Failed trial artifacts were preserved on c203 and archived read-only to c225. Only the two failed trials are restarted with identical settings on c224’s spacious /date volume, with periodic storage guarding. Full three-seed results remain pending.


## Research upgrade, 2026-10-14

Three assets and four fee levels were evaluated with all 84 component/control settings retained. Cash-like and negative findings do not establish an improved MacroHFT or CCF A contribution. See ../../research/cost-transport-memory-v1/docs/pilot-report.md for bilingual analysis. Remote final results remain unknown due unavailable SSH.

中文：已完成三市场组件验证，结果不支持将简单成本迁移与拒绝机制作为原创完整方法；未触碰新测试集。
