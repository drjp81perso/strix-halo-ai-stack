# Customizing for other hardware

This repository provides one authenticated, OpenAI-compatible catalog.

It also provides on-demand loading, semantic tests, and memory admission.

The included model roster is a reference profile. The project validated it on a Ryzen AI Max+ 395 system with 128 GiB of unified memory.

The roster is not a universal recommendation.

## Concepts first

### Discrete GPU

System RAM and VRAM are physically separate. A model may use both through partial offload, but CPU-resident tensors cross PCIe and are usually much slower.

```text
physical usage = host process/RAM + GPU VRAM
```

Both limits must be satisfied independently.

### Unified-memory GPU/APU

CPU and GPU map the same physical pool. A 96 GiB GPU mapping on a 128 GiB machine is **not** 224 GiB of capacity.

```text
GPU-mapped pages + CPU-only pages + OS/services <= physical RAM
```

Use the backend's device report to learn its effective allocation view:

```bash
docker compose exec gateway llama-server --list-devices
```

Different tools can report firmware carve-outs, GTT, Vulkan heaps, ROCm pools, or physical RAM. They are not necessarily contradictory.

## Sizing formulas

Use GiB consistently (`bytes / 1024^3`). Decimal model-card GB values are only estimates.

### Weight estimate

```text
raw weight GiB ≈ parameter_count × bits_per_weight / 8 / 1024^3
```

Then add 5–15% for quantization metadata/alignment. Published artifact size is better than the formula.

Typical rough multipliers:

| Format | Approx. bytes/parameter | Notes |
|---|---:|---|
| FP32 | 4.00 | Rare for local inference |
| BF16/FP16 | 2.00 | Highest normal inference fidelity |
| Q8 | 1.00–1.10 | Near-lossless, still large |
| Q6 | 0.75–0.85 | Strong quality/capacity compromise |
| Q5 | 0.63–0.72 | Common quality-focused local quant |
| Q4 | 0.50–0.60 | Common capacity-focused quant |
| Q3 | 0.38–0.48 | Useful for very large models |
| IQ2/IQ1 | 0.20–0.38 | Experimental/high quality loss |

MoE models still store all experts. Active parameters mainly predict compute per token, not resident weight size.

### Runtime budget

```text
runtime working set ≈ weights + KV cache + compute buffers + projector/encoders + safety margin
```

Start with these planning margins:

| Workload | Extra beyond weights |
|---|---:|
| Text LLM, 8K–16K, one slot | 10–20% + 2 GiB |
| Text LLM, 32K–64K | 15–30% + 2–6 GiB |
| Vision-language | Text margin + mmproj/image-token buffers |
| Image diffusion | 30–100%, model-dependent |
| Video diffusion | 50–200%, resolution/frame-dependent |

KV cache varies by architecture, context, parallel slots, and cache dtype. Measure it; do not rely on parameter count alone.

### Safe capacities

For a discrete GPU:

```text
safe VRAM budget = detected VRAM - GPU reserve
safe host budget = physical RAM - host reserve
```

For unified memory:

```text
safe mapped budget = min(effective GPU mapping - GPU reserve,
                         physical RAM - host reserve)
safe total AI working set = physical RAM - host reserve
```

Recommended initial reserves:

```text
host reserve = max(8 GiB, 15–25% of physical RAM)
GPU reserve  = max(2 GiB, 5–10% of effective VRAM/mapping)
```

Increase host reserve when the same machine runs a desktop, Open WebUI, databases, build jobs, or media pipelines.

## Common capacity profiles

These are conservative starting points, not guarantees. Weight budgets assume one main model, Q8 KV cache, one slot, and moderate context.

### Discrete GPUs

| System RAM | VRAM | Suggested host reserve | GPU reserve | Comfortable main-model weights | Typical model tier |
|---:|---:|---:|---:|---:|---|
| 16 GiB | 8 GiB | 6 GiB | 1.5–2 GiB | 4–6 GiB | 3B–8B Q4/Q5 |
| 32 GiB | 12 GiB | 8 GiB | 2 GiB | 7–9 GiB | 7B–14B Q4 |
| 32 GiB | 16 GiB | 8 GiB | 2–3 GiB | 10–13 GiB | 14B Q5; 20B Q4 |
| 64 GiB | 24 GiB | 12 GiB | 3–4 GiB | 16–20 GiB | 24B–32B Q4/Q5 |
| 64 GiB | 32 GiB | 12 GiB | 4 GiB | 23–27 GiB | 32B Q6; 70B Q3 with spill |
| 128 GiB | 48 GiB | 20 GiB | 5–6 GiB | 36–42 GiB | 70B Q4; large MoE Q3/Q4 |
| 128 GiB | 80 GiB | 20 GiB | 6–8 GiB | 64–72 GiB | 70B Q8; 100B+ Q4 |

Partial CPU offload can exceed the VRAM column, but performance depends strongly on PCIe bandwidth and tensor placement.

### Unified-memory systems

