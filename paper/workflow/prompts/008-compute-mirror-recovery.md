# 008 — Authorized compute fork and CQ experiment recovery

Local task specification; executor Codex/CQ; configuration revision 7.
Date: 2026-11-23. Venue and scientific route unchanged (provisional KDD;
cost-transport-memory-v1 is still an unpromoted diagnostic).

Goal: use the user-authorized SuuTTT/MacroHFT compute fork to recover experiments
through CQ while retaining SansaZheng/MacroHFT as the code/data/result archive.
Reuse the existing fork, inspect ancestry and expected heads, and synchronize
without force-overwriting concurrent work. Pin actual full commits in every job.

Inputs: verified archive commits, recovered source, CQ queue/fleet, preserved
legacy c224 /date/zyy/macrohft-cluster and c225 /date/zyy/macrohft-reproduction.
First execute bounded read-only inventories on the correct host. Use isolated
CQ project home on c224's /date local disk. Preserve other users' work, shared
environments, existing trial outputs and frozen validation selection. No paid
resources without a project budget. Do not infer completed experiments from
historical logs, and do not relabel restarts as exact resumptions.

Outputs: mirrored commit receipts, accepted CQ jobs and fetched inventories,
recovery decisions, environment/integration qualification and only missing
experiments where prerequisites pass. Synchronize real results and all critical
steps to the canonical archive after checking hashes. Full scientific readiness
remains unproven until the remaining research gates are met.
