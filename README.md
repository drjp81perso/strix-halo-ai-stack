# On-Demand Local AI Stack

Docker-based, OpenAI-compatible model catalog with automatic loading/unloading, memory admission, and semantic tests. It can be adapted to discrete GPUs, unified-memory APUs, or CPU-only hosts.

The checked-in roster is a validated **reference profile** for a Bosgame M5 / Ryzen AI Max+ 395 / 128 GB Ubuntu system. Start with:

- `docs/CUSTOMIZING.md` — generic sizing formulas, common RAM/VRAM tables, backend choices, and adaptation checklist
- `docs/HARDWARE-PROFILES.md` — practical 8/12/16/24/48 GB discrete and 32/64/128 GB unified examples
- `profiles/` — apply-ready memory-policy starting points
- `docs/REFERENCE-STRIX-HALO.md` — decisions specific to the validated reference system
- `docs/ARCHITECTURE.md` — control and execution planes
- `docs/OPERATIONS.md` — measured behavior and troubleshooting
- `docs/OPEN-WEBUI.md` — connection setup, audio/RAG wiring, concurrency and 429 troubleshooting
- `docs/MODEL-ROSTER.md` — canonical active/balanced/experimental/staged roster
- `docs/TESTING.md` — executable tests and candidate promotion contracts
- `docs/AUTOMATED-TEST-PROTOCOL.md` — static, smoke, active, exposed, Open WebUI, full, and soak suites
- `docs/EXPOSED-MODEL-TEST.md` — prove every canonical model listed by live `/v1/models` works

## What is operational on day one

One authenticated endpoint (`http://HOST:9292/v1`) announces and loads on demand:

| ID | Engine | Function |
|---|---|---|
| `llm/fast` | llama.cpp Vulkan | Qwen 3.5 35B-A3B Q5 fast agent |
| `llm/reasoning` | llama.cpp Vulkan | Qwen 3.5 122B-A10B Q4 reasoner |
| `llm/coder` | llama.cpp Vulkan | Qwen 3 Coder Next Q5 |
| `llm/vision` | llama.cpp Vulkan | Qwen 3 VL 32B Q4 + Q8 projector |
| `retrieval/embedding` | llama.cpp Vulkan | Qwen 3 Embedding 4B Q8 |
| `retrieval/reranker` | llama.cpp Vulkan | Qwen 3 Reranker 4B Q4 |
| `speech/whisper-large-v3-turbo` | whisper.cpp Vulkan | Speech recognition |
| `speech/kokoro` | audio.cpp CPU | Text-to-speech |

The concrete source/artifact registry is `registry/models.yaml`. Versioned selection tracks are also included:

- `models-v2.2026-11-stable.yaml` — conservative baseline
- `models-v3.2026-11-frontier.yaml` — recent credible candidates
- `models-v4.2026-11-lab.yaml` — speculative watchlist

See `registry/README.md`. Registries do not automatically announce models; only promoted entries added to `config/llama-swap.yaml` appear through `/v1/models`. Review all tracks with `./scripts/registry-report`.

Video, advanced images, music, and voice cloning are deliberately recorded as **staged** entries. They need pinned ROCm images plus workflow/API adapters; see `docs/STAGED-MULTIMEDIA.md`. They are not falsely advertised as working OpenAI endpoints before those adapters are built and tested.

## Memory policy

Memory thresholds are configured in `.env`, interpreted as **pre-start safety reserves**, and documented in `docs/CUSTOMIZING.md`. The checked-in defaults preserve the validated reference behavior: 20 GiB host reserve for heavy models, 16 GiB for light models, automatic llama.cpp fitting, and one heavyweight model at a time.

On unified-memory systems, mapped GPU memory is part of physical RAM—not additional capacity. On discrete systems, RAM and VRAM are separate constraints. In both cases, measure cold-load peaks and unloading before promoting a model.

Model processes are children of llama-swap; group switching and TTL terminate old servers. No Docker socket is mounted and inference should not depend on disk swap.

