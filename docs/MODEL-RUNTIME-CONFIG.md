# Model runtime configuration

Use `.env` to set the runtime context policy for each local language model.

Do not edit the generated `config/llama-swap.yaml` file. The generator replaces its content.

## Configuration variables

| Model | Preferred context | Minimum fitted context | Other setting |
|---|---|---|---|
| `llm/fast` | `LLM_FAST_CONTEXT_SIZE` | Not applicable | None |
| `llm/reasoning` | `LLM_REASONING_CONTEXT_SIZE` | `LLM_REASONING_FIT_CONTEXT` | `LLM_REASONING_BUDGET` |
| `llm/coder` | `LLM_CODER_CONTEXT_SIZE` | `LLM_CODER_FIT_CONTEXT` | None |
| `llm/vision` | `LLM_VISION_CONTEXT_SIZE` | `LLM_VISION_FIT_CONTEXT` | None |

The preferred context sets `--ctx-size`. The minimum fitted context sets `--fit-ctx`.

The output-token limit is not a server profile setting. Set `max_tokens` in the client request or in the Open WebUI model preset.

## Show a model policy

```bash
./scripts/ai-stack model-config show llm/coder
```

Use JSON output for automation:

```bash
./scripts/ai-stack model-config show llm/reasoning --json
```

## Change a model policy

Set a 64K preferred context and a 32K fitting floor:

```bash
./scripts/ai-stack model-config set \
  llm/coder \
  --context 65536 \
  --fit-context 32768
```

Change the reasoning budget:

```bash
./scripts/ai-stack model-config set \
  llm/reasoning \
  --reasoning-budget 1536
```

The command edits `.env`. It rejects a fitting floor that is larger than the preferred context.

## Apply a model policy

```bash
./scripts/ai-stack model-config apply llm/coder
```

The command does these actions:

1. Generates `config/llama-swap.yaml` from the template and `.env`.
2. Validates the complete deployment configuration.
3. Waits for the configuration watcher.
4. Unloads only the selected model.
5. Leaves the gateway and other services running.

The next request loads the selected model with the new context policy.

A full container recreation is not required.

Recreate the gateway only when you change its image, Compose service, or container environment.

## Capacity warning

A larger context increases KV-cache memory use. Increase one model at a time. Test the model after each change.

```bash
./scripts/ai-stack test llm/coder
./scripts/ai-stack protocol openwebui
```

Automatic fitting can reduce the preferred context to the configured fitting floor.

To guarantee the preferred context, set both values to the same number. The model can fail to load when that fixed allocation does not fit.
