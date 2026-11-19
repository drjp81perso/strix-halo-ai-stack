# Local Speech and Audio Model Registry — 2026-11-19

Target: Ryzen AI Max+ 395 (`gfx1151`), 128 GiB unified RAM, no more than about 96 GiB GPU-mappable memory. The 96 GiB mapping is part of physical RAM, not extra VRAM.

## Decision

Use **audio.cpp v0.9.5** as the first experimental native execution plane. It exposes HIP/ROCm and Vulkan backends, GGUF packages, a model manager, WebUI, CLI, C ABI, and server routes including `/v1/audio/speech` and `/v1/audio/transcriptions`. It already lists Qwen3 ASR/TTS, MOSS, Fish, IndexTTS, VibeVoice, ACE-Step, HeartMuLa, YuE2 and many other current families. This dramatically reduces the adapter burden, but does **not** prove that every family works correctly or quickly on `gfx1151`.

Keep the present whisper.cpp + Kokoro baseline until the candidates pass clean-reboot tests. For Python-native projects, pin a TheRock/ROCm/PyTorch build known to target `gfx1151`; never assume a CUDA README or generic `device="cuda"` example constitutes AMD support.

## Balanced track (`2026.11.19`)

| Registry ID | Model / role | License | Size | Runtime / API | AMD assessment | Confidence |
|---|---|---:|---:|---|---|---|
| `speech/qwen3-asr-0.6b` | 52-language streaming ASR; song recognition | Apache-2.0 | 0.6B; upstream repo 1.47 GiB | audio.cpp HIP/Vulkan; OpenAI transcription | Native port exists; validate `gfx1151` | Model high; AMD medium |
| `speech/moss-transcribe-diarize-0.9b` | Long-form ASR + timestamps + speakers + events | Apache-2.0 | 0.9B; 1.71 GiB | audio.cpp HIP/Vulkan; OpenAI transcription | Strong functional fit; validate long-context memory and RTF | High / medium |
| `speech/moss-tts-nano-100m` | CPU-real-time multilingual TTS + clone | Apache-2.0 | 0.1B + tokenizer; ONNX repos 0.71 GiB | ONNX Runtime CPU, FastAPI/CLI; OpenAI adapter or vLLM-Omni | Safest AMD option because CPU path is first-class | High |
| `speech/qwen3-tts-0.6b-base` | Streaming multilingual TTS + 3 s clone | Apache-2.0 | 0.6B; 2.34 GiB | audio.cpp HIP/Vulkan; OpenAI speech | Native port exists; enrollment adapter and HIP test needed | High / medium |
| `music/ace-step-15-xl-turbo` | Text-to-song, covers, repaint/edit | MIT | 4B DiT (~9 GB bf16 weights); project registry currently reserves ~50 GiB disk | Official Gradio, Python, REST API; ROCm scripts | Best-supported AMD music candidate; benchmark before enablement | High / medium-high |

## Experimental track (`2026.11.19`)

| Registry ID | Why it is interesting | License / policy issue | Runtime and AMD risk | Confidence |
|---|---|---|---|---|
| `speech/qwen3-asr-1.7b-aligner` | Higher-accuracy ASR plus 0.6B forced aligner | Apache-2.0 | audio.cpp port; 5.53 GiB upstream combined; gfx1151 untested | High / medium |
| `speech/qwen3-tts-1.7b-suite` | Clone + named voices + natural-language voice design | Apache-2.0 | Three separate checkpoints; audio.cpp support listed, but streaming/enrollment/unload need tests | High / medium |
| `speech/fish-drama3` | 35B-A3B multi-character scenes, cloning, infill/editing | Fish Audio Community License—not permissive OSI | Quantized audio.cpp port exists; MoE/HIP path is young | Medium-high / medium-low |
| `audio/mimo-audio-7b-instruct` | Few-shot audio LM: understanding, continuation, voice/style conversion, editing | Repo says Apache-2.0; HF metadata observed MIT—resolve before promotion | Upstream CUDA + FlashAttention; no verified AMD path | High / low |
| `music/yue2-3b` | Frontier songs with explicit editable score planning, covers, agent editing | Code Apache-2.0; weights CC BY-NC 4.0 + creator terms; companies need commercial license | audio.cpp port exists; upstream explicitly calls AMD experimental | High / medium-low |
| `music/heartmula-3b` | Lyrics/tag-conditioned songs; 48 kHz stereo codec | Apache-2.0 | audio.cpp GGUF port exists; upstream CUDA assumptions; combined upstream repos ~20.85 GiB | High / medium |

