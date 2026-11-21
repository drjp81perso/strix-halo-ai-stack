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

## Live terminal progress

Every suite prints timestamped progress immediately (UTC), even though detailed command output is written to log files:

```text
[2026-11-20T00:20:00Z] SUITE START name=exposed run_id=...
[2026-11-20T00:20:00Z] START environment                      suite=exposed test=1
[2026-11-20T00:20:00Z] PASS  environment                      elapsed=0m00s log=...
[2026-11-20T00:20:01Z] START exposed                          suite=exposed test=3
...
[2026-11-20T00:34:12Z] PASS  exposed                          elapsed=14m11s log=...
[2026-11-20T00:34:12Z] SUITE PASS name=exposed elapsed=14m12s passed=3 failed=0 report=...
```

The exposed runner also emits one start/finish pair for every live model or alias ID:

```text
[...Z] START 01/16 id=agent-fast type=alias target=llm/fast test=exact-chat
[...Z] PASS  01/16 id=agent-fast elapsed=0m06s log=...
```

On failure, the terminal shows the timestamp, elapsed time, exit code, log path, and the last 60 log lines. Long-running cold loads therefore no longer look like a hung test.

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

The suite queries live `/v1/models`.

It sends a real, capability-specific request for every returned ID. This includes canonical models and aliases.

Aliases use the canonical test assertions. The request still uses the alias ID.

The suite fails if it skips an ID or if an ID does not work. See `docs/EXPOSED-MODEL-TEST.md`.

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

The `active` suite does not run disabled models.

Each disabled model must have a planned contract in `tests/planned-models.yaml`.

Before promotion, implement the test and add the exact fixtures and artifacts. Then, move the test to `tests/models.yaml` and set `enabled: true`.

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
