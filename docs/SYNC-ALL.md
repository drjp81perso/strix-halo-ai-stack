# Sync-All: Unified Configuration Reconciliation

## Overview

The `sync-all` command provides a single, atomic operation to reconcile all four configuration paths in the Strix-Halo AI Stack:

1. **Registry** (`registry/models.yaml`) - Canonical source of truth for model definitions
2. **Template** (`templates/llama-swap.yaml`) - Runtime configuration template
3. **Environment** (`.env`) - Runtime parameters and memory settings
4. **Physical Files** (`MODEL_DIR/`) - Actual model weights on disk

Previously, these paths could drift apart, requiring manual reconciliation. The `sync-all` command identifies conflicts, reports them, and optionally applies fixes.

## The Four Paths Problem

| Path | Purpose | Can Drift When |
|------|---------|----------------|
| Registry | Model metadata, lifecycle, test coverage | Adding/removing models, changing test status |
| Template | Runtime command lines, paths, TTL | Enabling/disabling models, changing model paths |
| Environment | Context sizes, memory reserves, GPU targets | Changing hardware, adding new model types |
| Physical Files | Model weights on disk | Downloading candidates, manual file operations |

**Conflict Example**: You add a model to the registry and download its files, but forget to add it to the template. The model is "enabled" but will not start because the template does not know about it.

## Usage

### Dry-Run (Default)

```bash
./scripts/ai-stack sync-all
```

This performs all validation checks but **does not make changes**. It reports:
- Registry validation status
- Template-registry alignment
- Environment variable coverage
- Missing or orphan files
- Config generation readiness

### Apply Changes

```bash
./scripts/ai-stack sync-all --apply
```

Applies fixes for:
- Regenerates `config/llama-swap.yaml` from template
- Validates generated config

**Note**: `--apply` does not automatically:
- Download missing models (use `--sync-models`)
- Quarantine orphan files (use `--quarantine`)
- Restart the gateway (use `--recreate`)

### Full Sync with Model Downloads

```bash
./scripts/ai-stack sync-all --apply --sync-models --track all
```

Downloads any missing model artifacts for all tracks (active + candidates).

### Full Sync with Orphan Cleanup

```bash
./scripts/ai-stack sync-all --apply --quarantine
```

Quarantines unreferenced files after reconciliation.

### Full Sync with Gateway Restart

```bash
./scripts/ai-stack sync-all --apply --recreate
```

Recreates the gateway container to apply new configuration.

### Complete Full Sync

```bash
./scripts/ai-stack sync-all --apply --sync-models --quarantine --recreate --track all
```

Performs a complete reconciliation:
1. Validates all paths
2. Downloads missing models
3. Quarantines orphans
4. Regenerates config
5. Restarts gateway

## Command Options

| Option | Description |
|--------|-------------|
| `--apply` | Apply changes instead of dry-run |
| `--sync-models` | Download missing model artifacts |
| `--quarantine` | Move orphan files to `.trash/` |
| `--recreate` | Restart gateway container |
| `--track` | Track to sync (`active`, `balanced`, `experimental`, `staged`, `all`) |
| `--output` | Custom output directory for results log |

## Workflow

### Normal Daily Operation

```bash
# Check status before making changes
./scripts/ai-stack sync-all

# If everything looks good, no action needed
# If changes are needed:
./scripts/ai-stack sync-all --apply --recreate
```

### Adding a New Model

1. Add model to `registry/models.yaml` with `enabled: false`
2. Run `./scripts/ai-stack sync-all` (dry-run to check registry)
3. Download model: `./scripts/ai-stack model-sync all`
4. Test the model manually
5. When ready to promote:
   - Set `enabled: true` in registry
   - Add entry to `templates/llama-swap.yaml`
   - Run `./scripts/ai-stack sync-all --apply --recreate`

### Upgrading an Existing Model

1. Add candidate to registry with new artifact
2. Download candidate: `./scripts/ai-stack model-sync all`
3. Test candidate manually
4. When ready:
   - Swap artifact paths in `templates/llama-swap.yaml`
   - Run `./scripts/ai-stack sync-all --apply --recreate`
   - Run `./scripts/ai-stack protocol exposed`
   - Quarantine old files: `./scripts/ai-stack sync-all --quarantine`

### Recovering from Drift

If you suspect configuration drift:

```bash
# Full diagnostic
./scripts/ai-stack sync-all

# If errors are reported, fix them manually first
# Then apply fixes
./scripts/ai-stack sync-all --apply

# Restart to apply
./scripts/ai-stack sync-all --recreate
```

## Output Format

### Dry-Run Output

