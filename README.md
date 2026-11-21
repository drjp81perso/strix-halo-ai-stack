# On-Demand Local AI Stack

Run multiple local AI models behind one authenticated, OpenAI-compatible endpoint. The stack loads a model when a request arrives and unloads it after a period of inactivity.

The reference configuration is for this system:

- AMD Ryzen AI Max+ 395
- Radeon 8060S integrated GPU
- 128 GiB unified memory
- Approximately 96 GiB available to Vulkan
- Ubuntu
- Docker Compose

You can adapt the stack to other discrete-GPU, unified-memory, or CPU-only systems.

> **Note:** This project uses simplified technical English that follows ASD-STE100 principles. The project does not claim formal ASD-STE100 certification. See [Technical writing standard](docs/WRITING-STANDARD.md).

## Main functions

- One `/v1` endpoint for Open WebUI and other OpenAI-compatible clients
- On-demand model start and stop
- Host-memory admission checks
- Automatic device-memory fitting for llama.cpp
- Separate routes for chat, vision, embeddings, reranking, speech-to-text, and text-to-speech
- Functional tests for each model that appears in `/v1/models`
- Registry-based model inventory, download, replacement, quarantine, and purge
- Hardware profiles for common RAM and VRAM sizes

## Active reference models

| Model ID | Function | Engine |
|---|---|---|
| `llm/fast` | Fast chat and background tasks | llama.cpp Vulkan |
| `llm/reasoning` | Strong reasoning | llama.cpp Vulkan |
| `llm/coder` | Coding | llama.cpp Vulkan |
| `llm/vision` | Vision and OCR | llama.cpp Vulkan |
| `retrieval/embedding` | Embeddings | llama.cpp Vulkan |
| `retrieval/reranker` | Reranking | llama.cpp Vulkan |
| `speech/whisper-large-v3-turbo` | Speech-to-text | whisper.cpp Vulkan |
| `speech/kokoro` | Text-to-speech | audio.cpp CPU |

Only active models appear in `/v1/models`. Candidate models remain hidden until they pass their promotion tests.

## Read this first