| Physical RAM | Effective GPU mapping | Suggested host reserve | GPU reserve | Comfortable main-model weights | Typical model tier |
|---:|---:|---:|---:|---:|---|
| 16 GiB | 8–12 GiB | 6 GiB | 1–2 GiB | 4–6 GiB | 3B–8B Q4 |
| 32 GiB | 20–24 GiB | 8 GiB | 2 GiB | 12–17 GiB | 14B Q6; 24B Q4 |
| 64 GiB | 40–48 GiB | 12–16 GiB | 3–4 GiB | 28–38 GiB | 32B Q8; 70B Q3/Q4 |
| 96 GiB | 64–72 GiB | 16–20 GiB | 4–6 GiB | 48–58 GiB | 70B Q5/Q6; large MoE |
| 128 GiB | 64 GiB | 20–24 GiB | 4 GiB | 52–58 GiB mapped plus host spill | 70B Q6; 100B+ hybrid |
| 128 GiB | 96 GiB nominal (~94.7 observed) | 20–28 GiB | 4–8 GiB | 72–86 GiB | 100B–130B Q4; large MoE |
| 192 GiB | 144–160 GiB | 28–40 GiB | 8–12 GiB | 120–140 GiB | 200B+ Q4/Q3 experiments |

The "comfortable weights" column leaves room for normal runtime buffers. Long contexts, parallel users, image encoders, and video latents reduce it.

## Translating the table into configuration

### Admission reserve

`admit-run`'s first number is **minimum host `MemAvailable` before launch**, not model size:

```yaml
cmd: >-
  admit-run 12 4 --
  llama-server ...
```

Use roughly:

| Physical RAM | Headless appliance | Desktop/mixed-use host |
|---:|---:|---:|
| 16 GiB | 4–5 GiB | 6–8 GiB |
| 32 GiB | 6–8 GiB | 8–12 GiB |
| 64 GiB | 10–12 GiB | 12–18 GiB |
| 96 GiB | 14–18 GiB | 18–24 GiB |
| 128 GiB | 18–24 GiB | 24–32 GiB |
| 192 GiB | 28–36 GiB | 36–48 GiB |

The second number is the maximum current GTT use before a model starts.

This value detects an allocation that did not unload. It is not the final model-memory limit.

If the counter is not reliable on your hardware, adapt the guard. Do not silently remove the safeguard.

### llama.cpp fitting

For models close to capacity:

```text
--n-gpu-layers auto
--fit on
--fit-target 4096
--fit-ctx 8192
```

Choose `fit-target` from GPU reserve in MiB:

| Effective VRAM | Starting `--fit-target` |
|---:|---:|
| 8–12 GiB | 1024–1536 |
| 16–24 GiB | 2048–3072 |
| 32–48 GiB | 3072–4096 |
| 64–96 GiB | 4096–8192 |
| 128+ GiB | 8192–12288 |

Set `fit-ctx` to the smallest acceptable context. Automatic fitting cannot reduce the context below this value.

Use 16K as a starting floor for coding or RAG. Use 4K–8K for simple chat on a small GPU.

### Context and parallelism

Memory scales with total active context and slots. Start with:

```text
--parallel 1
--ctx-size 8192 or 16384
--cache-type-k q8_0
--cache-type-v q8_0
```

Raise one variable at a time. Advertised 128K/256K model context is a capability ceiling, not a sensible default.

## Backend customization

The supplied image is Vulkan-oriented and broadly suitable for AMD/Intel Vulkan devices. Other hardware may require a different base image/runtime:

| Hardware | Preferred first backend | Container/device considerations |
|---|---|---|
| AMD APU/GPU | Vulkan; benchmark ROCm | `/dev/dri`; ROCm also needs `/dev/kfd` |
| NVIDIA | CUDA image | NVIDIA Container Toolkit and GPU reservation |
| Intel Arc/iGPU | Vulkan/SYCL where supported | `/dev/dri`; test model coverage |
| CPU-only | CPU build | Remove GPU devices; choose smaller models |
| Apple Silicon | Native Metal, not Linux Docker | Use native llama.cpp/llama-swap |

Do not assume a CUDA-, ROCm-, Vulkan-, and Metal-specific optimization has identical flags or model support.

## Model selection and replacement

For every role, record:

- official publisher repository and license;
- conversion repository and exact revision;
- artifact filenames/checksums;
- architecture/runtime support;
- weight size and expected context;
- promotion status and test definition.

Update `registry/` first. Promote into `templates/llama-swap.yaml` only after the model passes `docs/TESTING.md`.

When replacing a model:

1. Add/download exact artifacts under `MODEL_DIR`.
2. Add a new model ID or preserve the stable role alias.
3. Start with one slot and conservative context.
4. Add/update the semantic test.
5. Measure cold load, throughput, peak memory, and unload.
6. Only then make it the default alias.

## Customization checklist

```bash
cp .env.example .env
./scripts/preflight
docker compose build --pull
docker compose run --rm --entrypoint llama-server gateway --list-devices
./scripts/generate-config
./scripts/validate
./scripts/start
./scripts/ai-stack models
./scripts/ai-stack test-all
```

Before sharing results, include hardware, physical RAM, effective device memory from `--list-devices`, backend/build version, quantization, context, parallel slots, and whether the run was cold or warm.
