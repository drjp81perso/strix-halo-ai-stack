# Contributing

Thank you for improving this project.

## Before you start

1. Read [Technical writing standard](docs/WRITING-STANDARD.md).
2. Read [Model roster](docs/MODEL-ROSTER.md).
3. Read [Automated test protocol](docs/AUTOMATED-TEST-PROTOCOL.md).
4. Do not commit model files, API keys, runtime databases, or generated media.

## Report a model candidate

Use the model-candidate issue template. Include:

- Official model repository
- Conversion repository, if applicable
- License
- Exact artifact names
- Expected disk and memory use
- Backend and device
- Context and quantization
- Source of the recommendation
- Estimated performance
- Planned local tests

If you used `whichllm` or FreeLLMArena, include the complete input settings and the result date.

## Add a candidate

1. Add the model to `registry/models.yaml` with `enabled: false`.
2. Select `balanced`, `experimental`, or `staged`.
3. Add exact artifacts when they are known.
4. Add a promotion gate.
5. Add a planned test to `tests/planned-models.yaml`.
6. Run validation.

```bash
./scripts/validate
./scripts/test-coverage --strict
```

## Promote a model

Do not promote a model because it loads one time.

A model must:

1. Pass its semantic test.
2. Meet its performance threshold.
3. Keep the required memory reserve.
4. Unload correctly.
5. Pass the exposed-model protocol.
6. Have an approved license.
7. Use pinned artifacts.

After promotion, run:

```bash
./scripts/ai-stack protocol full
```

## Change code

1. Create a branch.
2. Make one logical change.
3. Add or update tests.
4. Update the documentation.
5. Run the static protocol.

```bash
./scripts/ai-stack protocol static
```

6. If the change affects a running model, run the applicable model test.
7. If the change affects discovery or routing, run the exposed protocol.
8. If the change affects Open WebUI, run the Open WebUI protocol.

## Pull request content

State:

- Purpose
- Scope
- Hardware and backend
- Test commands
- Test results
- Memory and performance changes
- License changes
- Rollback method

Keep procedures in simplified technical English. Use short sentences and approved terms.
