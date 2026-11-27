# Reference profile: Ryzen AI Max+ 395 / 128 GB

This repository's checked-in model template is the validated reference profile for:

```text
System: Bosgame M5
APU: Ryzen AI Max+ 395
GPU: Radeon 8060S / RADV GFX1151
Physical memory: 128 GB unified
Nominal GPU mapping: 96 GB
Observed llama.cpp Vulkan memory: 96,986 MiB total / 96,813 MiB free
OS: Ubuntu
Runtime: llama-swap unified Vulkan container
```

The generic architecture and sizing rules are in `docs/CUSTOMIZING.md`. This file records only the reference-hardware decisions.

## Reference reserves

```text
Minimum host MemAvailable for heavy models: 20 GiB
Minimum host MemAvailable for light models: 16 GiB
Normal Vulkan fitting reserve: 4 GiB
One heavyweight model at a time
Q8 KV cache
```

The 96 GB mapping shares the same 128 GB physical pool. It is not extra memory.

## Reference model profiles

| Role | Artifact class | Context | Placement |
|---|---|---:|---|
| Fast agent | Qwen 35B-A3B Q5 | 32K | Full offload |
| Reasoner | Qwen 122B-A10B Q4 | 16K | Automatic GPU/host fit |
| Coder | Qwen Coder Next Q5 | 32K | Automatic GPU/host fit |
| Vision | Qwen VL 32B Q4 + Q8 projector | 32K | Full/automatic offload |
| Embedding | Qwen Embedding 4B Q8 | 32K ceiling | GPU |
| Reranker | Qwen Reranker 4B Q4 | 32K ceiling | GPU |
| STT | Whisper Large V3 Turbo Q5 | N/A | Vulkan |
| TTS | Kokoro 82M Q8 | N/A | CPU |

## Validated reasoning settings

```text
--reasoning on
--reasoning-effort low
--reasoning-budget 768
--reasoning-budget-message "Reasoning budget reached. Use the values already computed above, verify the numerator once, and provide only the concise final answer."
```

Clients should allow at least 1,536 completion tokens. Mathematical tests normalize plain-text and LaTeX equivalents.

## Known tooling considerations

- `llama-server --list-devices` is authoritative for the effective Vulkan allocation view.
- `rocm-smi` and DRM counters may report different pools.
- Headless Vulkan display warnings are benign.
- `--no-mmap` is obsolete; default `--load-mode auto` is used.
- Gateway metrics can lag after unload; `/running` changes immediately.

See `docs/OPERATIONS.md` for measured performance and `docs/TESTING.md` for acceptance tests.
