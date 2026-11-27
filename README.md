# MacroHFT reproduction and research extension

This repository preserves code, configuration and lightweight evidence for reproducing
[MacroHFT (KDD 2024)](https://arxiv.org/abs/2406.14537) and testing extensions.

**2026-11-27: ETH final artifacts recovered and reconciled.** Reference seed
12345 returns 39.280827%; three-seed reference mean is 37.685867%. The combined
modification fails, averaging -0.491520%. All six metrics/checkpoints and seven
source files are archived; no test was rerun. Full reproduction, a successful
new method and CCF A readiness remain incomplete.

- [Recovered evidence and limitations](docs/EVIDENCE-RECONCILIATION-20261127.md)
- [New causal diagnostic: mixed synthetic outcomes](research/delayed-memory-validity-v2/docs/report.md)

- [Recovery and provenance](RECOVERY.md)
- [CQ compute fork and archive synchronization](docs/COMPUTE-MIRROR.md)
- [CQ recovery runbook](docs/RECOVERY-RUNBOOK.md)
- [Reproduce the archived setup](docs/REPRODUCE-FROM-ARCHIVE.md)
- [Archive verification](docs/ARCHIVE.md)
- [Research completion gates](docs/RESEARCH-GATES.md)
- [Current recovery status](docs/STATUS.md)
- [Workflow status](paper/workflow/current.md) and [latest novelty review](docs/NOVELTY-UPDATE-20261127.md)

The upstream source revision is `31e5ef41f93b2aea6e63e6ae2267675c997a8e54`.
New recovery and modified training code have their own commits here. Four
unavailable source files were reconstructed from the pinned upstream plus the
recorded patch; that provenance is explicit. The upstream SHA must not identify
modified code. `code-provenance.json` binds the runtime files to this project.

The initial reproduction retrains the hyper-agent with six released ETH
experts. It does not reproduce all four markets or expert training from
scratch. A separate three-market cost-memory diagnostic is a validation
prototype; it is not the paper's test protocol or a complete new RL method.
Its mixed and negative evidence is retained.

中文：本仓库保存真实代码、实验数据、结果和步骤。ETH 六组最终指标与模型已核对，
原方法 seed 12345 与论文收益四舍五入后一致，combined 改进失败；新方法尚未达到投稿目标。数据归档以实际文件上传和校验成功为准；清单中的
pending 项表示文件仍未完整归档，不能当成已备份。


## Storage and remote execution

GitHub now tracks code, configuration, dependency recipes, documentation, lightweight
summaries and asset manifests. Datasets and model weights are being migrated to private
Hugging Face repositories; **HF access is pending, so no project HF revision is available
yet**. Historical GitHub assets remain at commit
`23a4d58191b223227c142fa715bec104bb9e97c0`; shared history and originals are preserved.

- [Migration status, inventory, rights and cleanup gates](docs/storage/MIGRATION.md)
- [Asset manifest](assets/manifest.json) and [split definitions](assets/splits.json)
- [Exact remote workflow commands](docs/storage/WORKFLOW.md)

**Verified on c225, 2026-11-28:** clean code checkout, 51 source hashes, 25 transfer-tool
checks, nine synthetic execution checks, and a pinned 548-byte public HF config download
plus independent streaming SHA-256 verification. See the
[remote receipt](docs/storage/verification/j-1128-452f42/receipt.json).
This is transport qualification; actual private MacroHFT asset restoration remains blocked
by HF access. No project dataset/model has been uploaded to HF or assigned a fabricated revision.

Do not run the old archive-building scripts for new results. They are retained only for
historical recovery. Do not use an unrestricted full clone on a personal computer.
The Mac keeps a sparse code checkout. A fresh audit recovered 64 of the 66 previously
unavailable iCloud items; two legacy-tooling copies remain missing. Local originals are preserved.

## Exact commands (inside an authorized CQ remote job)

Use a clean, shallow code checkout and the job's local output directory. Run interactive
`hf auth login` only in your own terminal with `HF_HOME` pointing to an approved private
credential directory **outside collected outputs**. Never put a token in a job spec.

```bash
python3 scripts/create_asset_env.py --root "$CQ_OUTPUT_DIR/asset-env"
export PYTHON="$CQ_OUTPUT_DIR/asset-env/bin/python"
# Interactive owner terminal only, if not using an approved secret manager:
"$CQ_OUTPUT_DIR/asset-env/bin/hf" auth login
"$PYTHON" scripts/assets.py audit --namespace YOUR_CONFIRMED_NAMESPACE
export MACROHFT_ASSET_ROOT="$CQ_OUTPUT_DIR/assets"
export MACROHFT_HF_CACHE="$CQ_OUTPUT_DIR/cache/hub"
export HF_HUB_CACHE="$MACROHFT_HF_CACHE"
export HF_XET_CACHE="$CQ_OUTPUT_DIR/cache/xet"
"$PYTHON" scripts/assets.py validate
# These project-asset commands block until actual HF pins are in the manifest:
"$PYTHON" scripts/assets.py fetch --asset feature-definitions --asset released-experts
"$PYTHON" scripts/assets.py fetch --asset eth-prepared \
  --file prepared/ETHUSDT/train/data.feather --file prepared/ETHUSDT/val/data.feather
"$PYTHON" scripts/assets.py fetch --asset eth-prepared --file prepared/ETHUSDT/train/data.feather
"$PYTHON" scripts/assets.py verify --asset eth-prepared \
  --file prepared/ETHUSDT/train/data.feather --file prepared/ETHUSDT/val/data.feather
"$PYTHON" scripts/assets.py stream-verify --asset eth-prepared --file prepared/ETHUSDT/train/data.feather
```

For an isolated minimal runtime check and a validation-only experiment:

```bash
python3.11 scripts/create_asset_env.py --root "$CQ_OUTPUT_DIR/research-env" --python python3.11
"$CQ_OUTPUT_DIR/research-env/bin/python" -m pip install --no-cache-dir -r requirements/research-cpu.txt
"$CQ_OUTPUT_DIR/research-env/bin/python" scripts/remote_run.py \
  --work-dir "$CQ_OUTPUT_DIR/check" --check-only
"$CQ_OUTPUT_DIR/research-env/bin/python" scripts/remote_run.py \
  --work-dir "$CQ_OUTPUT_DIR/run-12345" --variant reference --seed 12345 --epochs 1 --device cpu
```

For an authorized new dataset, use explicit source files and a current quota observation:

```bash
"$PYTHON" scripts/stage_assets.py --asset eth-prepared \
  --legacy-root /date/zyy/macrohft-reproduction --root "$CQ_OUTPUT_DIR/stage" \
  --output-manifest "$CQ_OUTPUT_DIR/upload-plan.json"
"$PYTHON" scripts/assets.py --manifest "$CQ_OUTPUT_DIR/upload-plan.json" upload \
  --asset eth-prepared --source "$CQ_OUTPUT_DIR/stage" \
  --repo-id YOUR_NAMESPACE/YOUR_PRIVATE_DATASET_REPO \
  --quota-record "$CQ_OUTPUT_DIR/quota.json" \
  --output-manifest "$CQ_OUTPUT_DIR/verified-manifest.json"
# For selected models: use --asset eth-reference-12345 and your private model repo,
# after the required dataset/expert revisions have been verified and merged.
```

Once that CQ upload job finishes, retrieve **only** its small verified manifest into the
existing write-authorized code checkout (for example, this Mac's sparse checkout):

```bash
cq fetch UPLOAD_JOB_ID --path verified-manifest.json
cp UPLOAD_JOB_ID/verified-manifest.json assets/manifest.json
python3 scripts/assets.py validate
git add assets/manifest.json
git commit -m 'Pin verified HF assets'
git push origin main
```

Add `--create-repo` only after checking that no suitable repo exists. Every newly created
repo is private. Keep cards, provenance, splits and original bytes; do not upload all epochs.
The [full runbook](docs/storage/WORKFLOW.md) specifies quota fields, interrupted-upload
recovery, the clean-checkout commands and model retention.

Only after verified uploads, pinned recovery and an independent backup, and with cleanup
authorized, inspect and remove an exact revision in the **project-specific** cache:

```bash
"$CQ_OUTPUT_DIR/asset-env/bin/hf" cache ls --revisions --cache-dir "$MACROHFT_HF_CACHE"
"$CQ_OUTPUT_DIR/asset-env/bin/hf" cache rm EXACT_REVISION_ID --cache-dir "$MACROHFT_HF_CACHE" --dry-run
# Review the dry run, then rerun without --dry-run; retain interactive confirmation.
```

No originals, shared caches or Git history are deleted by these setup commands.
