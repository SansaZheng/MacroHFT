# MacroHFT research upgrade status

Client date: 2026-10-14, Asia/Singapore. Goal: original, reproducible research toward CCF A submission quality. KDD is provisional. No acceptance or finished-paper claim.

Stage 005 audit/pilot completed: primary-literature novelty audit; separate causal cost-transport prototype; six meaningful tests; nine SHA256-verified public archives (388,800 minute rows, 17,852,203 bytes); 84 validation settings on BTC/ETH/SOL; 500 activity-matched random schedules for each of 12 asset/cost cells; visually inspected diagnostic figure. Reserved July-September 2026 months were not downloaded or evaluated.

Decision: do not promote cost transport plus distance/dispersion rejection as a new full RL method. Accounting is correct, but generic successor-feature novelty is already covered. The guard is often cash-like, and nominal-fee results do not establish an advantage over equally sparse trading. Negative results are preserved. This prototype has no learned MacroHFT experts and is not comparable with the original 39.28% test benchmark.

Original remote experiment status: UNKNOWN. SSH c225 and alternate c220ts both timed out. The last local training snapshot is from October 2, not current evidence. No new server training was launched; no remote job was stopped. Full final-results retrieval and bulk experiments require a working authorized SSH route. No paid rental or credential storage occurred.

Overall research objective: INCOMPLETE. Next: restore SSH and retrieve six final test artifacts; establish a distinct falsifiable mechanism for delayed-feedback memory validity; integrate and compare with matched MacroHFT and recent methods; then train, review and write only supported claims. Full coverage, paired training seeds, execution stress, independent review and a finished manuscript remain pending.

Artifacts:
- [Task specification](prompts/005-research-upgrade.md)
- [Literature audit](literature.md)
- [Method diagnostic](../../research/cost-transport-memory-v1/docs/method.md)
- [Pilot report](../../research/cost-transport-memory-v1/docs/pilot-report.md)
- [Completion gates](../../research/cost-transport-memory-v1/docs/impact-and-gates.md)

中文：已完成文献审计、代码、六项测试和三市场小实验，保留了不支持简单方向的负结果。目前还没有达到 CCF A 投稿条件。服务器连接失败，原复现最终结果无法核实；需要恢复实验室 VPN/Tailscale 或提供可用 SSH 入口。完整新方法、严谨对比和论文仍待完成。

## 2026-10-15 — CQ disabled by user

Do not use CQ for subsequent work. No active CQ jobs matched MacroHFT/FinancialAD during the bounded queue audit. No cancellation was performed. Other projects exist in the shared queue; cancellation scope clarification is pending. Direct SSH experiment status remains unverified; this instruction does not establish that those non-CQ jobs stopped.

## 2026-10-20 — CQ restored

User reauthorized CQ, superseding the October 15 ban. Configuration revision 5. Current job j-1020-197b77: queued; waiting for the first placement pass. This is a new read-only legacy inventory, not resumed training. Exact-work history for MacroHFT, macrohft and FinancialAD was empty; no matching active jobs were found in the full queued/assigned/running listings. The latest 1,000 cancelled records also had no matches; this is not a claim that all historical cancellations were inspected.

The original SSH training completion remains unknown. Inventory uses one CPU, no GPU, 0.25 GiB RAM, three-minute maximum runtime and zero cloud spend. No other project's historical cancelled job was restarted. Training is gated on verified legacy artifacts and environment/smoke checks.

# CQ resume status — 2026-10-20

CQ is enabled by the user; configuration revision 5 supersedes the October 15 ban.

Stage 006 executor: Codex/CQ. Status: blocked on a verifiable remote code snapshot, not on permission to use CQ.

The queue and fleet were inspected. Exact project labels MacroHFT, macrohft and FinancialAD had no prior CQ jobs. No active job metadata matched this project. No other project cancellation was reversed and no paid provider was used.

A new bounded CPU inventory j-1020-197b77 was accepted and assigned to c225. The launch was declined before any attempt: pinned commit 31e5ef41f93b2aea6e63e6ae2267675c997a8e54 could not be verified because /date/zyy/macrohft-reproduction/vendor/MacroHFT is not a Git repository. This does not prove that data/results are missing. The unusable diagnostic was cancelled; final CQ state is cancelled, attempts 0. No inventory ran and no training resumed.

Prepared artifacts: results/cq-resume-20261020/inventory.py, inventory-c225.spec.json, queue-audit.json, launch-failure snapshot job-j-1020-197b77.json and final job-final.json.

Next prerequisite: provide a correctly pinned code snapshot accessible to CQ (a project Git repository or an independently verified directory manifest), rerun the bounded read-only inventory, fetch original training/results/checkpoints, then submit only missing work behind environment/smoke checks. Local FinancialAD has no configured Git remote; no MacroHFT repository was found by the connected GitHub repository search. Preserve all legacy files.

Original reproduction scores and final training status remain unknown. The completed component pilot remains negative/mixed; overall CCF A research objective remains incomplete.

