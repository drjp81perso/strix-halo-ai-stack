# Open WebUI role presets

llama-swap aliases are API routing conveniences. Listing aliases in `/v1/models` duplicates entries in Open WebUI, so the reference config now uses:

```yaml
includeAliasesInList: false
```

Aliases remain accepted when a client already knows them; they are simply hidden from discovery. Prefer Open WebUI Workspace model presets for user-friendly names and category-specific prompts.

## Current presets

| Open WebUI display name | Base model ID | Purpose |
|---|---|---|
| Local Fast | `llm/fast` | Everyday chat and background tasks |
| Local Reasoning | `llm/reasoning` | Deliberate reasoning; max tokens 1536+ |
| Local Coder | `llm/coder` | Coding and repository work |
| Local Vision | `llm/vision` | Images, screenshots, OCR |

Configure audio/RAG outside the chat selector:

```text
STT: speech/whisper-large-v3-turbo
TTS: speech/kokoro
Embedding: retrieval/embedding
Reranker: retrieval/reranker where supported
```

## Proposed category presets after candidates pass

| Category | Proposed backend |
|---|---|
| Chat | `llm/gemma4-31b-q5` or incumbent `llm/fast` |
| Coding | `llm/qwen38-27b-q5` |
| Vision | `llm/gemma4-31b-q5` or incumbent `llm/vision` |
| Documents | `llm/gemma4-31b-q5` + retrieval |
| Agents | `llm/qwen38-27b-q5` + tools |
| Search | Fast/agent model + web-search tool; no separate model |
| Image | `image/qwen-image-2.1` |
| Image Edit | `image/qwen-image-2.1` |
| Video | `video/minimax-h3` |
| Image to Video | `video/minimax-h3` |
| Video Edit | `video/minimax-h3` |

Candidates must not be added to Open WebUI until promoted and exposed by the live catalog.