| Document | Purpose |
|---|---|
| [Quick start](#quick-start) | Install and start the reference stack. |
| [Customization guide](docs/CUSTOMIZING.md) | Calculate memory limits and adapt the stack. |
| [Hardware profiles](docs/HARDWARE-PROFILES.md) | Use example settings for common VRAM and unified-memory sizes. |
| [Reference hardware](docs/REFERENCE-STRIX-HALO.md) | Review settings that are specific to Ryzen AI Max+ 395. |
| [Architecture](docs/ARCHITECTURE.md) | Understand the control plane and the execution plane. |
| [Open WebUI](docs/OPEN-WEBUI.md) | Connect chat, audio, and retrieval functions. |
| [Open WebUI presets](docs/OPEN-WEBUI-PRESETS.md) | Add clear role names without duplicate backend aliases. |
| [Model roster](docs/MODEL-ROSTER.md) | Review active and candidate models. |
| [Model selection tools](docs/MODEL-SELECTION-TOOLS.md) | Use `whichllm` and FreeLLMArena to make a candidate list. |
| [Model lifecycle](docs/MODEL-LIFECYCLE.md) | Download, replace, quarantine, restore, and purge model files. |
| [One-command LLM upgrade](docs/ONE-COMMAND-LLM-UPGRADE.md) | Qualify and promote Qwen3.8-27B Q5 and Gemma 4 31B Q5. |
| [Source and deployment directories](docs/SOURCE-AND-DEPLOYMENT.md) | Synchronize a Git source tree to a Git-free runtime directory. |
| [Automated test protocol](docs/AUTOMATED-TEST-PROTOCOL.md) | Test configuration, models, aliases, and Open WebUI behavior. |
| [Operations](docs/OPERATIONS.md) | Review measured results and troubleshooting information. |

## Quick start

### 1. Install prerequisites

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-v2 python3-pip vulkan-tools jq
sudo usermod -aG docker,video,render "$USER"
```

Log out. Then, log in again.

### 2. Create the environment file

```bash
cp .env.example .env
chmod 600 .env
```

Get the GPU group IDs:

```bash
getent group video
getent group render
```

Set `VIDEO_GID` and `RENDER_GID` in `.env`.

Generate an API key:

```bash
printf 'sk-%s\n' "$(openssl rand -base64 48 | tr -d '\n')"
```

Set the result as `AI_API_KEY` in `.env`.

### 3. Set the model directory

Set an absolute path in `.env`:

```dotenv
MODEL_DIR=/srv/ai-models
```

Create the directory:

```bash
sudo mkdir -p /srv/ai-models
sudo chown "$USER:$USER" /srv/ai-models
```

### 4. Select a hardware profile

The default values match the 128 GiB reference system. For another system, apply a profile:

```bash
./scripts/apply-profile profiles/discrete-24gb.env
```

Other examples are in `profiles/`.

> **Caution:** A hardware profile changes memory limits. It does not change the model roster. Select model files that fit your hardware.

### 5. Run the preflight check

```bash
./scripts/preflight
```

For Vulkan systems, list the device memory that llama.cpp can use:

```bash
docker compose build --pull
docker compose run --rm --entrypoint llama-server gateway --list-devices
```

### 6. Download the active models

Install the Hugging Face CLI:

```bash
python3 -m pip install --user -U huggingface_hub
export PATH="$HOME/.local/bin:$PATH"
```

Download the active model set:

```bash
./scripts/ai-stack model-sync active
```

Review the model inventory:

```bash
./scripts/ai-stack model-status active
```

### 7. Validate and start the stack

```bash
./scripts/validate
./scripts/start
```

Expected health result:

```bash
curl -fsS http://127.0.0.1:9292/health
```

```text
OK
```

### 8. Run the smoke test

```bash
./scripts/ai-stack protocol smoke
```

### 9. Connect Open WebUI

Use this OpenAI-compatible connection:

```text
Base URL: http://AI_HOST:9292/v1
API key:  AI_API_KEY from .env
Provider: Default
```

See [Open WebUI integration](docs/OPEN-WEBUI.md) for audio and retrieval settings.

## Daily commands

```bash
./scripts/ai-stack status
./scripts/ai-stack models
./scripts/ai-stack roster
./scripts/ai-stack model-status all
./scripts/ai-stack logs
./scripts/ai-stack unload
```

Run all functional tests for models in the live catalog:

```bash
./scripts/ai-stack protocol exposed
```

Run the Open WebUI concurrency test:

```bash
./scripts/ai-stack protocol openwebui
```

Run the full acceptance protocol:

```bash
./scripts/ai-stack protocol full
```

## Model selection workflow

Use external tools to make a candidate list. Do not use their estimates as promotion evidence.

Run `whichllm`:

```bash
uvx whichllm@latest
```

For a specified device-memory limit:

```bash
uvx whichllm@latest --vram 96
```

Open [FreeLLMArena Run at Home](https://freellmarena.com/home) to compare category recommendations.

Then, use this project workflow:

1. Add the candidate to `registry/models.yaml`.
2. Add a planned test to `tests/planned-models.yaml`.
3. Download the exact artifacts.
4. Register a temporary endpoint.
5. Measure quality, speed, memory, and unload behavior.
6. Promote the candidate only if all required tests pass.
7. Move old files to quarantine.
8. Purge the quarantine after the rollback period.

See [Model selection tools](docs/MODEL-SELECTION-TOOLS.md) and [Model lifecycle](docs/MODEL-LIFECYCLE.md).

## Model-file safety

List unreferenced files without changing them:

```bash
./scripts/ai-stack model-prune all
```

Move reviewed files to quarantine:

```bash
./scripts/ai-stack model-prune all --apply
```

> **Warning:** Do not use `active --apply` when you want to keep downloaded candidate models. The command will quarantine files that are not in the active track.

Permanently delete old quarantine directories only after the rollback period:

```bash
python3 scripts/model-manager.py purge \
  --older-than-days 14 \
  --apply
```

## Security

- Keep `.env` out of Git.
- Rotate a key if it appears in a log, issue, or chat.
- Bind the API to a trusted interface.
- Use a firewall or a reverse proxy when the service is available outside the host.
- Keep model directories read-only in the inference container.
- Do not mount the Docker socket in the public gateway.
- Review model licenses before you download or promote a model.

## Project status

The text, vision, retrieval, and basic speech functions are active. Image, video, music, and voice-cloning models remain candidates until their runtimes and tests are complete.

See [Model roster](docs/MODEL-ROSTER.md) for the current state.

## Contributing and support

- Read [Contributing](CONTRIBUTING.md) before you open a pull request.
- Use the GitHub issue templates for bugs, model candidates, and documentation changes.
- Read [Security policy](SECURITY.md) before you report a vulnerability or an exposed credential.
- Follow the [Code of conduct](CODE_OF_CONDUCT.md).
