# Hardware-driven model selection — 2026-11-21

Target profile:

```text
Ryzen AI Max+ 395 / Radeon 8060S
128 GiB physical unified RAM
96 GiB nominal mapping (~94.7 GiB seen by llama.cpp)
16K context
Q5-class precision preferred
Minimum acceptable estimated decode: 7.5 tok/s
```

Sources used:

- FreeLLMArena Run at Home interactive simulator, selected card `Ryzen AI Max+ 395 128 GB`, 128 GB RAM, Q5_K_M, 8-bit KV cache, 16K context, data updated 2026-11-21.
- `uvx whichllm@latest --vram 96` output supplied by the reference host.
- Local measured results from this repository.

Estimates are screening signals, not local benchmarks. Image/video rows do not publish token rates and require separate pipeline testing.

## FreeLLMArena category results

| Category | Best shown | Q5/selected memory | Estimated speed | Decision |
|---|---|---:|---:|---|
| Chat | Gemma 4 31B | ~25 GB | 8.2 tok/s | Add balanced candidate |
| Coding | Qwen3.8-27B | ~21 GB | 9.7 tok/s | Highest implementation priority |
| Vision | Gemma 4 31B | ~25 GB | 8.2 tok/s | Same candidate covers vision |
| Image | Qwen-Image-2.1 | ~8.6 GB Q5; 18 GB F16 | Not reported | Add balanced candidate; license review |
| Video | MiniMax H3 | ~27 GB Q5; 70 GB F16 | Not reported | Add experimental candidate |
| Image edit | Qwen-Image-2.1 | ~8.6 GB Q5; 18 GB F16 | Not reported | Same image candidate |
| Documents | Gemma 4 31B | ~25 GB | 8.2 tok/s | Same Gemma candidate |
| Search | Nothing fits | — | — | Use agent + external search tools, not another resident model |
| Image to video | MiniMax H3 | ~27 GB Q5; 70 GB F16 | Not reported | Same video candidate |
| Video edit | MiniMax H3 | ~27 GB Q5; 70 GB F16 | Not reported | Same video candidate |
| Agents | Qwen3.8-27B | ~21 GB | 9.7 tok/s | Same Qwen candidate |

## whichllm results supplied by host

The supplied output ranked:

| Rank | Model | Quant | Weights | Estimated speed | Context |
|---:|---|---|---:|---:|---:|
| 1 | Qwen3.8-Flash-Next | Q4_K_M | 88.0 GB | 20.8 tok/s | 256K |
| 2 | Qwen3.8-27B | Q6_K | 22.2 GB | 9.1 tok/s | 256K |
| 3 | Qwen3.6-35B-A3B | Q6_K | 27.3 GB | 40.8 tok/s | 256K |
| 4 | GPT-OSS-120B | Q8_0 | 59.0 GB | 28.4 tok/s | 128K |
| 5 | K2-Horizon-MoVA-36B-A4B | Q6_K | 28.7 GB | 30.4 tok/s | 512K→339K |
| 6 | Qwen3.5-122B-A10B | Q5_K_M | ~83.9 GB | 14.4 tok/s | 256K |
| 7 | Gemma 4 26B-A4B | Q6_K | 21.6 GB | 29.3 tok/s | 256K |
| 8 | Qwen3-Next-80B-A3B-Instruct | Q5_K_M | 52.9 GB | 36.6 tok/s | 256K |
| 9 | Gemma 4 31B | Q6_K | 23.5 GB | 8.6 tok/s | 256K |
| 10 | GPT-OSS-20B | Q8_0 | 11.3 GB | 43.1 tok/s | 128K |

Our target uses 16K rather than the tool's displayed maximum context, giving more cache headroom. However, Q5 instead of Q4/Q6 changes both size and speed; every chosen artifact still requires a local test.

## Recommended roster changes

### Promote to implementation queue

1. **Qwen3.8-27B Q5** — proposed IDs/roles: coding, agents, fast generalist, optional vision.
   - Official/base source: `Qwen/Qwen3.8-27B`
   - Conversion candidate: `unsloth/Qwen3.8-27B-GGUF`
   - Artifact candidate: `Qwen3.8-27B-UD-Q5_K_M.gguf` + projector
   - Expected screening result: about 9.7 tok/s at Q5/16K.
   - Goal: compare against both current 35B fast agent and 80B Coder Next.

2. **Gemma 4 31B Q5** — proposed roles: chat, vision, documents.
   - Conversion candidate: `unsloth/gemma-4-31B-it-GGUF`
   - Artifact candidate: `gemma-4-31B-it-Q5_K_M.gguf` + projector
   - Expected screening result: about 8.2 tok/s at Q5/16K.
   - Goal: challenge Qwen VL and add a document-oriented preset.

3. **Qwen-Image-2.1** — proposed roles: image and image edit.
   - Fits easily by capacity.
   - Must review Qwen Research License and pin the exact sd.cpp/Comfy components.

### Experimental queue

4. **Qwen3.8-Flash-Next Q5**.
   - whichllm's top result was Q4_K_M at 88 GB/20.8 tok/s, not Q5.
   - Published Q5 XL artifacts are extremely close to the effective 94.7 GiB mapping.
   - Treat Q5 as a tight-fit experiment; Q4 may be the practical production choice despite the preference.

5. **MiniMax H3** — video/image-to-video/video-edit.
   - Capacity appears feasible.
   - Needs license confirmation, AMD pipeline validation, and a pinned ComfyUI/stable-diffusion.cpp workflow.

6. **NVIDIA Nemotron 3.5 Super VL 120B A12B NVFP4** — agents/vision challenger.
   - Arena estimates 22 tok/s and 89 GB.
   - NVFP4 may be NVIDIA-oriented; do not assume an AMD Vulkan path from fit alone.

## Existing model decisions

| Current model | Keep? | Reason |
|---|---|---|
| Qwen3.5 35B-A3B Q5 fast | Yes, benchmark incumbent | Locally measured ~52 tok/s and reliable |
| Qwen3.5 122B-A10B Q4 reasoner | Yes | Locally measured ~23 tok/s, bounded reasoning works |
| Qwen Coder Next Q5 | Yes until A/B | Locally measured ~53 tok/s; Qwen3.8 needs code/agent quality comparison |
| Qwen3 VL 32B | Yes until A/B | Working baseline; Gemma/Qwen3.8 multimodal challengers need tests |
| Retrieval/audio baseline | Yes | Arena categories do not replace embeddings, reranking, STT, or TTS |

## Category architecture

Do not necessarily assign one weight set per UI category. Use Open WebUI presets over a smaller tested backend roster:

- Chat/Documents/Vision → Gemma 4 31B candidate or current vision model.
- Coding/Agents → Qwen3.8-27B candidate.
- Search → fast agent plus web-search tools/RAG; simulator reports no fitting dedicated search model.
- Image/Image Edit → Qwen-Image-2.1 pipeline.
- Video/Image-to-video/Video-edit → MiniMax H3 experimental pipeline.

## Promotion thresholds

A candidate is promoted only if:

- 16K context loads with configured host reserve;
- measured decode is at least 7.5 tok/s;
- semantic/category tests beat or complement the incumbent;
- peak memory and unload pass;
- license is recorded;
- exact artifacts and checksums are pinned;
- Open WebUI role preset is documented.
