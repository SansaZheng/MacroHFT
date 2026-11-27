# Remote-first workflow (official HF client 1.8.0)

Run compute, migrations and transfers through CQ, on the authorized local disk of the
assigned lab server. The commands below are commands for a CQ job unless marked as an
interactive credential setup. Do not change shared environments, cache locations or
other users' runs. Never put credentials in a CQ spec, Git config, shell history or logs.

## Code and dependencies

Use a new shallow checkout; fetching old history would fetch the old data archive too.
For a pinned production CQ job, `code.git` and `code.commit` perform the checkout.
For an independent clean check:

```bash
export MACROHFT_WORK="$CQ_OUTPUT_DIR"
mkdir -p "$MACROHFT_WORK"
git init "$MACROHFT_WORK/code"
git -C "$MACROHFT_WORK/code" remote add origin https://github.com/SuuTTT/MacroHFT.git
git -C "$MACROHFT_WORK/code" fetch --depth=1 --filter=blob:none origin FULL_CODE_COMMIT
git -C "$MACROHFT_WORK/code" checkout --detach FETCH_HEAD
cd "$MACROHFT_WORK/code"
python3 scripts/create_asset_env.py --root "$MACROHFT_WORK/asset-env"
export PYTHON="$MACROHFT_WORK/asset-env/bin/python"
export MACROHFT_ASSET_ROOT="$MACROHFT_WORK/assets"
export MACROHFT_HF_CACHE="$MACROHFT_WORK/cache/hub"
export HF_HUB_CACHE="$MACROHFT_HF_CACHE"
export HF_XET_CACHE="$MACROHFT_WORK/cache/xet"
export PIP_CACHE_DIR="$MACROHFT_WORK/cache/pip"
```

The bootstrap uses a SHA-256-pinned official PyPA get-pip script and installs pip
inside the new environment only; it works without distro ensurepip. It refuses an
existing environment path. `requirements/assets.txt` pins the official HF client.

`HF_HOME` must point to an already-authorized, private credential directory **outside
CQ_OUTPUT_DIR and any uploaded/collected folders** if login is persisted. Set the HF
cache variables above separately. Do not reuse another lab user's login. An injected
HF_TOKEN from an approved secret manager is also supported; do not include its value in
specifications or commands. For an interactive owner terminal only:

```bash
# HF_HOME must already be a private credential directory approved for this project.
"$MACROHFT_WORK/asset-env/bin/hf" auth login
"$PYTHON" scripts/assets.py audit --namespace YOUR_CONFIRMED_NAMESPACE
```

The audit reports identity, token role and matching accessible repositories, never
credential contents. Check the account/organization's authenticated Storage settings.
Record this JSON under your private remote work directory (not a token):

```json
{
  "namespace": "YOUR_CONFIRMED_NAMESPACE",
  "checked_at": "ACTUAL_UTC_TIME_WITH_OFFSET",
  "source": "Authenticated HF Storage settings, observed by account owner",
  "included_free_bytes_remaining": 0,
  "charges_authorized": false
}
```

Zero is intentionally blocking. Replace it only with an actual current quota observation;
never treat a plan's advertised capacity as available capacity. Quota must be less than
24 hours old; uploads require 10% headroom. The tool locks and records conservative
byte reservations in this quota file before remote mutations, including failed/interrupted
attempts. Reconcile a fresh authenticated storage observation before releasing reservations.
Use one shared project quota record for concurrent uploads; never duplicate quota files
to multiply the same capacity. No upgrade or paid overflow is automated.

## Upload original data and selected models

First inspect the current ledger and remote inventory. Reuse existing HF repos discovered
by the audit. Create at most a private dataset repo and a private model repo if no suitable
project repos exist. Record private-upload authorization per asset based on actual rights;
no new license is assigned. No project HF repo exists in this workflow yet.

Prepare one logical asset at a time. The staging command checks source bytes and adds a
card and asset provenance; it does not alter originals or upload a directory indiscriminately.

```bash
"$PYTHON" scripts/stage_assets.py --asset eth-prepared \
  --legacy-root /date/zyy/macrohft-reproduction \
  --root "$MACROHFT_WORK/stage/dataset" \
  --output-manifest "$MACROHFT_WORK/upload-plan.json"
"$PYTHON" scripts/assets.py --manifest "$MACROHFT_WORK/upload-plan.json" upload \
  --asset eth-prepared --source "$MACROHFT_WORK/stage/dataset" \
  --repo-id YOUR_NAMESPACE/EXISTING_OR_APPROVED_DATASET_REPO \
  --quota-record "$MACROHFT_WORK/quota.json" \
  --output-manifest "$MACROHFT_WORK/verified-manifest.json"
```

Add `--create-repo` only on the first upload after discovery shows no suitable repository.
New repositories are always private. Existing public repositories are refused. No entire
working directory is uploaded: only the manifest's file list is sent in bounded batches.
On interruption rerun the same command with the same source; matching remote hashes are
skipped. Remote content is streamed back at the exact commit before a verified manifest
is produced. Stop if quota, source identity or concurrency checks fail.

