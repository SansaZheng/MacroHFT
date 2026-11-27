> Historical procedure. Its assets live at commit
> `23a4d58191b223227c142fa715bec104bb9e97c0`, not the current code-only tree.
> Use [the remote/HF workflow](storage/WORKFLOW.md) for new work.

# Reproduce the archived setup

This is a recovery procedure, not a report of completed retraining. The two
completed Kaggle jobs validate source identity and archival tools only.

1. Through CQ, first recover legacy inventory and final artifacts. The lab
   operator must allow `SansaZheng/MacroHFT`. Inspect current fleet, ownership,
   disk and existing MacroHFT work before using the prepared inventory spec.
   Do not submit duplicate training or assume that missing local logs mean a
   remote run failed. `cq/legacy-inventory-c225.json` is prepared, not executed.
2. Use a **new isolated checkout on authorized `/date` or `/data` storage**.
   Existing project directories and environments must remain intact. Check
   space for both the Git archive and reconstructed data before staging.
3. Check out the verified archive revision and verify actual project identity:

```sh
git checkout --detach db1f9d6ee2416db09874a822be99e60e631712b5
python3 scripts/verify_source.py --expected-commit db1f9d6ee2416db09874a822be99e60e631712b5
python3 scripts/patch_official.py --expected-commit db1f9d6ee2416db09874a822be99e60e631712b5
```

4. In that isolated remote checkout, restore the large data into the paths used
   by the archived runner. This explicitly acknowledges the incomplete legacy
   snapshot and checks the original hashes of every available file:

```sh
python3 scripts/restore_archive.py --root . --destination . --allow-partial
```

The three raw ETH splits and three whole prepared splits are available. Missing
small decomposition chunks remain listed; do not claim expert training from
scratch is qualified by the released-checkpoint reproduction. The four rebuilt
source files are identified in the manifest and reconstruction receipt.

5. Recreate/qualify an isolated runtime against the archived environment reports
   (`results/remote-environment.txt`, `results/cluster/runtime-provenance.json`).
   These reports are evidence, not a tested package lock for a new machine. Run
   `python3 tests/test_reproduction.py` there before training. Its ten tests
   include checkpoint loading, accounting, memory behavior and accelerated
   versus original rollout equivalence. **These ten runtime tests were not
   rerun during the November recovery; do not substitute the eleven tooling
   tests for them.**
6. After the legacy audit determines which runs are actually missing, use the
   preserved validation-frozen protocol: reference and combined, seeds 12345,
   2024, 42, 15 epochs. `scripts/run_experiment.py` passes `--skip_test` during
   training. Preserve old outputs and use distinct restarted-run directories.
   Final test access remains gated on frozen selection and verified checkpoints;
   recover already completed final evaluations instead of automatically rerunning.

Record each CQ specification, actual code SHA, dependency versions, input hashes,
seed, run status, costs/resources and output hashes. Fetch outputs and append
them to GitHub with the archive tools. Method development must use separate
versioned protocols and retain failures. See RESEARCH-GATES.md for the remaining
scientific evidence; there is no submission-ready manuscript yet.
