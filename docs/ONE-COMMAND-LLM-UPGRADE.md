# One-command LLM upgrade

Use this procedure to qualify and promote these candidates:

- Qwen3.8-27B Q5 for `llm/coder`
- Gemma 4 31B Q5 for `llm/vision`

The script keeps `llm/fast` and `llm/reasoning` unchanged.

## Safety behavior

The script does these actions in order:

1. Checks the current exposed-model baseline.
2. Downloads both candidates through the registry manager.
3. Adds temporary `candidate/*` endpoints.
4. Recreates the gateway.
5. Runs role tests for coding, chat, and vision.
6. Requires at least 7.5 tok/s for each candidate.
7. Stops if a semantic or speed test fails.
8. Restores the previous configuration after a failure.
9. Replaces the stable coder and vision endpoints only after all tests pass.
10. Runs the exposed-model and Open WebUI protocols.
11. Moves only the old coder and vision model directories to quarantine.

The script does not permanently delete a model file.

## Prerequisites

- Commit or stash repository changes.
- Install the Hugging Face CLI.
- Start Docker.
- Confirm the current stack passes the exposed protocol.
- Keep at least 80 GiB free in `MODEL_DIR`.
- Review the model licenses.

Check the working tree:

```bash
git status --short
```

Install the Hugging Face CLI:

```bash
python3 -m pip install --user -U huggingface_hub
export PATH="$HOME/.local/bin:$PATH"
```

Check disk space:

```bash
set -a
source .env
set +a

df -h "$MODEL_DIR"
```

## Preview the plan

```bash
python3 scripts/upgrade-target-llms.py
```

This command does not change files or download models.

## Run the upgrade

```bash
python3 scripts/upgrade-target-llms.py --apply
```

Use this command to keep old files in place after promotion:

```bash
python3 scripts/upgrade-target-llms.py \
  --apply \
  --no-prune
```

Use a different free-space threshold only when you understand the staging requirement:

```bash
python3 scripts/upgrade-target-llms.py \
  --apply \
  --minimum-free-gib 120
```

> **Warning:** Do not use `--allow-dirty` for a normal upgrade. A clean Git working tree is part of the rollback method.

## Expected download locations

```text
MODEL_DIR/llm/qwen38-27b-q5/
  Qwen3.8-27B-UD-Q5_K_M.gguf
  mmproj-BF16.gguf

MODEL_DIR/llm/gemma4-31b-q5/
  gemma-4-31B-it-Q5_K_M.gguf
  mmproj-BF16.gguf
```

## Qualification tests

Qwen3.8 runs these test specifications:

- `llm/coder`
- `llm/fast`
- `llm/vision`

Gemma 4 runs these test specifications:

- `llm/vision`
- `llm/fast`

The script records logs and results under:

```text
upgrade-results/YYYYMMDD-HHMMSS/
```

The qualification report is:

```text
upgrade-results/YYYYMMDD-HHMMSS/qualification.json
```

## Promotion result

The public model IDs remain stable:

```text
llm/coder  -> Qwen3.8-27B Q5
llm/vision -> Gemma 4 31B Q5
```

Open WebUI does not need new model IDs after promotion.

The old `llm/fast`, `llm/reasoning`, retrieval, and speech models remain active.

## Quarantine result

After all promotion tests pass, the script moves these directories:

```text
MODEL_DIR/llm/coder
MODEL_DIR/vision/qwen3vl
```

The target location is:

```text
MODEL_DIR/.trash/YYYYMMDD-HHMMSS/
```

The script writes `upgrade-manifest.json` in that directory.

Keep the quarantine for at least 14 days.

## Rollback after a successful upgrade

1. Restore the prior Git revision.
2. Restore the model directories from quarantine.
3. Regenerate the configuration.
4. Recreate the gateway.
5. Run the exposed protocol.

Example:

```bash
git log --oneline -5
git checkout PREVIOUS_COMMIT -- \
  templates/llama-swap.yaml \
  config/llama-swap.yaml \
  tests/models.yaml \
  tests/planned-models.yaml \
  registry/models.yaml
```

Restore the directories. Replace the timestamp:

```bash
TRASH="$MODEL_DIR/.trash/YYYYMMDD-HHMMSS"

mv "$TRASH/llm/coder" "$MODEL_DIR/llm/coder"
mv "$TRASH/vision/qwen3vl" "$MODEL_DIR/vision/qwen3vl"
```

Then, apply the old configuration:

```bash
./scripts/generate-config
./scripts/validate
docker compose up -d --force-recreate gateway
./scripts/ai-stack protocol exposed
```

## Failure behavior

If a candidate fails before promotion, the script restores the configuration backup and recreates the gateway.

Downloaded candidate files remain in `MODEL_DIR`. This permits diagnosis and a later retest. Use the model manager to quarantine them after review.
