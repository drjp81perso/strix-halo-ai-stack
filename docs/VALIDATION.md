# Validation record

Validated in the build workspace on 2026-11-19:

- `compose.yaml`, `config/llama-swap.yaml`, and `registry/models.yaml` parse as YAML.
- `config/audiocpp.json` parses as JSON.
- Every shell script passes `bash -n`.
- `config/llama-swap.yaml` validates against the current upstream `config-schema.json` snapshot.
- Hugging Face repositories and exact enabled filenames were queried through the Hub API.

Not validated in the build workspace because its Docker daemon and AMD GPU are unavailable:

- pulling/building the container image;
- Vulkan device access;
- loading actual model weights;
- measured memory peaks;
- end-to-end Open WebUI behavior.

Run `./scripts/validate`, `./scripts/preflight`, and then `./scripts/test-api --generate` on the Bosgame. Treat initial memory numbers as conservative admission estimates until measured on that host.
