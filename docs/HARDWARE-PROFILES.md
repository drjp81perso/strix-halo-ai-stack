# Practical hardware profiles

These profiles translate the sizing rules in `CUSTOMIZING.md` into starting configurations. They are deliberately conservative and assume one active generation model, one parallel slot, Q8 KV cache, and an otherwise reasonably idle host.

> Applying a profile changes safety/fitting thresholds only. It does **not** replace the checked-in 35B/122B model roster. Select and configure models that fit the profile before starting.

Apply safely:

```bash
cp .env.example .env          # first installation only
./scripts/apply-profile profiles/discrete-24gb.env
```

The command backs up `.env`, replaces profile keys, runs preflight, regenerates configuration, and validates it.

## Discrete GPU profiles

CPU spill traverses PCIe and may be much slower. "Main model" describes approximate weights, not total runtime working set.

| Profile | Assumed system RAM | GPU reserve | Host reserve | Initial context floor | Comfortable main-model weights | Practical role selection |
|---|---:|---:|---:|---:|---:|---|
| 8 GB VRAM | 16+ GiB | 1.5 GiB | 6 GiB | 4K | 4–6 GiB | 3B–8B Q4/Q5 chat/coder; 0.5B embedding; Whisper/Kokoro CPU |
| 12 GB VRAM | 24–32 GiB | 2 GiB | 8 GiB | 8K | 7–9 GiB | 7B–14B Q4; small VLM; light SD/Flux quantized |
| 16 GB VRAM | 32+ GiB | 2.5 GiB | 8 GiB | 8K | 10–13 GiB | 14B Q5/Q6; 20B Q4; medium VLM/image models |
| 24 GB VRAM | 48–64 GiB | 3 GiB | 12 GiB | 8K | 16–20 GiB | 24B–32B Q4/Q5; 70B Q2/Q3 hybrid; modern image models |
| 48 GB VRAM | 96–128 GiB | 5 GiB | 20 GiB | 16K | 36–42 GiB | 70B Q4; large MoE Q3/Q4; larger image/video experiments |

### 8 GB discrete

```dotenv
HEAVY_HOST_RESERVE_GB=6
GPU_FIT_TARGET_MIB=1536
MIN_FIT_CONTEXT=4096
```

Start with an 8B Q4_K_M-class model, 4K–8K context, and `--parallel 1`. Keep embeddings and TTS on CPU where practical. Do not use the reference 35B model.

### 12 GB discrete

```dotenv
HEAVY_HOST_RESERVE_GB=8
GPU_FIT_TARGET_MIB=2048
MIN_FIT_CONTEXT=8192
```

A 14B Q4 or efficient 20B-class low-bit model is realistic. Vision projectors consume extra memory; budget for them separately.

### 16 GB discrete

```dotenv
HEAVY_HOST_RESERVE_GB=8
GPU_FIT_TARGET_MIB=2560
MIN_FIT_CONTEXT=8192
```

Prefer 14B Q5/Q6 or 20B Q4. A 32B Q3 may load but leaves little room for context. For image generation, retain at least 2–4 GiB for VAE/text encoders and activations.

### 24 GB discrete

```dotenv
HEAVY_HOST_RESERVE_GB=12
GPU_FIT_TARGET_MIB=3072
MIN_FIT_CONTEXT=8192
```

This is a strong 24B–32B Q4/Q5 tier. A 70B Q2/Q3 can be evaluated with host spill, but decode speed depends on PCIe bandwidth. Increase the reserve for desktop/gaming use.

### 48 GB discrete

```dotenv
HEAVY_HOST_RESERVE_GB=20
GPU_FIT_TARGET_MIB=5120
MIN_FIT_CONTEXT=16384
```

Target 70B Q4 or large MoE models with published weights around 36–42 GiB. Video and 30B+ diffusion pipelines can still need substantial transient memory.

## Unified-memory profiles

The mapping and host use share one physical pool. The "effective mapping" must be measured with the backend, for example:

```bash
docker compose exec gateway llama-server --list-devices
```

