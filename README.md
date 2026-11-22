# MacroHFT reproduction and research extension

This repository preserves code, data and evidence for reproducing
[MacroHFT (KDD 2024)](https://arxiv.org/abs/2406.14537) and testing extensions.

**2026-11-23: research remains incomplete.** Final original-test results have
not been recovered. Neither improvement over the published 39.28% ETH return
nor CCF A submission readiness has been established.

- [Recovery and provenance](RECOVERY.md)
- [CQ recovery runbook](docs/RECOVERY-RUNBOOK.md)
- [Archive verification](docs/ARCHIVE.md)
- [Research completion gates](docs/RESEARCH-GATES.md)
- [Current recovery status](docs/STATUS.md)
- Legacy workflow documents and source: pending hydration; see the archive manifest.

The upstream source revision is `31e5ef41f93b2aea6e63e6ae2267675c997a8e54`.
New recovery code has its own commits here. Legacy modified training source
is still being recovered. The upstream SHA must not identify modified code.

The initial reproduction retrains the hyper-agent with six released ETH
experts. It does not reproduce all four markets or expert training from
scratch. A separate three-market cost-memory diagnostic is a validation
prototype; it is not the paper's test protocol or a complete new RL method.
Its mixed and negative evidence is retained.

中文：本仓库保存真实代码、实验数据、结果和步骤。复现最终成绩仍待核实，
新方法尚未达到投稿目标。数据归档以实际文件上传和校验成功为准；清单中的
pending 项表示文件仍未完整归档，不能当成已备份。
