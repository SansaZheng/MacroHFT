# CQ recovery runbook

## Verified state

The old job `j-1020-197b77` never executed: its non-Git source folder could not
prove the requested upstream commit. New recovery code was pushed successfully
to this repository at `6c164570461c269d04ed2cee719247beb3317d50`.

CQ rejected `code.git=SansaZheng/MacroHFT` with HTTP 400: only `SuuTTT` repositories
are allowed. No new job ID was issued. The CQ operator must permit this exact
repository. Do not evade the allowlist or use fabricated hashes or another
project's identity.

## Execution sequence after repository access is enabled

1. Inspect queue/fleet and current code SHA again. Pin the actual pushed commit.
2. Check home/storage placement before staging. The current CQ guide says c225
   `/data2` is full and new homes need `/data3`; the draft is not a verified
   storage allocation. Preserve the user's authorized large-storage constraints.
3. Run `scripts/cq_inventory.py` on c225 with root
   `/date/zyy/macrohft-reproduction`, then separately on c224 with root
   `/date/zyy/macrohft-cluster`. Diagnostic envelope: 1 CPU, 0 GPU, 0.25 GiB RAM,
   0.01 GiB output, 3-minute runtime. These are bounds, not training measurements.
4. Require `inventory.json` and `progress.log` with 6/6. Fetch through `cq fetch`.
   Inspect individual file errors: inventory_complete does not prove data exists.
5. Retrieve final summaries, frozen selection, all run receipts and checkpoints.
   Verify hashes. Do not reinterpret historical status as a live process check.
6. Preserve completed trials. The frozen candidate is combined; reference and
   combined need seeds 12345, 2024, 42. Only seed-12345 validation chose the method.
   Never choose again using test outcomes. Recover an existing final evaluation
   rather than automatically repeating it.
7. Build isolated environment through CQ, then integration smoke, then only
   missing training with dependencies. Measure CPU/RAM/GPU/time before scaling.
   Upstream checkpoints omit replay/memory/optimizer/RNG; incomplete runs cannot
   be described as exact continuations. Preserve partials and label restarts.
8. Report six final evaluations, all seeds, mean/sample standard deviation,
   failures and protocol limitations. Archive actual data/checkpoints/logs.

No other users' jobs, environments or files are to be modified. Paid cloud
usage remains disabled until this project has an explicit spending ceiling.
