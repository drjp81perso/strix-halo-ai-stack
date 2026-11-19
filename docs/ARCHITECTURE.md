# Architecture

## Control plane

```text
Open WebUI -> llama-swap gateway :9292 -> selected loopback inference process
                                  -> /v1/models catalog
                                  -> TTL/swap lifecycle
                                  -> admission guard
media URLs <- Caddy :9293 <- outputs/
```

`gateway` uses `ghcr.io/mostlygeek/llama-swap:unified-vulkan`, which includes llama-server, whisper-server, audiocpp_server, and sd-server. The bundle currently enables only artifact sets whose paths and server contracts are explicit and verifiable.

## Why process-level backends first

The bundled C/C++ servers run as llama-swap child processes in one container. This provides:

- direct Vulkan access through `/dev/dri`;
- model-specific start/stop;
- automatic dynamic ports;
- deterministic SIGTERM-based memory reclamation;
- no root-equivalent Docker socket;
- one OpenAI-compatible public endpoint.

Python ROCm workloads require incompatible environments and therefore belong in isolated sibling containers. They are a second execution plane, staged separately.

## Memory model

The 128 GB physical memory pool is authoritative. GTT/GPU mapping does not create extra capacity.

```text
physical AI usage <= approximately 104-108 GB
normal mapped GPU target <= approximately 90 GB
host protection floor >= 20 GB MemAvailable at admission
absolute GPU-mappable platform ceiling ~= 96 GB
```

The guard checks current conditions only. It does not predict an engine's eventual allocation. Exclusive routing and measured model choices provide the other half of the safety policy.

## Routing groups

- `heavyweight-exclusive`: one chat/coder/vision model.
- `retrieval-exclusive`: one embedding or reranker process; may coexist with a normal heavyweight.
- `speech-light`: one STT or TTS process; may coexist with normal workloads.

Before the 122B model or high-transient visual workloads, manually unload all optional processes. Future capacity metadata should use measured peaks rather than estimates.

## Ports

| Port | Purpose | Default binding |
|---:|---|---|
| 9292 | llama-swap API/UI | 127.0.0.1 |
| 9293 | generated media | 127.0.0.1 |
| dynamic 5800+ | inference processes | container loopback only |

## Failure behavior

- Missing model: child exits; llama-swap returns startup failure.
- Admission failure: `admit-run` exits 75 with memory details.
- Health timeout: request fails without leaving an untracked backend.
- Inactive model: TTL triggers graceful termination, then force termination after timeout.
- Gateway restart: all child inference processes die with the container.
