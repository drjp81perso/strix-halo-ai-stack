# Model selection tools

Use model-selection tools to make a candidate list. Use local tests to approve a model.

This project recommends 2 advisory tools:

- [`whichllm`](https://github.com/av/which-llm) or the current project link shown by its package metadata
- [FreeLLMArena Run at Home](https://freellmarena.com/home)

> **Caution:** These tools use estimates and public benchmark data. They do not test your exact driver, backend, quantization, prompt, or workload.

## Use `whichllm`

`whichllm` detects local hardware and ranks model candidates.

### 1. Install `uv`

Follow the official [`uv` installation instructions](https://docs.astral.sh/uv/getting-started/installation/).

### 2. Detect the local hardware

```bash
uvx whichllm@latest
```

### 3. Set a device-memory value

Use this form when automatic detection does not match the effective backend memory:

```bash
uvx whichllm@latest --vram 96
```

For a Ryzen AI Max+ system, compare the value with:

```bash
docker compose exec gateway llama-server --list-devices
```

Use the llama.cpp value for Vulkan planning.

### 4. Save the result

```bash
mkdir -p benchmark-results/model-selection
uvx whichllm@latest --vram 96 \
  | tee benchmark-results/model-selection/whichllm.txt
```

### 5. Interpret the result

Record these fields:

- Model repository
- Quantization
- Weight size
- Fit type
- Estimated speed
- Context limit
- Publication date
- Score

Do not treat the estimated speed as a measured result. Add the model to the candidate registry and run the local acceptance tests.

## Use FreeLLMArena

FreeLLMArena provides an interactive hardware simulator and category views.

### 1. Open the tool

Open [FreeLLMArena Run at Home](https://freellmarena.com/home).

### 2. Select the hardware

Select the closest hardware profile. Then, set:

- GPU count
- System RAM
- RAM type
- Precision
- KV-cache precision
- Context length

### 3. Review each category

The current interface includes categories such as:

- Chat
- Coding
- Vision
- Image
- Video
- Image edit
- Documents
- Search
- Image to video
- Video edit
- Agents

### 4. Record the input settings

A recommendation has no value without its input settings. Record the hardware, precision, KV cache, and context.

### 5. Record the estimate date

The model list and public benchmark data change frequently. Record the date shown by the site.

### 6. Check licenses and runtimes

Before you add a candidate, check:

- The official model license
- The conversion license
- The exact artifact names
- Backend support
- Required adapters or workflows
- The expected disk size

## Reference-system example

For the Ryzen AI Max+ 395 reference system, the project used:

```text
Hardware: Ryzen AI Max+ 395 128 GB
GPU count: 1
System RAM: 128 GB
Precision: Q5_K_M
KV cache: 8-bit
Context: 16K
Minimum acceptable decode speed: 7.5 tok/s
```

The detailed result is in [Hardware-driven model selection](HARDWARE-MODEL-SELECTION-2026-11-21.md).

## Convert a recommendation into a candidate

1. Add the candidate to `registry/models.yaml`.
2. Set `enabled: false`.
3. Set the correct track: `balanced`, `experimental`, or `staged`.
4. Add the exact source and artifact patterns.
5. Add the license.
6. Add a promotion gate.
7. Add a planned test to `tests/planned-models.yaml`.
8. Download only the candidate.
9. Add a temporary model endpoint.
10. Run local performance and semantic tests.

Example download command:

```bash
python3 scripts/model-manager.py \
  --track all \
  --id llm/qwen38-27b-q5 \
  sync
```

## Promotion criteria

A text model must meet all applicable requirements:

- It loads at the target context.
- It keeps the configured host reserve.
- It meets the local decode-speed threshold.
- It passes the semantic test for its role.
- It supports the required tools or vision inputs.
- It unloads and returns memory to the baseline range.
- Its license is approved.
- Its artifacts and revisions are pinned.

Image, video, and audio-generation models need latency and media-quality tests instead of token-speed tests.

## Recommended policy

Use this statement in issues and pull requests:

> `whichllm` and FreeLLMArena identified this model as a candidate. Local tests determine promotion.