## Watch list, not selected

- **IndexTTS-2.5 (0.8B, ~5.11 GiB):** excellent emotion/speed/pronunciation control and production vLLM support, but weights use the bilibili Model Use License. Consider only if its license is acceptable; audio.cpp has a native port.
- **VibeVoice:** ASR streaming/diarization is compelling and audio.cpp supports it, but the original 1.5B TTS code was removed after misuse; Microsoft labels the family research/development and discourages untested commercial/real-world deployment.
- **F5-TTS:** explicit ROCm 7.2 instructions and a mature codebase, but pretrained weights are CC-BY-NC. Useful benchmark/control, not the balanced default.
- **Step-Audio 2 mini:** broad audio reasoning and speech-to-speech capability, Apache-2.0, but the official path is CUDA/vLLM and the 7B-class deployment is less direct than MiMo or audio.cpp-native choices.
- **Whisper large-v3-turbo:** retain as a reliable baseline and regression oracle. It is no longer the most feature-rich option for diarization, song transcription, or forced alignment.

## AMD interpretation

1. `gfx1151` support is improving rapidly in vLLM and ROCm/TheRock, but AMD's general ROCm support matrix historically distinguishes officially supported discrete GPUs from community-enabled hardware. Treat this APU as **supported only after local proof**.
2. Preferred order: audio.cpp HIP → audio.cpp Vulkan → ONNX CPU → PyTorch ROCm/TheRock → CPU fallback.
3. Avoid FlashAttention-2 as a hard dependency. Prefer SDPA/eager only for short tests, or native audio.cpp kernels.
4. UMA permits large models to fit, but bandwidth and host-memory pressure still matter. Admit one large music/audio LM at a time and preserve at least 20 GiB for the host.

## Promotion gate

For each candidate pin the upstream commit, artifact revision, exact files and SHA-256. Then record, after a clean reboot:

- backend/device detection (`gfx1151`), cold-load time and peak physical/GTT memory;
- 1, 10 and 60 minute inputs for ASR where supported; timestamps and diarization correctness;
- TTS first-audio latency, RTF, long-text stability, multilingual and clone similarity;
- music generation at 30 s, 2 min and maximum intended duration; editing/cover modes;
- cancellation, timeout, malformed input, unload-to-baseline, and output persistence;
- Open WebUI end-to-end route and the consent-protected voice-enrollment boundary.

Do not mark an entry `enabled: true` solely because it loads on CPU or because its upstream project advertises ROCm generically.

## Primary sources

- https://github.com/0xShug0/audio.cpp
- https://github.com/QwenLM/Qwen3-ASR
- https://github.com/QwenLM/Qwen3-TTS
- https://github.com/OpenMOSS/MOSS-Transcribe-Diarize
- https://github.com/OpenMOSS/MOSS-TTS
- https://github.com/OpenMOSS/MOSS-TTS-Nano
- https://github.com/ace-step/ACE-Step-1.5
- https://github.com/fishaudio/fish-speech
- https://github.com/XiaomiMiMo/MiMo-Audio
- https://github.com/multimodal-art-projection/YuE
- https://github.com/HeartMuLa/heartlib
- https://github.com/index-tts/index-tts
- https://github.com/microsoft/VibeVoice
- https://github.com/SWivid/F5-TTS
- https://github.com/ROCm/TheRock
- https://rocm.docs.amd.com/projects/install-on-linux/en/latest/reference/system-requirements.html
