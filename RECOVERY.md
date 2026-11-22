# MacroHFT: recovery and reproducible research

This repository is the user-designated archive for the MacroHFT reproduction and
method-development project. It is being populated from preserved local evidence.
It does **not** establish reproduction of the published 39.28% ETH return or
CCF A submission readiness.

## Code identity

The upstream implementation is `ZONG0004/MacroHFT`, revision
`31e5ef41f93b2aea6e63e6ae2267675c997a8e54`. Our repairs and experiments have their
own Git commits in this repository. An upstream SHA must never identify a
modified or non-Git project directory.

The October 20 CQ diagnostic was rejected before execution because its legacy
source folder was not a Git repository. The new inventory entrypoint is a
standard-library script pinned by this repository's actual commit. It reads
only the specified legacy project directory and writes its report to
`CQ_OUTPUT_DIR`. It never starts, cancels or restarts training.

## Recovery sequence

1. Inspect CQ history, current resources and the authenticated GitHub destination.
2. Push and verify this repository's actual commit.
3. Submit the bounded CPU inventory through CQ with that commit and the required
   host-specific legacy directory. Confirm CQ permits this GitHub owner.
4. Fetch and verify the inventory, existing final summaries and checkpoints.
5. Preserve completed work. Qualify the environment and a small integration run
   before submitting only the missing experiments.
6. Keep the validation-selected candidate frozen. Never select a method using
   its held-out test result.

## Data and evidence archive

The intended archive includes original data, derived splits, released expert
weights, source patches, experiment specifications, logs, numerical results and
negative method-development diagnostics. Environment directories and nested Git
databases are not experimental data and are excluded. Third-party paper PDFs
are linked at https://arxiv.org/abs/2406.14537 and
https://personal.ntu.edu.sg/boan/papers/KDD24_MacroHFT.pdf.

Large files will be stored as lossless gzip parts, with checksums for each part
and the reconstructed original. This avoids requiring paid LFS storage. A
manifest alone is not a completed backup. Until all parts are pushed and
verified, data archival remains incomplete. Remote training artifacts are also
incomplete until retrieved from the original server.

## 中文状态

本仓库用于保存真实代码、数据、实验步骤与证据。原论文收益尚未完成独立核实，
现有新方法也尚未达到目标投稿水平。恢复顺序为版本校验、旧结果检查、环境与
冒烟验证、补跑缺失实验；不会覆盖旧结果或重新选择已冻结的测试方案。
