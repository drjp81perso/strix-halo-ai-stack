# Model testing

Every test enforces a lifecycle: unload all, baseline metrics, cold request, semantic validation, loaded-state capture, unload, and empty `/running` verification. Raw results go to `benchmark-results/`.

```bash
./scripts/ai-stack test MODEL_ID
./scripts/ai-stack test-all
```

## Current tests

- `llm/fast`: exact `local API ready`, normal stop, no hidden reasoning.
- `llm/coder`: extract and execute one Python block; exactly three asserts; verify unsorted/touching intervals and no mutation. Generated code execution is limited to the fixed trusted prompt.
- `llm/reasoning`: Bayes answer; nonempty final content; normal stop; below 1,536 tokens; LaTeX-aware `10/21` and `47.62%`; reject known wrong answers.
- `llm/vision`: generated red square PNG; response must identify red and square/rectangle.
- `retrieval/embedding`: three finite equal-length vectors; cat/kitten cosine similarity must exceed cat/database similarity.
- `retrieval/reranker`: AMD unified-memory document must score above cooking text.
- `speech/kokoro`: valid non-silent WAV longer than 0.3 seconds.
- `speech/whisper-large-v3-turbo`: transcribe the deterministic WAV produced by the Kokoro test and find local/speech/recognition/test.

`test-all` is sequential and orders Kokoro before Whisper.

## Candidate coverage

Candidates that are not yet runnable still require a concrete promotion test in `tests/planned-models.yaml`. This includes multilingual/diarization STT, cloning TTS, music generation/editing, image generation/editing, video generation, and adapter contracts. Use:

```bash
./scripts/ai-stack roster
```

Validation fails when an active model lacks an executable test or a canonical candidate lacks a planned test. See `docs/MODEL-ROSTER.md` for the full matrix.

## Staged multimedia promotion tests

Image/video/music/voice adapters must also verify decodable persistent output, requested dimensions/duration, cancellation, reproducibility where promised, output survival after unload, and authenticated consent-controlled voice enrollment.

## Interpretation

- Capacity rejection is a safe infrastructure result, not quality failure.
- Correct hidden reasoning with a wrong final answer is failure.
- HTTP 200 without semantic correctness is failure.
- Metrics lag is acceptable only when values return to baseline shortly after unload.
