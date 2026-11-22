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
  CQ job j-1123-7725b2 completed: six identity and five archive tests passed,
  with fetched receipts; no training or market evaluation.
- Lab CQ submission rejected SansaZheng/MacroHFT at the repository-owner policy.
  Operator allowlisting is required before legacy lab recovery. No training
  resumed, no held-out market test was evaluated, no paid resources were rented.

Next: finish and verify the expanded GitHub archive, collect the new CPU
qualification receipt, then recover legacy artifacts through CQ when the lab
policy permits this repository. Preserve frozen validation selection; only
missing experiments may be resumed after artifact and environment checks.