## 1. Prerequisites

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-v2 python3-pip vulkan-tools
sudo usermod -aG docker,video,render "$USER"
```

Log out and back in. Confirm:

```bash
vulkaninfo --summary
ls -l /dev/dri
cat /sys/class/drm/card*/device/mem_info_gtt_total
```

Use a kernel and driver supported by your hardware. The reference image uses Vulkan; CUDA, ROCm, SYCL, Metal, and CPU-only deployments require the corresponding engine image or native runtime. See `docs/CUSTOMIZING.md`.

## 2. Configure

```bash
cp .env.example .env
```

Determine group IDs:

```bash
getent group video
getent group render
```

Put the numeric values into `VIDEO_GID` and `RENDER_GID`.

Choose memory-policy values using `docs/CUSTOMIZING.md` or apply a starting profile:

```bash
./scripts/apply-profile profiles/discrete-24gb.env
# or: profiles/unified-32gb.env, unified-64gb.env, unified-128gb.env
```

The command backs up `.env`, changes safety/fitting thresholds, regenerates, and validates. It does not change the model roster. The `.env.example` defaults match the 128 GB reference system; smaller hosts must select smaller model artifacts and update the model template.

Set the host model library in `.env`. For example:

```dotenv
MODEL_DIR=/srv/ai-models
```

Create it and grant your user ownership:

```bash
sudo mkdir -p /srv/ai-models
sudo chown "$USER:$USER" /srv/ai-models
```

Compose mounts `${MODEL_DIR}` read-only at `/models` inside the gateway. All paths in `config/llama-swap.yaml` are container paths under `/models`; download and check scripts resolve the same host `MODEL_DIR` automatically. You can instead use `MODEL_DIR=./models`, but an absolute path on the model NVMe is recommended.

Generate an API key:

```bash
printf 'sk-%s\n' "$(openssl rand -base64 48 | tr -d '\n')"
```

Put it into `AI_API_KEY`, then:

```bash
chmod 600 .env
./scripts/preflight
```

`AI_BIND=127.0.0.1` is secure for same-host access. Change it to the Bosgame's LAN IP only if Open WebUI runs elsewhere. Do not use `0.0.0.0` without a trusted firewall/reverse proxy.

If Open WebUI has a different browser origin, add it under `security.cors.allowedOrigins` in `config/llama-swap.yaml`.

## 3. Download the enabled model set

Install the current Hugging Face CLI:

```bash
python3 -m pip install --user -U huggingface_hub
export PATH="$HOME/.local/bin:$PATH"
```

Download roughly 190 GB:

```bash
./scripts/download-models
```

Downloads are written to the `MODEL_DIR` configured in `.env`. Or download only the models you need by following `registry/models.yaml`. Missing weights do not prevent the gateway from starting, but selecting that model will fail clearly.

## 4. Validate and start

```bash
./scripts/validate
./scripts/start
```

The canonical llama-swap template is `templates/llama-swap.yaml`; generate the rendered file with `./scripts/generate-config`. The generator reads `templates/runtime-policy.yaml` and refuses obsolete flags. `./scripts/generate-config --check`, `./scripts/validate`, and `./scripts/start` all fail if the rendered config is stale or violates policy.

The custom image adds `admit-run`, runtime flag validation, and small diagnostic utilities to the official unified Vulkan image. `scripts/start` verifies every llama-server flag against the binary before launching llama-swap.

Current llama.cpp removed `--no-mmap`. The stack leaves its default `--load-mode auto` behavior in place. If a specific Strix Halo build demonstrably requires mmap disabled, use the current equivalent `--load-mode none` after benchmarking it—not the obsolete flag.

Inspect:

```bash
docker compose logs -f gateway
./scripts/status
```

Test discovery:

```bash
./scripts/test-api
```

Test an actual cold load and generation:

```bash
./scripts/test-api --generate
```

The first request can take minutes while weights load.

## 5. Connect existing Open WebUI

Configure an OpenAI-compatible connection:

```text
Base URL: http://127.0.0.1:9292/v1
API key:  value of AI_API_KEY
```

If Open WebUI is in Docker on the same host, use either:

```text
http://host.docker.internal:9292/v1
```

with `host.docker.internal:host-gateway`, or attach its container to `strix-halo-ai` and use:

```text
http://gateway:8080/v1
```

For the shared network:

```bash
docker network connect strix-halo-ai <open-webui-container-name>
```

Open WebUI configures chat, STT, TTS, embedding, and reranking in separate settings even though they share this gateway.

## 6. User-friendly management

Use the wrapper for normal operations:

```bash
./scripts/ai-stack --help
./scripts/ai-stack status
./scripts/ai-stack models
./scripts/ai-stack roster
./scripts/ai-stack config
./scripts/ai-stack test llm/fast
./scripts/ai-stack test-all
./scripts/ai-stack protocol exposed
./scripts/ai-stack protocol openwebui
./scripts/ai-stack protocol full
./scripts/ai-stack unload
./scripts/ai-stack ui
```

Management UI: `http://HOST:9292/ui`. Tests run sequentially and save JSON under `benchmark-results/`. See `docs/OPERATIONS.md` and `docs/TESTING.md`.

