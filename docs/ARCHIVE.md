# Archive contract

Small files are stored directly in Git. Files larger than 40 MiB are losslessly
gzipped and split into parts of at most 32 MiB. They contain the actual bytes;
this does not require paid Git LFS storage. `data-archive/manifest.json` records
original sizes/hashes and part sizes/hashes. No manifest alone proves a backup.

```sh
# Refuses incomplete archives and verifies original decompressed bytes too.
python3 scripts/restore_archive.py --root .
# Restore large files outside the code checkout; differing files are preserved.
python3 scripts/restore_archive.py --root . --destination /date/zyy/macrohft-restored
# Meaningful integrity tests: round-trip, corruption, overwrite, path boundaries.
python3 tests/test_archive.py
# Explicit partial inspection (does not certify backup completeness).
python3 scripts/restore_archive.py --root . --allow-partial
```

Directly stored files remain in the checkout. `--destination` reconstructs the
large data files; configure data paths accordingly. The current build recipe is:

```sh
python3 scripts/prepare_github_archive.py --source /path/to/original-project --destination /path/to/git-clone
# Later: fill only small pending files; preserve published files and new code.
python3 scripts/fill_pending_archive.py --source /path/to/original-project --destination /path/to/git-clone
```

`--metadata-only` or `--skip-unavailable` are preparation modes. Pending bytes
make the archive incomplete and the verifier refuses it. A complete local
snapshot still excludes unknown remote training artifacts until they are
retrieved through CQ and independently verified.

Excluded: installed virtual environments, nested Git databases, symlinks,
system/cache files, active construction logs and third-party paper PDF/text
copies. Original publications are linked in RECOVERY.md. Upstream redistribution
rights are not expanded. Code, configurations, environment reports, data,
released expert weights, results, plots and negative evidence are preserved
when their bytes are available.

Before claiming GitHub persistence, verify the push, remote commit and objects.
The user's old iCloud-backed project is preserved; the new Git checkout used
for publication is outside iCloud to avoid repeated eviction while archiving.

The initial expanded snapshot b243af0 was downloaded into an independent bare
clone: 227 Git objects (910,717,268 stored bytes) passed SHA-256. Its receipt is
in results/recovery-20261123/github-b243af0-verification.json. Later verification
streams new/changed GitHub objects and checks unchanged Git blob IDs against
that verified baseline, avoiding a second full copy on a nearly full disk.

`reconstructed_from_upstream` names four source files recovered from a fresh
official checkout plus the recorded patch. They are executable source with
verified construction, not evidence that the legacy originals were retrieved.
The missing legacy files and unknown remote training artifacts prevent a claim
that every experiment is archived, even though all three raw ETH split files
and all three prepared whole-split files are now represented by real bytes.
