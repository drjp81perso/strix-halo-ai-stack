# Model lifecycle: inventory, update, replacement and pruning

## Current behavior versus old scripts

The original `download-models` and `check-models` scripts used eight fixed file names.

They downloaded missing artifacts. They did not read new registry candidates or remove old files.

Thus, a model or quantization change could leave a large quantity of unreferenced data.

The repository now uses `scripts/model-manager.py` and `registry/models.yaml` as the source of truth.

## Safety policy

Pruning is intentionally two-step:

1. **Quarantine** unreferenced files under `MODEL_DIR/.trash/TIMESTAMP/`.
2. **Purge** quarantine only after a retention period.

No normal command permanently deletes model weights immediately. This protects against a mistaken registry edit and allows rollback without re-downloading.

Hidden Hugging Face cache/lock directories are ignored by model pruning. Manage shared HF caches separately; the downloader uses `--local-dir`, so final artifacts are stored in `MODEL_DIR`.

## Inventory

Active models:

```bash
./scripts/ai-stack model-status
```

Another track:

```bash
./scripts/ai-stack model-status balanced
./scripts/ai-stack model-status experimental
./scripts/ai-stack model-status all
```

The report shows expected files, missing patterns, managed size, and unreferenced files.

Machine-readable:

```bash
python3 scripts/model-manager.py --track active status --json
```

## Download/update

Sync active artifacts:

```bash
./scripts/ai-stack model-sync active
```

Sync balanced candidates:

```bash
./scripts/ai-stack model-sync balanced
```

Or one exact registry ID:

```bash
python3 scripts/model-manager.py \
  --track all \
  --id llm/qwen38-27b-q5 \
  sync
```

Downloads first go to a staging directory. The manager moves a file to its final location only after the download is complete.

A download can replace an existing file with the same name. Pin the revision and checksum before promotion.

The manager does not guess a file name. It reports and skips a candidate that has no exact `files` or `include` value.

## Replacing a model

Recommended workflow:

1. Add candidate to `registry/models.yaml` with exact source, files/include, local directory, license and planned test.
2. Sync only that ID.
3. Add a temporary llama-swap candidate entry; do not replace the incumbent yet.
4. Run semantic, performance, memory and unload tests.
5. Promote candidate and disable/remove the old model from the canonical template/active registry.
6. Regenerate/recreate gateway and run exposed/full protocols.
7. Inventory unreferenced artifacts.
8. Quarantine; keep for rollback.
9. Purge after retention.

Do not overwrite a working incumbent before the challenger passes.

## Prune dry run

Active references only:

```bash
./scripts/ai-stack model-prune active
```

Everything not referenced by active models is shown as a candidate for quarantine. This includes downloaded but disabled candidate models, so **do not apply active pruning if you intend to retain candidates**.

Keep active + candidates by pruning against all canonical registry entries:

```bash
./scripts/ai-stack model-prune all
```

## Quarantine

After reviewing the dry run:

```bash
./scripts/ai-stack model-prune active --apply
```

Files move to:

```text
MODEL_DIR/.trash/YYYYMMDD-HHMMSS/
```

A `manifest.json` records original relative paths and total bytes.

To retain balanced candidates while pruning other experiments:

- Temporarily use `--track all` (keeps all registry-managed artifacts), or
- Quarantine with a curated registry/track after promoting the intended models.

Current implementation selects one track at a time; `all` is safest when uncertain.

## Rollback

Read the quarantine manifest and move the file back to its original path. Example:

```bash
TRASH="$MODEL_DIR/.trash/20261121-120000"
cat "$TRASH/manifest.json" | jq

# Restore one file preserving its relative path:
REL='llm/old-model/model.gguf'
mkdir -p "$MODEL_DIR/$(dirname "$REL")"
mv "$TRASH/$REL" "$MODEL_DIR/$REL"
```

Then restore the previous registry/template Git revision and regenerate.

## Permanent purge

Dry run quarantines older than 14 days:

```bash
python3 scripts/model-manager.py purge --older-than-days 14
```

Apply:

```bash
python3 scripts/model-manager.py purge \
  --older-than-days 14 \
  --apply
```

Purge is irreversible.

## Storage planning

Before downloading:

```bash
df -h "$MODEL_DIR"
./scripts/ai-stack model-status all
```

Keep enough free space for:

- download staging (up to one additional full model copy);
- active models;
- retained rollback quarantine;
- media outputs;
- filesystem headroom (prefer at least 10–15%).

The included 2 TB disk is adequate for a curated roster, but multiple large quantizations, image/video pipelines and quarantine can consume it quickly.

## Limitations

- Registry candidates that list upstream package/repository artifacts rather than exact downloadable files are not automatically synced.
- The manager does not yet pin Hugging Face revisions or verify SHA-256 unless those fields are added to the registry.
- It does not delete shared global Hugging Face caches.
- It does not infer references from arbitrary files outside `registry/models.yaml`.
- A dry run and review remain mandatory before `--apply`.
