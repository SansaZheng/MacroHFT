# Local storage after archival

The user requested publication and removal of local MacroHFT data on
2026-11-24. `SansaZheng/MacroHFT` remains the canonical archive. This request
does not authorize modifying other FinancialAD projects or remote jobs.

Before removing the full local checkout, verify all current published branch
snapshots by streaming their actual GitHub blobs and comparing Git object
hashes. The archive manifest additionally records SHA-256 hashes and original
file sizes. Large datasets are real gzip parts, not external links.

Retain a shallow, blob-filtered sparse checkout containing code, documentation,
CQ specifications, the archive manifest and cleanup receipts. It deliberately
omits datasets, checkpoints, training logs and archive parts. Their absence in
the local sparse checkout is not a deletion from GitHub. The runtime
qualification and archive qualification branches remain published remotely.

Restore on authorized `/date` or `/data` storage with sufficient free space:

```sh
git clone https://github.com/SansaZheng/MacroHFT.git /data/zyy/MacroHFT
cd /data/zyy/MacroHFT
python3 scripts/restore_archive.py --allow-partial --destination .
```

Replace the example directory with an available authorized project directory;
do not overwrite an existing experiment. A full clone downloads archived data.
Avoid `git sparse-checkout disable` on the space-constrained Mac because it
would download the omitted data again. `verify_source.py` checks the complete
runtime snapshot, so use it after restoring the needed runtime files, rather
than claiming that the deliberately incomplete sparse checkout can train.

The original iCloud tree currently consists almost entirely of nonresident
placeholders. Its 66 pending files have not been retrieved, so they are
preserved. Native download requests were accepted, but bounded reads still
timed out. No iCloud cloud copy is deleted by local cleanup. Four source files
previously reconstructed from pinned upstream remain explicitly identified in
the manifest. Remote final experiment artifacts remain unretrieved.

See `results/archive-cleanup-20261124/` for the scope, pending list, verification
and actual cleanup outcome. This is a partial archival state, not a claim that
every historical experiment or iCloud file has been recovered.