For models, first merge the verified dataset/expert revisions into the input manifest.
Then use the same staging/upload commands with `--asset eth-reference-12345` and the
selected private model repo. Each model binds dataset revisions, config, seed, source
identity and metrics. Inspect final/recovery checkpoints before adding them; do not
upload every epoch. Full optimizer/RNG/replay resume state must be identified explicitly.

Review the generated verified manifest (no credentials). From the existing canonical
write-authorized code checkout, retrieve only that metadata and update GitHub:

```bash
cq fetch UPLOAD_JOB_ID --path verified-manifest.json
cp UPLOAD_JOB_ID/verified-manifest.json assets/manifest.json
python3 scripts/assets.py validate
# The uploader already streamed the pinned remote bytes before producing this manifest.
python3 scripts/check_git_policy.py
git add assets/manifest.json
git commit -m 'Pin verified HF asset revision and checksums'
git push origin main
```

Use the canonical write-authorized checkout for the final Git push and fast-forward the
compute mirror to the same commit. Never force-push over a changed head. The transfer tool
itself does not automatically mutate GitHub or rewrite history.

## Retrieve only the assets needed

These commands **fail until the relevant real HF revisions have been verified**:

```bash
"$PYTHON" scripts/assets.py fetch --asset feature-definitions --asset released-experts \
  --root "$MACROHFT_ASSET_ROOT" --cache-dir "$MACROHFT_HF_CACHE"
"$PYTHON" scripts/assets.py fetch --asset eth-prepared \
  --file prepared/ETHUSDT/train/data.feather --file prepared/ETHUSDT/val/data.feather \
  --root "$MACROHFT_ASSET_ROOT" --cache-dir "$MACROHFT_HF_CACHE"
# A single file rather than an entire logical asset:
"$PYTHON" scripts/assets.py fetch --asset eth-prepared \
  --file prepared/ETHUSDT/train/data.feather \
  --root "$MACROHFT_ASSET_ROOT" --cache-dir "$MACROHFT_HF_CACHE"
"$PYTHON" scripts/assets.py verify --asset eth-prepared \
  --file prepared/ETHUSDT/train/data.feather --file prepared/ETHUSDT/val/data.feather \
  --root "$MACROHFT_ASSET_ROOT"
# Streaming integrity check, without a persistent dataset copy:
"$PYTHON" scripts/assets.py stream-verify --asset eth-prepared --file prepared/ETHUSDT/train/data.feather
```

The file fetch does not fetch validation/test unless explicitly selected. A full asset
`verify` expects every declared file; do not confuse a partial download with completeness.
Feather inputs require local random-access files for the existing experiment. Streaming
verification is supported, but it is not a streaming training adapter. For a future
Parquet conversion, use bounded batches on the server, preserve original files, create
new derived-data identities and validate split boundaries before use.

## Minimal reproduction and experiments

Build a separate Python 3.11 numerical environment under CQ_OUTPUT_DIR, using
`requirements/research-cpu.txt`. This recipe records the prior numerical qualification;
new-host qualification is mandatory. A venv is job-local and must not be copied to another
host; persistent multi-host environments must use the CQ conda workflow.

```bash
python3.11 scripts/create_asset_env.py --root "$MACROHFT_WORK/research-env" --python python3.11
"$MACROHFT_WORK/research-env/bin/python" -m pip install --no-cache-dir \
  -r requirements/research-cpu.txt
# Transfer-client dependencies are not needed by the runner's local verify step.
"$MACROHFT_WORK/research-env/bin/python" scripts/remote_run.py \
  --asset-root "$MACROHFT_ASSET_ROOT" --work-dir "$MACROHFT_WORK/check" --check-only
"$MACROHFT_WORK/research-env/bin/python" scripts/remote_run.py \
  --asset-root "$MACROHFT_ASSET_ROOT" --work-dir "$MACROHFT_WORK/run-seed12345" \
  --variant reference --seed 12345 --epochs 1 --device cpu
```

The runner exports only committed code into an empty run directory, links verified inputs,
records code and asset revisions plus the exact selected paths, and writes results there.
It links only train/validation splits; final test inputs are not required or linked. It preserves the original
`--skip_test` behavior. Do not re-evaluate observed final test periods for method selection.
Increase epochs or request GPUs only after the CQ resource/environment smoke gates pass.

## Recoverable-cache cleanup (manual, only after the gates)

No local originals or shared caches are deleted by this migration. After uploads and
pinned download checks succeed and an independent backup is verified, inspect only a
project-specific cache. In an explicitly authorized cleanup session:

```bash
"$MACROHFT_WORK/asset-env/bin/hf" cache ls --revisions --cache-dir "$MACROHFT_HF_CACHE"
"$MACROHFT_WORK/asset-env/bin/hf" cache rm --help
# Copy an exact revision ID from cache ls; keep the interactive confirmation.
"$MACROHFT_WORK/asset-env/bin/hf" cache rm EXACT_REVISION_ID --cache-dir "$MACROHFT_HF_CACHE"
```

Do not run `cache rm` on a shared/global cache. Do not use recursive deletion of the
original iCloud tree. Deleting current Git files does not remove historical objects;
any history rewrite needs separate explicit approval and a verified backup.
