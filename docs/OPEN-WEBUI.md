# Open WebUI integration

## Connection

Add an OpenAI-compatible connection:

```text
URL: http://AI_HOST:9292/v1
API key: AI_API_KEY from .env
Provider: Default
Forward cookies: Off
```

Use an address reachable from the Open WebUI backend/container. `localhost` inside that container is not the AI host unless both services share a network namespace.

The gateway hides aliases from `/v1/models` with `includeAliasesInList: false`. Thus, Open WebUI does not show each backend two times.

A client can still use a known alias. Use Workspace model presets for clear role names. See `docs/OPEN-WEBUI-PRESETS.md`.

Allowlist chat models only:

```text
llm/fast
llm/reasoning
llm/coder
llm/vision
```

Configure STT, TTS, and RAG separately:

```text
STT model: speech/whisper-large-v3-turbo
TTS model: speech/kokoro; voice alloy
Embedding model: retrieval/embedding
```

Reranking through `/v1/rerank` depends on the installed Open WebUI version/provider support.

## Why a cold model may briefly show “Too many requests”

Open WebUI can send more than one request for a user message.

It sends the main chat request. It can also send requests for a title, tags, or follow-up text.

The old setting `globalConcurrencyLimit: 1` rejected the second request with HTTP 429 during a cold load.

The server log signature is:

```text
POST /v1/chat/completions ... 429 ...
model loaded
POST /v1/chat/completions ... 200 ...
```

This means inference succeeded, but the UI displayed the rejected companion request.

The default is now:

```dotenv
GLOBAL_CONCURRENCY_LIMIT=4
```

and the template uses:

```yaml
globalConcurrencyLimit: ${env.GLOBAL_CONCURRENCY_LIMIT}
```

This does **not** load four heavyweight models or create four llama.cpp slots:

- routing still permits only one heavyweight model group at a time;
- each llama-server still uses `--parallel 1`;
- memory admission remains in force;
- extra gateway requests wait behind loading/routing rather than being rejected globally.

Do not increase this value without a test when many users share the service.

First, measure the queue behavior. Then, add model slots with an explicit memory budget, or keep a low limit and accept controlled HTTP 429 responses.

## Apply the fix

```bash
# Add or change in .env
GLOBAL_CONCURRENCY_LIMIT=4

./scripts/generate-config
./scripts/validate
# .env changes require recreation; restart alone reuses old environment.
docker compose up -d --force-recreate gateway
```

Verify the effective configuration:

```bash
grep '^globalConcurrencyLimit:' config/llama-swap.yaml
```

Expected:

```text
globalConcurrencyLimit: ${env.GLOBAL_CONCURRENCY_LIMIT}
```

The environment substitution happens in llama-swap, so the rendered YAML intentionally contains the macro. A plain `docker compose restart gateway` does not refresh container environment variables. Confirm the recreated container sees the value:

```bash
docker compose exec gateway sh -lc 'echo "$GLOBAL_CONCURRENCY_LIMIT"'
```

Then run the regression directly:

```bash
./scripts/ai-stack protocol openwebui
```

Check startup logs for configuration errors and then retry a fresh chat.

## Background-task model recommendation

If Open WebUI has a task-model setting, use `llm/fast` for titles, tags, and other background tasks.

Do not send background tasks to `llm/coder` or `llm/reasoning`. A background task can start a large model and occupy its only slot.

If the UI still shows 429:

1. Confirm the gateway was recreated and reports `GLOBAL_CONCURRENCY_LIMIT=4`.
2. Inspect logs to identify how many requests Open WebUI sends.
3. Disable nonessential background features temporarily or select `llm/fast` as the task model.
4. Do not increase model `--parallel` until peak KV-cache memory is measured.

## Other log messages

This warning is model metadata-related and was automatically overridden by llama.cpp:

```text
control-looking token ... was not control-type; its type will be overridden
```

It did not prevent loading or generation in the observed coder run. Track it across llama.cpp/model revisions, but it is not the cause of the 429.
