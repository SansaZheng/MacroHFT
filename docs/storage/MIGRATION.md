# GitHub / Hugging Face / remote execution migration

Status: code-side migration implemented; HF authentication, namespace, repository discovery,
write permission and account storage headroom are not established. No HF asset upload
or private-repository creation has been performed. A null revision is a blocker, not
an implied `main` revision. Existing private repositories cannot be discovered anonymously.

## Preservation and authority

- Code: https://github.com/SansaZheng/MacroHFT; compute mirror:
  https://github.com/SuuTTT/MacroHFT. Reuse both repositories.
- Historical archive commit: `23a4d58191b223227c142fa715bec104bb9e97c0`.
  Current-tree untracking preserves this commit, every original and previous evidence.
  It does not remove shared history or reclaim its disk space.
- `assets/legacy-git-assets.json` inventories 316 paths removed from current tracking,
  approximately 1.18 GB of known stored payloads (compressed shards counted as stored).
  `data-archive/manifest.json` remains an explicitly historical snapshot, not the current
  Git tree. Use that old commit for old restore/verification tools.
- The historical original-file inventory describes 1,408,351,584 bytes, including
  116,639,138 bytes in 66 historically pending iCloud items. A fresh local read-only
  audit now recovered hashes for 64 of these (116,632,452 bytes); two legacy-tooling
  copies are still absent at their recorded paths. These recovered bytes are not yet HF-backed. These totals overlap the stored-payload
  total and must not be added together. Newly readable local files are not yet independent backups; see `local-pending-audit.json`.
- c225 original inputs: `/date/zyy/macrohft-reproduction`; prior c224 setup:
  `/date/zyy/macrohft-cluster`. Read-only audit is through CQ. Shared caches and other
  users' jobs are untouched. Only job-specific CQ output directories receive writes.
- HF targets will be private Dataset and Model repositories in the authenticated,
  user-confirmed namespace. Inspect existing repositories before choosing names.
  Preserve upstream notices; no new license is assigned. Upstream data/expert rights
  remain a review item; private backup permission is not a public redistribution license.

## Asset organization

`assets/manifest.json` is the machine-readable migration ledger. Each verified asset
must have repo_id, repo_type, immutable 40-character HF revision, required paths,
file sizes and SHA-256. The corresponding source archive commit, config, seeds and metrics
are retained for six selected hyper-agent models. Original training Git commits were
not recorded; the seven source hashes establish a narrower source correspondence.
Do not relabel the archive commit as the original execution commit.

Dataset layout: `original/ETHUSDT/{train,val,test}/`,
`prepared/ETHUSDT/{train,val,test}/`, `features/`, `decomposition/ETHUSDT/`,
and `research/cost-memory/`. Original Feather files are 85–274 MB and already
practical split-sized shards. Preserve their exact bytes before any Parquet conversion;
never silently replace them. Monthly ZIP source archives remain separate by market/month.
Split dates and original hashes are in `assets/splits.json`; preprocessing code is in
`scripts/prepare_data.py` and `vendor/MacroHFT/preprocess/decomposition.py`.

Model layout: six released experts under `released/ETHUSDT/`; six validation-selected
hyper-agent weights under `hyperagent/ETHUSDT/{variant}/seed-{seed}/`.
The remote audit found six epoch-15 final weights in addition to six selected best
weights. All 193 selected server files (1,278,333,903 bytes) passed a read-only SHA-256
audit in CQ job `j-1127-794ac6`; final-model hashes are now recorded. No separately
named optimizer/RNG/replay resume snapshot was found in the bounded inventory.
A weights-only file is not a full optimizer/RNG replay recovery checkpoint. Retain
best, final and genuine restart state; do not upload every epoch. Preserve failed-method
selected weights because they support the published negative comparison.

## Migration gates and historical cleanup

1. Authenticate securely and inspect existing repositories/permissions and actual
   included storage remaining. Do not buy storage or use paid overflow.
2. Confirm private-backup rights for third-party inputs and experts. Stage explicit
   file lists on remote storage; verify SHA-256 before upload.
3. Upload only selected files; capture the returned full commit; stream it back through
   an independent verification request. Model manifests bind verified dataset revisions.
4. From a clean remote checkout and empty project-specific cache, download selected
   pinned assets and run the runtime check. Preserve the receipt and environment versions.
5. Verify an independent second backup (existing server originals or a separately
   verified archive). Only then propose deletion of local originals/caches.
6. Shared Git history rewrite is a separate approval decision. If later authorized:
   record all refs, make and verify a bundle on remote backup storage, produce an exact
   filter-repo path list from the migration ledger, review changed commit mappings,
   coordinate both owners, and replace shared refs only in an agreed maintenance window.
   No force-push, history rewrite, original deletion or shared-cache deletion is part
   of this implementation.

## Client compatibility

Official `huggingface_hub==1.8.0` was installed temporarily for API-signature inspection
and public streaming verification. Upload behavior is covered by mocked tests, not a
live private upload; live authentication/write qualification is still pending. The uploader uses `upload_folder(..., parent_commit=...)`
with explicit file allowlists in batches of at most 50. Rerunning compares remote SHA-256
(or streams small Git files), skips matching files, and retries remaining batches.
Xet handles transport deduplication. A failed final verification does not produce a
verified manifest. No deprecated `resume_download` or unsupported future-client flags.

