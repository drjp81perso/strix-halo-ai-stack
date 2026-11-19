# Staged Multimedia Execution Plane

Current speech/audio candidate decision record: [`AUDIO-MODEL-REGISTRY-2026-11-19.md`](AUDIO-MODEL-REGISTRY-2026-11-19.md).

These capabilities remain in `registry/models.yaml` with `enabled: false`. This is intentional: catalog discovery must represent working endpoints, not aspirations.

## Planned additions

| ID | Runtime | Required contract |
|---|---|---|
| `speech/chatterbox-clone` | Dedicated PyTorch/ROCm image | OpenAI `/v1/audio/speech`, `/v1/audio/voices`, protected enrollment API |
| `image/flux2-klein` | stable-diffusion.cpp Vulkan | Verified GGUF/safetensors components and `/v1/images/generations` |
| `image/z-image-turbo` | stable-diffusion.cpp Vulkan | Verified components and generation defaults |
| `video/wan22-5b` | ComfyUI ROCm | Pinned workflow, async job adapter, persistent output URL |
| `music/ace-step-xl` | ACE-Step ROCm | OpenAI chat/responses adapter plus persistent audio output |

## Lifecycle architecture

Do not mount `/var/run/docker.sock` in the public gateway. Add a restricted local launcher with an allowlist such as:

```text
start chatterbox
stop chatterbox
start comfyui-wan22
stop comfyui-wan22
start acestep
stop acestep
```

The launcher owns Docker/Podman access and accepts no arbitrary command, image, volume, or environment input. llama-swap's `cmd` calls that launcher; `cmdStop` stops the allowlisted service.

Each ROCm service needs:

```yaml
devices:
  - /dev/kfd:/dev/kfd
  - /dev/dri:/dev/dri
group_add:
  - video
  - render
ipc: host
shm_size: 8g
```

Pin image digests, model revisions, and workflow JSON. Never use unbounded `latest` deployments for these research stacks.

## Persistent outputs

Adapters must copy finished media to:

```text
outputs/audio/
outputs/image/
outputs/music/
outputs/video/
```

and return a URL from the persistent Caddy service. Outputs must not be served only by an inference container that TTL later destroys.

## Video/music UI behavior

There is no universal OpenAI-compatible local video or music-generation route. Use both:

1. A catalog-visible chat adapter for discoverability.
2. An Open WebUI tool for typed parameters, progress, cancellation, and output rendering.

A video/music chat adapter should return a normal chat-completion object containing a Markdown media link and structured generation metadata. It should not misuse `/v1/audio/speech` for music.

## Voice cloning safety

Reference enrollment is an administrative operation, not ordinary TTS. Require authentication and explicit consent; store the reference audio and derived embeddings as sensitive biometric data. Normal synthesis can expose approved clones as named voices.

## Promotion checklist

A staged entry becomes enabled only after:

- exact artifacts and checksums are pinned;
- the license is recorded;
- AMD ROCm/Vulkan startup succeeds after a clean reboot;
- cold-load peak physical/GTT usage is measured;
- generation peak is measured at maximum supported request settings;
- stop/unload returns memory to baseline;
- API health, cancellation, timeout, and failed-job behavior are tested;
- output persists after backend teardown;
- Open WebUI invocation is tested end-to-end.
