# 008b — Portable numerical runtime qualification

Local task specification; executor Codex/CQ; configuration revision 7.
The host-specific legacy inventories are accepted but blocked by normal CQ
CPU/RAM reservations. Perform independent qualification while they wait.

Run the existing ten reproduction regression tests, unchanged, using six
released experts and deterministic synthetic train/validation fixtures only.
Use a pinned code-only branch mirrored to both authorized repositories. Create
an isolated environment under CQ_OUTPUT_DIR on free Kaggle CPU; do not modify
shared code or environments. Resource bound: one CPU, no GPU, 4 GB RAM, 4 GB disk,
15-minute maximum runtime, zero paid spend. No real market data, held-out tests,
model training, candidate selection or claimed numerical benchmark results.

Verify every code/weight hash; pin direct dependency versions; record actual
package freeze, source commit, timing, child RSS, fixture hashes and raw test
logs. Require all ten tests to pass. Fetch small receipts and synthetic fixtures,
then archive them in SansaZheng/MacroHFT and mirror the exact committed state to
SuuTTT/MacroHFT. Failure is diagnostic and must not be relabeled as success.

This is a different runtime qualification from the old lab environment; passing
it does not establish full reproduction or CCF A submission readiness.
