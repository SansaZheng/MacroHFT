# 006 — Resume CQ and audit legacy experiments

Local task specification; executor: Codex; configuration revision 5.
Goal: restore CQ authorization, avoid duplicate submissions, and recover the true status of MacroHFT experiments before launching missing training. KDD remains provisional; the research route is unchanged.
Inputs: existing workflow state, cluster plan, CQ queue/resource status, legacy c225 /date/zyy/macrohft-reproduction and c224 /date/zyy/macrohft-cluster.
Procedure: inspect project queue/history; submit bounded standard-library CPU inventory jobs against existing pinned source where available; retrieve status/results receipts. Never alter legacy experiments or start their old SSH coordinator. Do not restart other projects' cancelled jobs or rent paid capacity.
Initial envelope: 1 CPU, 0 GPUs, 0.25 GiB RAM, 0.01 GiB disk, at most 3 minutes per inventory. This is a conservative diagnostic allocation, not a measured training allocation. Only small JSON inventory/results; no dataset/checkpoint copies.
Success: verified project CQ entries and fetched inventories, or an exact queue/input blocker; config and state reconciled. Training is gated on input/completion audit and a separate environment/smoke qualification.
