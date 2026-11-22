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
```

Directly stored files remain in the checkout. `--destination` reconstructs the
large data files; configure data paths accordingly. The current build recipe is:

```sh
python3 scripts/prepare_github_archive.py --source /path/to/original-project --destination /path/to/git-clone
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