| Profile | Typical effective mapping | GPU reserve | Host reserve | Context floor | Comfortable main-model weights | Practical role selection |
|---|---:|---:|---:|---:|---:|---|
| 32 GB unified | 20–24 GiB | 2 GiB | 8 GiB | 4K | 12–17 GiB | 14B Q6; 24B Q4; small VLM/image |
| 64 GB unified | 40–48 GiB | 4 GiB | 12 GiB | 8K | 28–38 GiB | 32B Q8; 70B Q3/Q4; medium video |
| 128 GB unified | 64–96 GiB | 4–8 GiB | 20–28 GiB | 16K | 52–86 GiB depending mapping | 70B Q6/Q8; 100B–130B Q4 hybrid; large MoE |

### 32 GB unified

```dotenv
HEAVY_HOST_RESERVE_GB=8
GPU_FIT_TARGET_MIB=2048
MIN_FIT_CONTEXT=4096
```

Use a 14B Q5/Q6 or 24B Q4 model. Do not map so much memory that the OS and model loader lose the 8 GiB reserve. One medium model at a time.

### 64 GB unified

```dotenv
HEAVY_HOST_RESERVE_GB=12
GPU_FIT_TARGET_MIB=4096
MIN_FIT_CONTEXT=8192
```

This supports high-quality 32B models and 70B Q3/Q4 experiments. Keep image/video pipelines exclusive because weights and latents compete for the same physical pages.

### 128 GB unified

```dotenv
HEAVY_HOST_RESERVE_GB=20
GPU_FIT_TARGET_MIB=4096
MIN_FIT_CONTEXT=16384
```

If the backend exposes only 64 GiB, use approximately 52–58 GiB for mapped weights. Put the remaining model data in host memory.

If the backend exposes approximately 96 GiB, use approximately 72–86 GiB for weights after the reserve.

The reference system showed 94.7 GiB in llama.cpp. It ran a 76.5 GiB, 122B MoE quant with hybrid placement.

## Model-role templates by tier

| Tier | Fast agent | Strong model | Coding | Vision | Retrieval | Speech |
|---|---|---|---|---|---|---|
| 8 GB | 3B–8B Q4 | Same model | 7B coder Q4 | 3B–7B VLM Q4 | 0.3B–1B CPU/Q8 | Whisper small/medium; Kokoro CPU |
| 12 GB | 7B–14B Q4 | 14B Q4 | 7B–14B coder | 7B VLM | ≤1B embedding/reranker | Whisper turbo; Kokoro CPU |
| 16 GB | 14B Q5 | 20B Q4 | 14B coder Q5 | 7B–14B VLM | 1B–4B one at a time | Whisper turbo; richer TTS |
| 24 GB | 24B–32B Q4 | 32B Q4/Q5 | 24B–32B coder | 14B–32B VLM Q4 | 4B models | Full speech stack |
| 48 GB | 32B Q8 | 70B Q4 | 32B+ coder | 32B VLM | 4B–8B models | Full speech stack |
| 32 GB unified | 14B Q6 | 24B Q4 | 14B–24B coder | 7B–14B VLM | 1B–4B | Full light speech stack |
| 64 GB unified | 32B Q6/Q8 | 70B Q3/Q4 | 32B coder | 32B VLM Q4 | 4B | Full speech stack |
| 128 GB unified | 35B MoE Q5 | 70B Q8 / 100B–130B Q4 | 80B MoE Q5 | 32B+ VLM | 4B–8B | Full speech and advanced media |

These are architecture classes, not endorsements of a specific daily-changing model. Use the versioned registries as candidate lists and verify licenses.

## Profile acceptance procedure

After applying a profile and selecting models:

```bash
./scripts/preflight
docker compose run --rm --entrypoint llama-server gateway --list-devices
./scripts/start
./scripts/ai-stack models
./scripts/ai-stack test-all
```

Record cold-load time, prompt/decode throughput, peak host/device memory, and unload behavior. If a model loads only by exhausting the reserve, choose a smaller quant/model instead of weakening the guard.
