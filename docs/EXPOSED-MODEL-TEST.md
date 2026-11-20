# Exposed-model functional test

This suite answers one operational question:

> Does every canonical model currently advertised by `/v1/models` actually respond through its declared API and pass a minimal semantic check?

Run:

```bash
./scripts/ai-stack protocol exposed
```

## Dynamic discovery

The suite queries the live endpoint:

```text
GET /v1/models
```

It does not trust a hard-coded enabled list. Records with:

```yaml
meta.llamaswap.type: model
```

are canonical exposed models and must have an executable test in `tests/models.yaml`. If an advertised model has no test, the suite fails before promotion can be considered complete.

Records with:

```yaml
meta.llamaswap.type: alias
```

are validated to point to an existing canonical model. Aliases are not inferred a second time because that would duplicate expensive model loads; their target's functional test is the inference proof.

## Capability-appropriate routes

The test registry maps each exposed model to its actual endpoint and assertion:

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

Each canonical model is tested sequentially from an unloaded state and unloaded afterward.

## Results

The suite writes:

```text
benchmark-results/protocol-*/exposed.json
benchmark-results/exposed__MODEL-ID-*.log
```

The summary contains:

- live catalog/canonical/alias counts;
- pass/fail result and duration for every canonical model;
- alias target contracts;
- advertised models missing tests;
- tests that are no longer advertised;
- count of failures.

## Difference from other suites

- `active` uses the checked-in expected active list. It is useful for release regression.
- `exposed` uses the live `/v1/models` catalog. It catches accidental exposure, stale configuration, and models added without a functional test.
- `openwebui` tests a concurrent cold-load request pattern and rejects any 429.

The `full` suite now uses `exposed` so it always follows the live advertised catalog.

## Pass criteria

The suite passes only when:

1. `/v1/models` is authenticated and readable.
2. Every canonical advertised model has an executable test.
3. Every canonical model's endpoint responds successfully.
4. Every semantic assertion passes.
5. Every model unloads and leaves `/running` empty.
6. Every advertised alias points to a canonical model.

Candidate models that are present only in `registry/models.yaml` and have `enabled: false` are not advertised and are therefore not run. Their promotion contracts remain in `tests/planned-models.yaml`.
