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
