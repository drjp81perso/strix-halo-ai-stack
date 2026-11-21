# Exposed-model functional test

This suite answers one operational question:

> Does every ID returned by live `/v1/models` actually route, respond through the correct API, pass a minimal semantic check, and unload?

Run everything:

```bash
./scripts/ai-stack protocol exposed
```

Filter while diagnosing:

```bash
./scripts/ai-stack protocol exposed --type alias
./scripts/ai-stack protocol exposed --id tts --id whisper
./scripts/ai-stack protocol exposed --match '^(tts|whisper)$'
./scripts/ai-stack protocol exposed --kind tts
./scripts/ai-stack protocol exposed --fail-fast
```

## Dynamic discovery

The suite queries authenticated `GET /v1/models`; it does not trust a hard-coded enabled list.

Canonical records have:

```yaml
meta.llamaswap.type: model
```

Aliases have:

```yaml
meta.llamaswap.type: alias
meta.llamaswap.modelID: CANONICAL_ID
```

The suite sends a request for every returned ID. This includes each canonical ID and each alias ID.

An alias uses the semantic test for its canonical target. The request still puts the alias in the `model` field.

The suite waits for the cold load, validates the output, and unloads the model. This proves each ID that Open WebUI can see.

This intentionally loads a target again for each alias. Completeness is favored over speed.

## Capability-appropriate routes

| Capability | Route | Functional assertion |
|---|---|---|
| Chat/agent | `/v1/chat/completions` | Normal stop and expected final text |
| Coder | `/v1/chat/completions` | Generated Python executes and satisfies invariants |
| Reasoner | `/v1/chat/completions` | Correct bounded final answer, including LaTeX normalization |
| Vision | `/v1/chat/completions` with image | Correct color/shape identification |
| Embedding | `/v1/embeddings` | Finite vectors and semantic cosine ordering |
| Reranker | `/v1/rerank` | Relevant document scores higher |
| TTS | `/v1/audio/speech` | Decodable, non-silent WAV |
| STT | `/v1/audio/transcriptions` | Required spoken keywords transcribed |

All IDs run sequentially from an unloaded state. The canonical semantic spec comes from `tests/models.yaml`; `tests/run.py --spec-id CANONICAL_ID ALIAS_ID` sends the alias while applying the canonical assertions.

## Results

```text
benchmark-results/protocol-*/exposed.json
benchmark-results/exposed__MODEL-ID-*.log
```

As each ID starts and finishes, the terminal prints UTC timestamp, ordinal progress, ID/type/target/test, elapsed duration, status, and log path. The console and JSON report pass/fail per returned ID, including:

- catalog type (`model` or `alias`);
- requested ID;
- canonical target;
- test kind;
- wall time;
- concise failure reason, exit code, error excerpt, and log path;
- total catalog/canonical/alias counts;
- returned IDs that were not tested.

Example shape:

```text
PASS model   llm/coder  llm/coder  41.2 python-code
PASS alias   coder      llm/coder  40.8 python-code
```

## Difference from other suites

- `active` runs the checked-in canonical active list once each.
- `exposed` runs **every live returned ID**, including aliases.
- `openwebui` tests concurrent foreground/background cold-load behavior and rejects 429.

`full` uses `exposed`, so release testing follows the actual live catalog.

## Pass criteria

1. `/v1/models` is authenticated and readable.
2. Every returned record is a supported canonical or alias type.
3. Every alias target is also advertised canonically.
4. Every canonical target has an executable semantic test.
5. Every returned ID performs a real successful request.
6. Every semantic assertion passes.
7. Every invocation unloads and leaves `/running` empty.
8. No returned ID is skipped.

Disabled registry candidates are not advertised and therefore are not run. Their promotion contracts remain in `tests/planned-models.yaml`.

## Audio alias caveat

JSON chat routes tolerate aliases because most llama-server backends ignore or accept arbitrary model labels. Audio backends can validate the body/form `model` strictly. The observed failures were:

```text
tts: unknown model id: tts
whisper: multipart request required canonical model rewrite
```

The corresponding model entries now set `useModelName` to their canonical IDs so llama-swap rewrites JSON TTS and multipart STT requests before proxying. This is why testing aliases by real inference is valuable.

After syncing this change to the server, ensure the live gateway actually reloaded/recreated before rerunning:

```bash
./scripts/generate-config
./scripts/validate
docker compose up -d --force-recreate gateway
./scripts/ai-stack protocol exposed --id tts --id whisper
```

An alias record in `/v1/models` does not prove that `useModelName` is active. The public model metadata does not contain that field.

If the test reports `unknown model id: tts`, check the effective gateway configuration. The gateway can still use an old configuration.

The error can also mean that the installed llama-swap build does not rewrite the JSON model field.