```text
SYNC-ALL DRY-RUN
Timestamp: 2026-11-27 21:52:53
Output: /aiwork/strix-halo-ai-stack/benchmark-results/sync-all-20261127-215253
============================================================

✓ REGISTRY: Loading registry...
✓ REGISTRY: Found 24 models
✓ REGISTRY: ✓ All active models have executable tests (8)
✓ REGISTRY: ✓ All candidates have planned tests (16)

✓ TEMPLATE: Comparing registry with template...
✓ TEMPLATE: ✓ Template matches registry (8 enabled models)

✓ ENVIRONMENT: Validating environment variables...
✓ ENVIRONMENT: ✓ All 12 profile and 8 env variables resolved

✓ FILES: Checking physical files...
⚠ FILES: Found 3 orphan files (2.1 GiB)
  ORPHAN: experiments/old-model/model.gguf
  ORPHAN: tests/cache/temp.bin
  ORPHAN: .trash/20261120-140000/manifest.json
✓ FILES: ✓ All enabled model artifacts present

✓ CONFIG: Generating config...
✓ CONFIG: Config generated successfully

✓ VALIDATION: Running validation...
✓ VALIDATION: Validation passed

============================================================
SYNC-ALL SUMMARY
============================================================

Status: DRY-RUN (WARNINGS)

REGISTRY:
  ✓ Loading registry...
  ✓ Found 24 models
  ✓ ✓ All active models have executable tests (8)
  ✓ ✓ All candidates have planned tests (16)

TEMPLATE:
  ✓ Comparing registry with template...
  ✓ ✓ Template matches registry (8 enabled models)

ENVIRONMENT:
  ✓ Validating environment variables...
  ✓ ✓ All 12 profile and 8 env variables resolved

FILES:
  ✓ Checking physical files...
  ⚠ Found 3 orphan files (2.1 GiB)
    ORPHAN: experiments/old-model/model.gguf
    ORPHAN: tests/cache/temp.bin
    ORPHAN: .trash/20261120-140000/manifest.json
  ✓ ✓ All enabled model artifacts present

CONFIG:
  ✓ Generating config...
  ✓ Config generated successfully

VALIDATION:
  ✓ Running validation...
  ✓ Validation passed

------------------------------------------------------------
RECOMMENDED ACTIONS:
  --apply           Apply changes
  --sync-models     Also download missing candidate artifacts
  --quarantine      Also quarantine orphan files
  --recreate        Also restart the gateway container
============================================================
```

### Apply Output

```text
SYNC-ALL APPLY
Timestamp: 2026-11-27 21:53:15
Output: /aiwork/strix-halo-ai-stack/benchmark-results/sync-all-20261127-215315
============================================================

... (same validation steps) ...

✓ FILES: Quarantining orphan files...
✓ FILES: Orphans quarantined successfully

✓ CONFIG: Recreating gateway container...
✓ CONFIG: Gateway recreated successfully

Results saved to: /aiwork/strix-halo-ai-stack/benchmark-results/sync-all-20261127-215315/results.json

============================================================
SYNC-ALL SUMMARY
============================================================

Status: APPLIED (SUCCESS)
...
```

## Results Logging

Each run creates a timestamped directory in `benchmark-results/`:

```
benchmark-results/
└── sync-all-20261127-215253/
    └── results.json
```

The `results.json` file contains structured output for programmatic analysis:

```json
{
  "registry": {
    "status": "success",
    "errors": [],
    "warnings": [],
    "info": ["Found 24 models", "✓ All active models have executable tests"]
  },
  "template": {
    "status": "success",
    ...
  },
  ...
}
```

## Error Handling

### Registry Validation Fails

**Symptoms**: Duplicate IDs, missing tests, incorrect `test_status`

**Fix**: Edit `registry/models.yaml` and re-run:
```bash
./scripts/ai-stack sync-all
```

### Template Mismatch

**Symptoms**: Enabled model not in template, or template has disabled model

**Fix**: 
- Add missing model to `templates/llama-swap.yaml`
- Or set `enabled: false` in registry
- Re-run: `./scripts/ai-stack sync-all --apply`

### Environment Variable Missing

**Symptoms**: Template references `${profile.X}` or `${env.Y}` not in `.env`

**Fix**:
- Add variable to `.env` (copy from `.env.example` if needed)
- Or remove reference from template
- Re-run: `./scripts/ai-stack sync-all --apply`

### Missing Model Files

**Symptoms**: Enabled model has no artifacts in `MODEL_DIR/`

**Fix**:
```bash
./scripts/ai-stack sync-all --apply --sync-models --track active
```

### Orphan Files

**Symptoms**: Files in `MODEL_DIR/` not referenced by any registry entry

**Fix**:
```bash
# Review orphans first (dry-run)
./scripts/ai-stack sync-all

# Quarantine if safe
./scripts/ai-stack sync-all --apply --quarantine
```

## Integration with Other Commands

| Command | When to Use After sync-all |
|---------|---------------------------|
| `./scripts/ai-stack protocol exposed` | After promoting a new model |
| `./scripts/ai-stack model-status all` | To verify file status after sync |
| `./scripts/ai-stack roster` | To check test coverage after changes |
| `./scripts/ai-stack logs` | To debug gateway issues after recreate |

## Best Practices

1. **Always run dry-run first**: Never use `--apply` without reviewing the dry-run output.

2. **Sync before deployment**: Run `sync-all` before any deployment to catch drift early.

3. **Use `--track all` for candidates**: When testing new models, sync all tracks to ensure candidates are available.

4. **Quarantine before purge**: Orphan files go to `.trash/` first. Review before permanent deletion.

5. **Recreate gateway after config changes**: Environment variable changes require container recreation.

6. **Keep results**: The `benchmark-results/sync-all-*` directories provide audit trails for troubleshooting.

## Troubleshooting

### "Config generation failed"

Check `templates/llama-swap.yaml` for syntax errors or missing variable references.

```bash
./scripts/generate-config
```

### "Gateway recreation failed"

Check Docker logs:

```bash
docker compose logs gateway
```

### "Model sync failed"

Check Hugging Face CLI installation:

```bash
python3 -m pip install --user -U huggingface_hub
export PATH="$HOME/.local/bin:$PATH"
```

### "Validation failed"

Run validation manually for detailed output:

```bash
./scripts/validate
```

## See Also

- [Model Lifecycle](MODEL-LIFECYCLE.md) - Model download, quarantine, and purge workflow
- [Customizing](CUSTOMIZING.md) - Hardware profiles and memory settings
- [Testing](TESTING.md) - Model test coverage and promotion
- [Model Roster](MODEL-ROSTER.md) - Current model status and lifecycle stages
