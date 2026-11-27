# Current research state — 2026-11-27

Executor: Codex/CQ. Configuration revision 8. KDD provisional.
Route: delayed-memory-validity-v2, diagnostic only; novelty unproven.

## Completed this invocation

- Retrieved completed c224/c225 CQ inventories. Recovered four original JSON
  files with exact source SHA-256/size matches, including the final ETH summary.
- Recomputed six trial returns/aggregates. Reference mean 37.685867%, combined
  mean -0.491520%; paired mean difference -38.177387 percentage points. Reference
  seed 12345 is 39.280827%, rounding to the published 39.28%. ETH hyper-agent
  scope only; individual trial/checkpoint reconciliation is still pending.
- Implemented a causal delayed-feedback baseline ledger; nine tests passed.
  Frozen synthetic diagnostic: 240 streams x five predictors, 1200 score rows,
  8.773 seconds. Local conditioning helps the constructed local/recurrent cases
  and hurts stationary/global cases. No market performance or novelty claim.
- Source audit distinguishes market/event staleness, representation updates,
  stale bootstrapped Q labels, and cached replay targets. A test-time gate would
  alter the original protocol because memory is queried during training.

## Active

CQ j-1127-458f37: assigned; assigned to c225; copying project macrohft-recovery from c224 to c225.
Last checked: 2026-11-27T10:46:00.198593+00:00.
This is a read-only collection, not a training/evaluation job. It will retrieve
six checkpoints and per-trial metrics, and hash existing trajectory arrays.
[Prompt 009](prompts/009-evidence-recovery.md).

Stage 010 diagnostic completed; [prompt](prompts/010-delayed-validity-screen.md),
[report](../../research/delayed-memory-validity-v2/docs/report.md).

## Next evidence gates

Verify collected model hashes and per-trial metrics; preserve the negative
combined result. Before integrated training, implement and compare simple
value-target refresh, no-memory and equivalent contextual weighting baselines
under a frozen validation-only protocol. Do not reuse the observed 2023 ETH
final period for selecting a new method. Reserved 2026 test data remain unseen.
All-market/from-scratch reproduction, independently established novelty,
robust market gains and a submission-ready manuscript remain incomplete.

Local checkout remains sparse; no market data were downloaded. 66 original
iCloud files remain pending/preserved. No paid compute or other-user job change.
