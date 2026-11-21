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
5. Applies a role-specific runtime profile.
6. Runs independent upgrade contracts for coding, chat, and vision.
7. Requires at least 7.5 tok/s for each candidate.
8. Stops if a semantic, response-contract, or speed test fails.
9. Restores the previous configuration after a failure.
10. Replaces the stable coder and vision endpoints only after all tests pass.
11. Runs the exposed-model and Open WebUI protocols.
12. Moves only the old coder and vision model directories to quarantine.

The script does not permanently delete a model file.

## Deployment model

Run this procedure in the deployed runtime directory. The directory does not need a `.git` directory.

You can keep the source repository in a different location. Use `rsync` to update the deployment directory.

Exclude `.env`, models, outputs, state, benchmark results, and upgrade results.

The upgrade script creates its own file snapshot for rollback.

## Prerequisites

- Synchronize the tested source files to the deployment directory.
- Install the Hugging Face CLI.
- Start Docker.
- Confirm the current stack passes the exposed protocol.
- Keep at least 80 GiB free in `MODEL_DIR`.
- Review the model licenses.

Check that the required deployment files exist:

```bash
for file in \
  templates/llama-swap.yaml \
  config/llama-swap.yaml \
  tests/models.yaml \
  tests/planned-models.yaml \
  registry/models.yaml; do
  test -f "$file" || echo "Missing: $file"
done
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

The script checks the registered artifact paths before it downloads a model.

- It prints `reuse` when all registered files are present.
- It prints `download` when one or more registered files are missing.
- A failed qualification keeps the downloaded candidate files for the next run.
- A test retry does not download complete model files again.

Use a forced refresh only when the local artifacts are damaged or the registry points to a new revision:

```bash
python3 scripts/upgrade-target-llms.py \
  --apply \
  --refresh-models
```

> **Warning:** A forced refresh can transfer tens of gibibytes. Do not use it for a normal test retry.

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

> **Warning:** Do not edit the managed configuration files while the upgrade is running. The script uses a local transaction snapshot for rollback.

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

The upgrade tests do not copy the incumbent model tests. They use stable role contracts.

Qwen3.8 uses the `coder` runtime profile and runs:

- `upgrade/coder` with 1,536 output tokens
- `upgrade/chat` with 128 output tokens
- `upgrade/vision` with 256 output tokens

Gemma 4 uses the `vision` runtime profile and runs:

- `upgrade/vision` with 256 output tokens
- `upgrade/chat` with 128 output tokens

The `coder` and `vision` runtime profiles disable reasoning. These basic contracts require the final answer in `message.content`. They also require `finish_reason: stop`.

The test result separates these layers:

- Runtime start
- Role capability
- OpenAI response contract
- Performance
- Unload lifecycle

A correct answer in `reasoning_content` proves capability for diagnosis. It does not pass the response contract. Open WebUI requires usable final content.

The script records logs and results under:

```text
upgrade-results/YYYYMMDD-HHMMSS/
```

The qualification report is:

```text
upgrade-results/YYYYMMDD-HHMMSS/qualification.json
```

See `docs/UPGRADE-RESULTS.md` for commands that show performance, model output, and explicit failure reasons.

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

1. Select the applicable transaction directory.
2. Restore the configuration snapshot.
3. Restore the model directories from quarantine.
4. Regenerate the configuration.
5. Recreate the gateway.
6. Run the exposed protocol.

List transactions:

```bash
find upgrade-results \
  -mindepth 1 \
  -maxdepth 1 \
  -type d \
  -printf '%f\n' \
  | sort -r
```

Restore the saved files. Replace the timestamp:

```bash
TX="upgrade-results/YYYYMMDD-HHMMSS"

cp -a "$TX/backup/templates/llama-swap.yaml" \
  templates/llama-swap.yaml
cp -a "$TX/backup/config/llama-swap.yaml" \
  config/llama-swap.yaml
cp -a "$TX/backup/tests/models.yaml" \
  tests/models.yaml
cp -a "$TX/backup/tests/planned-models.yaml" \
  tests/planned-models.yaml
cp -a "$TX/backup/registry/models.yaml" \
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

## Qualification states

Each benchmark result has a `qualification_state` value:

- `pass`
- `runtime-fail`
- `semantic-fail`
- `capability-pass-contract-fail`
- `lifecycle-fail`

A vision model can identify the image in `reasoning_content` and still fail the response contract.

Correct the candidate runtime profile and run the test again. Do not classify this result as a vision-capability failure.
