# Canonical model roster and test coverage

`registry/models.yaml` is the canonical roster. It contains 24 entries divided by lifecycle—not 24 advertised endpoints.

| Lifecycle | Meaning | Test requirement |
|---|---|---|
| `active` / `enabled: true` | Configured in llama-swap and downloadable by current scripts | Executable semantic/lifecycle test in `tests/models.yaml` |
| `balanced` candidate | Preferred next candidate based on license/runtime/API fit | Promotion specification in `tests/planned-models.yaml` |
| `experimental` candidate | Frontier capability with runtime/license uncertainty | Planned test plus blocker/gate |
| `staged` candidate | Desired modality requiring adapter/artifact/workflow | Planned contract and persistence test |

Run:

```bash
./scripts/ai-stack roster
```

Current coverage is 8 executable active tests and 16 planned candidate tests. Validation fails if any canonical entry lacks the appropriate coverage.

## Active baseline

| ID | Role | Test |
|---|---|---|
| `llm/fast` | Fast agent | Exact final response, no hidden reasoning |
| `llm/reasoning` | Strong reasoning | LaTeX-aware Bayes correctness, bounded reasoning |
| `llm/coder` | Coding agent | Generated Python execution and invariants |
| `llm/vision` | Vision-language | Deterministic red-square recognition |
| `retrieval/embedding` | Embeddings | Semantic cosine ordering |
| `retrieval/reranker` | Reranking | Relevant document outranks irrelevant one |
| `speech/whisper-large-v3-turbo` | STT | Deterministic keyword transcription |
| `speech/kokoro` | TTS | Valid non-silent WAV and duration |

These remain the regression oracle while newer candidates are evaluated.

## Balanced candidates

| ID | Main promotion test |
|---|---|
| `speech/qwen3-asr-0.6b` | Multilingual/song STT, streaming latency, RTF |
| `speech/moss-transcribe-diarize-0.9b` | WER, timestamps, speaker-turn F1, events |
| `speech/moss-tts-nano-100m` | CPU RTF, long text, cloning and consent boundary |
| `speech/qwen3-tts-0.6b-base` | Streaming TTS, multilingual clone, voice enumeration |
| `music/ace-step-15-xl-turbo` | 30 s/2 min songs, BPM/duration, cover/repaint, cancellation |

## Experimental candidates

| ID | Main promotion test/blocker |
|---|---|
| `speech/qwen3-asr-1.7b-aligner` | WER plus forced-alignment boundary error |
| `speech/qwen3-tts-1.7b-suite` | Base clone, custom voice, voice design, enrollment security |
| `speech/fish-drama3` | Multi-speaker separation, infill, license acceptance |
| `audio/mimo-audio-7b-instruct` | AMD port without CUDA dependency; caption/generation/editing |
| `music/yue2-3b` | Score conditioning/editing and non-commercial license review |
| `music/heartmula-3b` | Lyrics presence, stereo 48 kHz output, cancellation |

## Staged multimedia candidates

| ID | Main promotion test/blocker |
|---|---|
| `speech/chatterbox-clone` | Consent-protected enrollment and clone similarity |
| `image/flux2-klein` | Exact artifacts, generation/editing, dimensions and seed repeatability |
| `image/z-image-turbo` | Typography OCR, dimensions and deterministic seed |
| `video/wan22-5b` | ffprobe, frames/duration, conditioning, cancellation and persistence |
| `music/ace-step-xl` | OpenAI adapter, async jobs and persistent output |

There are two ACE-Step entries because one describes the balanced upstream XL-Turbo evaluation and one describes the eventual public adapter endpoint. They may be consolidated when the adapter pins a single artifact/revision.

## Keeping the roster current

1. Add a candidate to `registry/models.yaml` with `enabled: false`, a track, stage, license, runtime, and promotion gate.
2. Add its acceptance contract to `tests/planned-models.yaml` in the same commit.
3. Implement runtime/adapter and exact artifacts.
4. Move the test into executable `tests/models.yaml` and implement its test kind.
5. Run the test from a clean unload state and capture memory/performance.
6. Only then set `enabled: true` and add it to `templates/llama-swap.yaml`.

Versioned frontier/lab registries remain discovery snapshots. The canonical roster is the subset the project has consciously accepted into its lifecycle.
