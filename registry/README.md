# Versioned model registries

These files separate **operational configuration** from a fast-moving model watchlist.

| File | Purpose |
|---|---|
| `models.yaml` | Original concrete artifact/download registry used by the current bundle |
| `models-v2.2026-11-stable.yaml` | Conservative known-good profile |
| `models-v3.2026-11-frontier.yaml` | Recent models with credible fit and plausible AMD runtimes |
| `models-v4.2026-11-lab.yaml` | Speculative/watchlist models, including explicit non-fit entries |

A registry is not automatically a llama-swap configuration. It records model selection, provenance, fit, licensing, maturity, and promotion blockers. Only `config/llama-swap.yaml` controls what `/v1/models` announces.

## Why this separation matters

New model names appear faster than runtime support. A Hugging Face repository does not prove:

- that its tensors are complete;
- that a quantization preserves useful quality;
- that upstream llama.cpp supports the architecture and chat template;
- that a Python repository works on ROCm/gfx1151;
- that weights plus KV/latents/workspaces fit under the 96 GB mapping;
- that licensing permits the intended use;
- that an OpenAI-compatible endpoint exists;
- or that memory returns to baseline after unload.

Therefore `candidate`, `laboratory`, `watch`, and `promoted` have intentionally different meanings.

## Promotion gate

Before moving an entry into `config/llama-swap.yaml`:

1. Verify the official publisher repository and license.
2. Pin exact model revision, filenames, conversion source, and checksums.
3. Confirm architecture support in a pinned engine build.
4. Run a clean-reboot load on the Bosgame.
5. Record cold-load peak `MemAvailable` and GTT usage.
6. Exercise maximum configured context/resolution/duration.
7. Test tools/templates or media workflow correctness.
8. Stop it and verify memory returns to baseline.
9. Test the actual OpenAI route/Open WebUI integration.
10. Only then mark `promoted` and add it to llama-swap.

## Suggested profile use

- Use **stable** when reliability matters.
- Evaluate **frontier** models one role at a time against the stable incumbent.
- Use **lab** as a research backlog; do not batch-download it.

## Updating over time

Create a new dated snapshot instead of silently editing history:

```text
models-v3.2027-01-frontier.yaml
models-v4.2027-01-lab.yaml
```

Record `as_of`, source repository, official release, conversion, license, quant size, runtime status, and the reason it supersedes an incumbent.

Do not choose candidates solely by Hugging Face trending rank. Prefer official cards, reproducible local evaluations, permissive licenses, and demonstrated upstream runtime support.