## 7. API examples

```bash
set -a; source .env; set +a
BASE="http://${AI_BIND}:${AI_PORT}"
AUTH="Authorization: Bearer ${AI_API_KEY}"
```

Models:

```bash
curl -s -H "$AUTH" "$BASE/v1/models" | jq
```

Chat:

```bash
curl -s -H "$AUTH" -H 'Content-Type: application/json' \
  "$BASE/v1/chat/completions" -d '{
    "model":"llm/fast",
    "messages":[{"role":"user","content":"Explain UMA briefly."}],
    "stream":false
  }' | jq
```

Transcription:

```bash
curl -s -H "$AUTH" "$BASE/v1/audio/transcriptions" \
  -F model=speech/whisper-large-v3-turbo -F file=@recording.wav
```

Speech:

```bash
curl -s -H "$AUTH" -H 'Content-Type: application/json' \
  "$BASE/v1/audio/speech" -d '{
    "model":"speech/kokoro",
    "voice":"siwis-fr",
    "input":"Bonjour depuis le serveur local."
  }' -o output.wav
```

Reranking:

```bash
curl -s -H "$AUTH" -H 'Content-Type: application/json' \
  "$BASE/v1/rerank" -d '{
    "model":"retrieval/reranker",
    "query":"AMD unified memory",
    "documents":["An apple recipe", "A description of shared CPU/GPU RAM"]
  }' | jq
```

## 8. Loading and unloading behavior

- A request's `model` selects the configured process.
- llama-swap starts it on an automatically assigned loopback port.
- Requests wait for `/health` (or the backend's configured readiness route).
- A conflicting heavyweight is terminated first.
- Each model's TTL starts after activity stops.
- Unload everything immediately:

```bash
./scripts/unload
```

Unload one model:

```bash
./scripts/unload llm/fast
```

View running models and memory:

```bash
./scripts/status
```

## 9. Tuning

Start with the supplied contexts. Do not jump to advertised 256K contexts.

For the 122B model, monitor cold-load and generation peaks:

```bash
watch -n1 free -h
watch -n1 'cat /sys/class/drm/card*/device/mem_info_gtt_used'
docker stats
```

If Qwen 122B exceeds the safe envelope:

1. Reduce context to 16K.
2. Keep Q8 KV cache.
3. Unload speech/retrieval first.
4. Only then reduce `--n-gpu-layers` to create a deliberate CPU/GPU split.

Do not rely on swap. A clean capacity failure is preferable to host paging or OOM-killing the control plane.

## 10. Security and limitations

- Pin the floating base image to a tested digest after first validation.
- Models are mounted read-only.
- The API binds to loopback by default and requires a key.
- The media service also binds to loopback by default.
- `admit-run` sees host memory counters read-only.
- The system currently uses process-level inference inside the gateway container. This guarantees reliable teardown without granting Docker-daemon control.
- Python/ROCm multimedia runtimes will later be sibling containers controlled through a restricted launcher—not a raw Docker socket.
