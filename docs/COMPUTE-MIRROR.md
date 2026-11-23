# Compute and archive repositories

The user authorized this arrangement on 2026-11-23:

- `SansaZheng/MacroHFT` remains the canonical code, data, result and documentation
  archive. Local Git SSH authenticates as SansaZheng.
- `SuuTTT/MacroHFT` is the CQ compute fork. It already existed when this stage
  began; the authenticated GitHub connector has write access as SuuTTT.
- Main branches are synchronized by fast-forwarding to the **same full commit**.
  Compute branches are also published to both repositories. No independent code
  changes are hidden only in the compute fork.

## Synchronization procedure

1. Inspect both current heads and the local worktree. Preserve concurrent changes.
2. Commit code/data/results to the canonical archive and push using its existing
   SSH authentication. Verify the remote commit.
3. Through the SuuTTT GitHub connection, update the compute ref with the observed
   `expected_sha`, `force=false`, and the canonical commit. For a new compute
   branch, create it at that exact published commit. Shared fork history makes
   the same Git objects available without copying credentials.
4. Verify both remote refs match. If a head changed unexpectedly, inspect it
   before retrying; never force-overwrite another session's work.
   If a new commit is not yet visible in the fork, a cross-fork draft PR can
   expose the exact change for review; retry the guarded fast-forward only
   after verifying the heads. PR #1 records this recovery. A successful SSH
   dry run does not establish fork write permission; the actual push was
   denied, so fork writes continue through the SuuTTT connector.
5. CQ lab specs use `code.git=SuuTTT/MacroHFT` and an actual full pushed commit.
   Kaggle specs use `code.github=SuuTTT/MacroHFT`. Jobs stay pinned if main moves.
6. Fetch completed CQ outputs, verify provenance and hashes, archive failures
   alongside successes, then repeat the same synchronization. This procedure
   runs during active work; it is not an installed background synchronization
   service.

## Recovery execution

Dedicated project home: `macrohft-recovery`, source host c224. CQ maps its home
to c224's `/date/sudingli/cq-home` local disk. The c224 and c225 metadata checks
are restricted to their respective hosts because their legacy inputs are local.
They read `/date/zyy/macrohft-cluster` and `/date/zyy/macrohft-reproduction` and
write only to their own CQ output directories. No legacy job is restarted or
cancelled by these checks. Current resource reservations may delay placement;
free physical RAM/CPU does not override CQ's per-host reservation policy.

The independent code-only runtime qualification branch contains the existing ten
reproduction tests, unchanged, plus six released experts. Its wrapper creates
deterministic synthetic fixtures and an isolated CPU environment entirely under
CQ_OUTPUT_DIR. No real market data, model training or held-out test evaluation
is performed. Passing it is useful numerical compatibility evidence, but a lab
environment still needs its own qualification before production experiments.

Do not launch the old SSH-based cluster orchestrator under CQ. It starts remote
work and writes fixed legacy paths. A resumed experiment must use isolated CQ
outputs, preserve partials, and avoid repeating any final evaluation recovered
from the old artifacts. The frozen candidate/seed protocol remains unchanged.

Local free disk is currently below the archive tools' 2 GiB safety threshold.
Large missing files and future results must stay on verified server storage
until a safe archival route is available. A manifest or queued job is never
reported as completed data retrieval. No paid compute is authorized by this
two-repository arrangement.

中文：计算仓库负责提供 CQ 允许的源码入口，归档仓库继续保存代码、数据、结果
和步骤；两边用相同提交标识对应。已解除仓库所有者限制，但调度等待、旧结果
回收、运行环境验证和正式训练仍需分别记录，不能合并宣称“实验已恢复完成”。