中文：CQ 使用授权已恢复，队列和资源已检查。检查作业被 CQ 接受，但因旧源码缺少 Git 元数据而在启动前拒绝；已撤回该作业。训练并未恢复，需先补齐可核验的代码快照。没有修改其他项目作业或旧实验文件。

[Active task specification](prompts/006-cq-resume.md)


## 2026-11-23 — verified publication and CQ CPU recovery

# Versioned recovery — 2026-11-23

Active prompt 007, executor Codex, configuration revision 6. KDD remains provisional;
research route cost-transport-memory-v1 remains unpromoted. No CCF A readiness claim.

- GitHub archive: https://github.com/SansaZheng/MacroHFT . Active checkout is
  /Users/zyy/.local/share/macrohft/repository, outside iCloud.
- Commit b243af03c62dc7c819484cfe02d21402da20dcda was pushed, independently
  downloaded into a fresh bare clone, and 227 actual Git objects passed SHA-256.
  It represents 208 original files / 1,010,231,907 bytes. The disposable clone
  was removed after recording the verification receipt to preserve local disk.
- A larger snapshot is prepared; inspect data-archive/manifest.json and the
  latest GitHub verification receipt for its verified extent. Pending files and
  reconstructed source are explicit; remote final training artifacts are missing.
- CQ job j-1123-5f1786 completed on free Kaggle CPU: source manifest verified,
  five archive tests passed, 4.355 seconds, child peak RSS 29,175,808 bytes.
- Actual project-commit verification replaces the invalid assumption that vendor
  has its own Git metadata. Six local source-identity regression tests passed;
  CQ job j-1123-7725b2 is submitted to qualify this new verifier remotely.
- Lab CQ submission rejected SansaZheng/MacroHFT at the repository-owner policy.
  Operator allowlisting is required before legacy lab recovery. No training
  resumed, no held-out market test was evaluated, no paid resources were rented.

Next: finish and verify the expanded GitHub archive, collect the new CPU
qualification receipt, then recover legacy artifacts through CQ when the lab
policy permits this repository. Preserve frozen validation selection; only
missing experiments may be resumed after artifact and environment checks.


## 2026-11-23 — final verified recovery checkpoint

# Recovery checkpoint — 2026-11-23

Prompt 007; executor Codex/CQ; configuration revision 6. Provisional KDD target.
Research route cost-transport-memory-v1 remains unpromoted; CCF A goal incomplete.

Completed: actual project source identity repaired and checked (51 runtime
artifacts); six identity and five archive tests pass in CQ job j-1123-7725b2.
Earlier CQ archive job j-1123-5f1786 also completed. Both outputs were fetched;
no paid compute, model training or held-out market evaluation occurred.

GitHub: https://github.com/SansaZheng/MacroHFT . Verified data/archive revision
is db1f9d6ee2416db09874a822be99e60e631712b5: 433 files / 1,289,504,736 represented
bytes. All 454 Git objects are covered by new remote SHA-256 checks or identical
Git blobs in the independently downloaded baseline. Current documentation and
verification receipts are published in a subsequent small commit.

Partial archive remains explicit: 66 legacy files pending iCloud retrieval;
four source files reconstructed from official upstream plus the recorded patch;
remote final training artifacts not retrieved. Local working checkout:
/Users/zyy/.local/share/macrohft/repository (outside iCloud).

Blocked: lab CQ code.git allowlist rejects SansaZheng/MacroHFT. The CQ operator
must allow that exact repository. Prepared next step: cq/legacy-inventory-c225.json,
with queue/host/storage checks before submission. Recover legacy final artifacts
and qualify the isolated runtime before resuming only missing experiments.

The two CQ qualification jobs are finished; no training job is running from
this recovery work. New method gains, full fair comparisons, execution stress,
independent paper review and a submission-ready manuscript remain unestablished.
See docs/REPRODUCE-FROM-ARCHIVE.md, docs/RESEARCH-GATES.md and
 docs/NOVELTY-UPDATE-20261123.md for reproducible steps and scientific constraints.


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


## 2026-11-23 — authorized compute route established

The user authorized SuuTTT/MacroHFT as the CQ compute fork, synchronized with
SansaZheng/MacroHFT. This resolves the old repository-owner blocker.
Read-only lab inventories are accepted but await scheduler reservations;
numerical qualification retries remain separate from training. Current job
states, evidence and limitations: [current.md](current.md). No scientific
readiness claim and no automatic restart of legacy training.


## 2026-11-27 — recovered negative ETH comparison and v2 diagnostic

The old final result is no longer unknown: exact-hash summary retrieved via CQ;
reference mean 37.685867%, combined -0.491520%. Raw six-trial reconciliation is
active in j-1127-458f37. New v2 baseline diagnostic passed nine tests and records
all 1200 synthetic score rows; it is not a new RL method. See current.md for
active state, source audit, limitations and next evidence gates.
