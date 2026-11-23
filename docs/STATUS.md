# Recovery status — 2026-11-23

GitHub SSH write access works. The expanded archive contains all raw ETH splits,
all whole prepared ETH splits, released experts, available local training logs,
the three-market pilot and its negative/mixed diagnostics. Large files contain
real lossless bytes with hashes. The manifest still lists 66 missing legacy
files; four additional source files were reconstructed from pinned upstream plus
the recorded patch. Remote final training artifacts remain unretrieved.

The original b243af0 upload was independently downloaded and all 227 Git objects
verified. The expanded archive db1f9d6 passed original-file/part SHA-256 checks and
remote verification: 433 files / 1,289,504,736 represented bytes, 454 Git objects.
Of those, 234 new/changed remote objects were streamed and hashed; 220 unchanged
Git blobs were tied to the independently verified baseline. The receipt is
results/recovery-20261123/github-db1f9d6-verification.json.

CQ jobs j-1123-5f1786 and j-1123-7725b2 completed on free Kaggle CPU and were
fetched. Five archive tests and six source-identity regression tests pass. The
new source verifier uses the actual project commit and 51 runtime artifact
hashes; nested vendor Git metadata is not needed. Four missing source files
were rebuilt from the official pinned commit and historical patch. These are
engineering checks, not model-training or trading-effectiveness evidence.

Lab CQ rejected code.git=SansaZheng/MacroHFT at its repository-owner allowlist.
The CQ operator must enable that exact repository before legacy inventory and
training recovery. No lab policy, other users' jobs or shared environment was
changed. No paid compute was used. There are no active MacroHFT training jobs
established by this recovery work.

Next: complete missing-byte archive, enable the lab repository, recover original
final artifacts, qualify the environment, then run only missing experiments
under the frozen protocol. New-method implementation, paired comparisons,
execution stress and a submission-ready manuscript remain incomplete. No CCF A
readiness claim. See NOVELTY-UPDATE-20261123.md and RESEARCH-GATES.md.

中文：已完成 GitHub 部分数据归档、真实代码身份修复和两次 CQ CPU 验证。
实验室白名单仍阻塞旧结果回收与训练恢复；没有把通过工具测试当成方法有效。


## User-requested retry — 2026-11-23 06:57 UTC

Authenticated accounts verified: the GitHub connector is SuuTTT; the local
Git SSH account is SansaZheng. Existing repository pushes use the latter and
work. The earlier connector push=false report is not a blocker to publication.

The exact prepared lab inventory was submitted again after checking the queue
and fleet. CQ returned HTTP 400: only repositories of SuuTTT can be cloned on
the lab servers (got SansaZheng). No job ID was issued, and no training started.
The remaining prerequisite is CQ operator permission for SansaZheng/MacroHFT,
not GitHub write permission. Receipt:
results/recovery-20261123/lab-retry-20261123T065712Z.json.
