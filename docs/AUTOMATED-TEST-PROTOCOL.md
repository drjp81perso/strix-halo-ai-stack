# Automated acceptance protocol

The protocol exists because transport success is not semantic success. Observed examples include:

- a removed CLI option caused a 500 before model load;
- a 200 response exhausted its token budget in hidden reasoning and had empty final content;
- mathematically correct LaTeX was rejected by a plain-text validator;
- Open WebUI issued a second request during cold load and received 429 while the main request succeeded.

## Commands

```bash
./scripts/ai-stack protocol static
./scripts/ai-stack protocol smoke
./scripts/ai-stack protocol active
./scripts/ai-stack protocol exposed
./scripts/ai-stack protocol openwebui
./scripts/ai-stack protocol full
./scripts/ai-stack protocol soak
```

Every run creates:

```text
benchmark-results/protocol-YYYYMMDD-HHMMSS/
├── summary.json
├── TEST.log
└── optional raw JSON
```

## Suites

### Static

No running API required:

- YAML/JSON/shell syntax;
- template/render synchronization;
- forbidden runtime options;
- canonical roster uniqueness;
- active test and candidate promotion-test coverage;
- runtime flag check when Docker is available.

Use it in CI for every commit.

### Smoke

- health is 200;
- unauthenticated `/v1/models` is 401;
- authenticated model discovery works;
- cold `llm/fast` returns the exact expected final content;
- model unloads and `/running` is empty.

Run after deployment or restart.

### Active

Runs all eight active models sequentially. Each role has semantic assertions, not only HTTP checks. It starts unloaded, captures metrics, validates output, unloads, and verifies no process remains.

This suite can take several minutes because coder/reasoner cold loads are intentional.

### Exposed

Dynamically queries live `/v1/models`, runs a capability-appropriate functional test for every canonical advertised model, validates alias targets, and fails if any advertised model lacks a test. This is the primary answer to “does everything shown as available actually work?” See `docs/EXPOSED-MODEL-TEST.md`.

### Open WebUI

Emulates the incident seen in the UI:

1. unload coder;
2. submit foreground coder chat;
3. 150 ms later submit a background title request;
4. require both requests to return 200;
5. count any HTTP 429 as failure;
6. unload and verify empty `/running`.

This protects `GLOBAL_CONCURRENCY_LIMIT` and cold-load queue behavior from regression.

### Full

Runs static, smoke, live exposed-model, and Open WebUI suites.

### Soak

Runs the active suite three times. Use it after engine/model upgrades to detect allocation leaks, lifecycle races, or unload degradation.

## Environment inputs and precedence

The runner sources `.env` before every suite. It uses:

```text
AI_BIND, AI_PORT, AI_API_KEY
HEAVY_HOST_RESERVE_GB, LIGHT_HOST_RESERVE_GB
HEAVY_MAX_CURRENT_GTT_GB, LIGHT_MAX_CURRENT_GTT_GB
TTS_MAX_CURRENT_GTT_GB
GPU_FIT_TARGET_MIB, MIN_FIT_CONTEXT
GLOBAL_CONCURRENCY_LIMIT
PROTOCOL_UNLOAD_WAIT_SECONDS
PROTOCOL_MEMORY_RETURN_TOLERANCE_GIB
PROTOCOL_MAX_HTTP_429
```

Model memory variables feed llama-swap through Compose and `${env.*}` in the generated configuration. Protocol variables control the harness. Each `summary.json` and model result records the effective non-secret values.

Important: after changing `.env`, recreate the gateway:

```bash
docker compose up -d --force-recreate gateway
```

A plain restart retains the old container environment. The protocol's environment preflight fails if `GLOBAL_CONCURRENCY_LIMIT < 2` for Open WebUI testing.

## Pass/fail rules

A test fails on any of:

- unexpected status (including 429);
- empty or truncated required final content;
- wrong semantic result;
- invalid media output;
- model left running after unload;
- missing canonical roster coverage;
- stale generated configuration.

A safe admission rejection is reported distinctly during model qualification, but an active model suite treats it as failure because active models are expected to run on the declared reference profile.

## Candidate protocol

Disabled models are not executed by `active`. They must have a planned contract in `tests/planned-models.yaml`. Promotion requires implementing that test kind, exact fixtures/artifacts, and moving it into `tests/models.yaml` before `enabled: true`.

## CI recommendation

CI without GPU:

```bash
./scripts/ai-stack protocol static
```

Reference hardware after deployment:

```bash
./scripts/ai-stack protocol smoke
./scripts/ai-stack protocol openwebui
```

Nightly or before release:

```bash
./scripts/ai-stack protocol full
```

After llama.cpp, model, driver, or kernel upgrade:

```bash
./scripts/ai-stack protocol soak
```

## Interpreting results

Keep raw reports with hardware/backend metadata. Compare:

- cold-load wall time;
- prompt and decode tok/s;
- peak host and device memory;
- completion tokens and finish reason;
- unload latency and post-unload state;
- background-request statuses.

Do not compare warm and cold runs as if equivalent.