The pinned client has no `get_storage_report` API. A quota observation must be taken
from authenticated HF storage settings and recorded with namespace, time, source and
included free bytes remaining. The uploader refuses observations older than 24 hours
and requires 10% headroom. No public quota is assumed to be private quota.

The original iCloud project currently occupies about 1.49 GiB on disk, including about
1.29 GiB under vendor and 169 MiB in its old virtual environment. These are preserved
until independent backups and asset migration are verified. This differs from the earlier
mostly-dataless state; metadata and read checks were repeated rather than assumed.

## Current qualification limits

Local asset tooling has 25 passing tests; source identity has six passing tests. GitHub
Actions checks code-only tracking, source hashes and these tests. The immutable public
HF transport fixture was streamed and verified locally without downloading a model.
The first c225 clean-checkout job failed because system ensurepip was unavailable;
the isolated PyPA bootstrap fixed that step, but package installation then hit DNS
resolution errors. An alternate CQ placement on c219 failed its code fetch; c224's
CPU queue reserved remaining capacity for GPU work, so our own queued probe was cancelled.
No other job was stopped. Failed attempts are recorded, not counted as passes.

The original c225 project interpreter has `huggingface_hub==0.36.2`; it was inspected
read-only and lacks the pinned uploader's write-permission API. Its read path needs the
existing OS CA bundle, selected only by job environment variables with TLS verification
still enabled. The normal cached download returned an empty file. SHA-256 verification
rejected it, as documented in `verification/j-1128-2f35cf/diagnostic.json`. The fetcher
now retries that integrity failure once with an official-client unbuffered stream,
reads at most the expected size plus one byte, and publishes only fully verified bytes.
It does not mutate a suspect shared cache. Fresh 1.8.0 installation subsequently passed in `j-1128-7b3618` (see retry below);
live private upload qualification remains blocked by account access. No shared DNS, certificate store or existing
environment was modified.

References: [official HF upload guide](https://huggingface.co/docs/huggingface_hub/guides/upload),
[HF storage accounting](https://huggingface.co/docs/hub/storage-limits),
[official pip bootstrap guidance](https://pip.pypa.io/en/stable/installation/).

## Personal checkout inspection

Use `git status --short` and `git ls-tree -r --name-only HEAD` for local inspections.
In a partial clone, size/diff operations that need missing historical blobs can fetch
those blobs automatically. This audit encountered that behavior; approximately 273 MiB
of historical Git objects remain locally and were not deleted. Subsequent size inventory
used the GitHub tree API, without fetching asset bytes. Avoid full-history clones and
old-asset diffs on the Mac. This remaining object storage is separate from the roughly
2.2 MB current tracked code/evidence tree and the 1.49 GiB preserved original project.

## Completed clean remote check — 2026-11-28

CQ job `j-1128-452f42` completed on c225 from a new GitHub checkout at
`99529f6edd1b37bd630ce5305e51cb6c7e1553be`: 51 source hashes, 25 asset-workflow tests,
and nine synthetic causal-gate tests passed. It retrieved only `config.json` (548 bytes)
from [the public transport fixture](https://huggingface.co/hf-internal-testing/tiny-random-bert/tree/f171d7baecaf37b5da5a3616d8833b9969753535),
pinned at `f171d7baecaf37b5da5a3616d8833b9969753535`. Downloaded-file and independent
stream verification both matched SHA-256
`54f9f0001ec62b6a53072a7c9d1b630e346ae51fca14a5799e54f0d918281872`.

The 3,470-byte [receipt](verification/j-1128-452f42/receipt.json) has SHA-256
`c2c0790a85c81d807065e4086fd2c8291057f4db11d4c1ae24ee1d1579b6a74f`, matching CQ's
output verifier. The [check summary](verification/j-1128-452f42/checks.json) identifies
the retained remote log. Job-owned scratch code/assets/cache were removed after success;
only small diagnostics were collected locally. Existing environments and originals stayed intact.

This verifies public pinned transport and minimal execution, **not** a private MacroHFT
asset restoration or paper reproduction. No project HF repository URLs/revisions can
be reported yet. The remaining inputs are the HF namespace, secure project authentication,
actual included private storage headroom, and private-backup rights for upstream data/experts.
The temporary personal HF tooling environment was removed (33,296,384 allocated bytes);
no original data or historical Git objects have been deleted.

## Requested retry — 2026-11-28

CQ job `j-1128-7b3618` successfully built a fresh isolated official HF 1.8.0 environment
on c225 and repeated the clean pinned code checkout, 51 source hashes, 25 asset tests,
nine synthetic tests, and public pinned file download plus independent streaming
verification. Runtime was about 307 seconds. The earlier package-installation blocker
is cleared for this observed run. Existing OS CA verification stayed enabled.
[Receipt](verification/j-1128-7b3618/receipt.json) and
[checks/dependency versions](verification/j-1128-7b3618/checks.json) are archived.

A fresh credential check still found no project HF login on the Mac, in CQ secrets,
or at the checked c225 project/default locations. No token contents were read and no
private asset was uploaded. Account/repository discovery, permission/quota verification,
private-backup rights review and actual asset migration remain pending. The successful
client setup is not an authenticated upload test. Only this job's disposable scratch
was removed; project originals and shared environments remain unchanged.
