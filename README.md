# MacroHFT reproduction and research extension

This repository preserves code, data and evidence for reproducing
[MacroHFT (KDD 2024)](https://arxiv.org/abs/2406.14537) and testing extensions.

**2026-11-27: ETH final artifacts recovered and reconciled.** Reference seed
12345 returns 39.280827%; three-seed reference mean is 37.685867%. The combined
modification fails, averaging -0.491520%. All six metrics/checkpoints and seven
source files are archived; no test was rerun. Full reproduction, a successful
new method and CCF A readiness remain incomplete.

- [Recovered evidence and limitations](docs/EVIDENCE-RECONCILIATION-20261127.md)
- [New causal diagnostic: mixed synthetic outcomes](research/delayed-memory-validity-v2/docs/report.md)

- [Recovery and provenance](RECOVERY.md)
- [CQ compute fork and archive synchronization](docs/COMPUTE-MIRROR.md)
- [CQ recovery runbook](docs/RECOVERY-RUNBOOK.md)
- [Reproduce the archived setup](docs/REPRODUCE-FROM-ARCHIVE.md)
- [Archive verification](docs/ARCHIVE.md)
- [Research completion gates](docs/RESEARCH-GATES.md)
- [Current recovery status](docs/STATUS.md)
- [Workflow status](paper/workflow/current.md) and [latest novelty review](docs/NOVELTY-UPDATE-20261127.md)

The upstream source revision is `31e5ef41f93b2aea6e63e6ae2267675c997a8e54`.
New recovery and modified training code have their own commits here. Four
unavailable source files were reconstructed from the pinned upstream plus the
recorded patch; that provenance is explicit. The upstream SHA must not identify
modified code. `code-provenance.json` binds the runtime files to this project.

The initial reproduction retrains the hyper-agent with six released ETH
experts. It does not reproduce all four markets or expert training from
scratch. A separate three-market cost-memory diagnostic is a validation
prototype; it is not the paper's test protocol or a complete new RL method.
Its mixed and negative evidence is retained.

中文：本仓库保存真实代码、实验数据、结果和步骤。ETH 六组最终指标与模型已核对，
原方法 seed 12345 与论文收益四舍五入后一致，combined 改进失败；新方法尚未达到投稿目标。数据归档以实际文件上传和校验成功为准；清单中的
pending 项表示文件仍未完整归档，不能当成已备份。


## Local storage — 2026-11-24

Archived data remain in this GitHub repository. The Mac now keeps a small sparse
code/documentation checkout; verified local data copies and their full Git
object database were removed to free space. The 66 unavailable iCloud files
remain explicitly pending and preserved. See [storage and restore steps](docs/LOCAL-STORAGE.md)
and [cleanup receipt](results/archive-cleanup-20261124/cleanup-result.json).
