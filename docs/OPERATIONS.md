# Operations and observed behavior

This records facts established on the Bosgame M5, Ryzen AI Max+ 395, 128 GB unified memory, Ubuntu, and llama.cpp Vulkan.

## Confirmed Vulkan device

```bash
docker compose exec gateway llama-server --list-devices
```

Observed:

```text
Vulkan0: Radeon 8060S Graphics (RADV GFX1151) (96986 MiB, 96813 MiB free)
```

llama.cpp can use approximately 94.71 GiB on this device.

The result also confirms that llama.cpp selected the Radeon device. It did not select llvmpipe.

`rocm-smi`, DRM GTT counters, and gateway metrics can report different memory pools.

The headless `vulkaninfo` warnings about DISPLAY, XDG, and display planes do not affect this compute task.

## Memory and admission policy

The 96 GB mapping is part of the 128 GB physical pool, not additional RAM.

- Heavyweight models require at least 20 GiB host `MemAvailable` before start.
- Retrieval/speech workloads require 16 GiB.
- `--fit on --fit-target 4096 --fit-ctx 16384` preserves about 4 GiB Vulkan headroom and permits host placement.
- One heavyweight model runs at a time.
- Q8 KV caches reduce context memory.
- TTL and explicit unload reclaim allocations.

`admit-run` protects a host reserve; it is not a model-size estimator. llama.cpp is the authoritative allocator.

## Measured models

| Model | Cold request/load | Prompt | Generation | GPU | Host increment | Unload | Quality |
|---|---:|---:|---:|---:|---:|---:|---|
| Qwen 35B-A3B Q5 | 2.5–5.5 s cached | ~140 tok/s | ~52 tok/s | ~26 GB class | small | <1 s | Exact smoke response passed |
| Qwen Coder Next Q5 | 41.22 s / ~34.54 s | 113.38 tok/s | 53.41 tok/s | ~53.37 GiB | ~0.6 GiB | 0.69 s | Generated code executed and passed tests |
| Qwen 122B-A10B Q4 | ~90–96 s / ~44–46 s | 118–132 tok/s | 20.6–23.1 tok/s | ~64 GiB | ~8.4 GiB | 0.76–0.83 s | Correct with final tuned budget |

Telemetry can lag process exit briefly. Verify `/running` immediately, then allow several metrics intervals for memory counters.

## Reasoning model behavior

- Unrestricted 1,024 tokens: all tokens went to `reasoning_content`; final content was empty.
- 512-token reasoning budget: forced a premature transition and produced a wrong recalculation.
- Validated setting:

```text
--reasoning on
--reasoning-effort low
--reasoning-budget 768
--reasoning-budget-message "Reasoning budget reached. Use the values already computed above, verify the numerator once, and provide only the concise final answer."
```

Clients should allow `max_tokens: 1536`. The validated Bayes test returned `finish_reason: stop`, nonempty content, 1,191 tokens, `10/21`, and `47.62%`.

## LaTeX-aware validation

Equivalent answers may appear as `10/21`, `\frac{10}{21}`, `47.62%`, or `47.62\%`. Tests normalize `\frac`, `\dfrac`, `\tfrac`, escaped percentages, and math delimiters before checking final content.

## Removed llama.cpp option

`--no-mmap` was removed. Current explicit mmap disabling is `--load-mode none`; default `--load-mode auto` remains recommended. Policy, generation, static checks, and runtime checks prevent regression.

## User-facing commands

```bash
./scripts/ai-stack status
./scripts/ai-stack models
./scripts/ai-stack config
./scripts/ai-stack test llm/fast
./scripts/ai-stack test-all
./scripts/ai-stack unload
./scripts/ai-stack ui
```
