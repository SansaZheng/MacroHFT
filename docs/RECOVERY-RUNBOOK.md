# CQ recovery runbook

## Verified state

The old job `j-1020-197b77` never executed: its non-Git source folder could not
prove the requested upstream commit. New recovery code was pushed successfully
to this repository at `6c164570461c269d04ed2cee719247beb3317d50`.

CQ rejected `code.git=SansaZheng/MacroHFT` with HTTP 400: only `SuuTTT` repositories
are allowed. No new job ID was issued. The CQ operator must permit this exact
repository. Do not evade the allowlist or use fabricated hashes or another
project's identity.

CQ's separately documented Kaggle CPU backend accepted pinned GitHub code.
Job j-1123-5f1786 completed and its results were fetched: four source hashes and
five archive-integrity tests passed. It did not access lab files or train a model.
The follow-up j-1123-7725b2 qualifies six new source-identity regression tests;
consult its fetched receipt for completion. Both jobs prohibit rentals/paid spend.

## Source identity after recovery

The published vendor tree is already patched and does not need nested `.git`.
Pass the actual full **project** commit from the CQ specification:

```sh
python3 scripts/verify_source.py --expected-commit "$SOURCE_COMMIT"
python3 scripts/patch_official.py --expected-commit "$SOURCE_COMMIT"
```

The second command verifies the already patched tree without changing it.
For an independently cloned official checkout, use `--repo /path/to/fresh/clone`;
the script verifies that directory is the exact Git root and has the pinned
upstream commit before applying the recorded patch. It cannot borrow the parent
project's Git identity. Missing/altered source or an altered manifest fails closed.

## Execution sequence after repository access is enabled

1. Inspect queue/fleet and current code SHA again. Pin the actual pushed commit.
2. Check home/storage placement before staging. The current CQ guide says c225
   `/data2` is full and new homes need `/data3`; the draft is not a verified
   storage allocation. Preserve the user's authorized large-storage constraints.
3. Run `scripts/cq_inventory.py` on c225 with root
   `/date/zyy/macrohft-reproduction`, then separately on c224 with root
   `/date/zyy/macrohft-cluster`. The prepared c225 diagnostic declares 1 CPU,
   0 GPU, 1 GB RAM, 4 GB disk including code staging, and 6 minutes. These are
   conservative bounds, not measured training requirements. Confirm host/storage
   placement before submission; `prefer` is not a hard host constraint.
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
