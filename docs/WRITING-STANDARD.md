# Technical writing standard

This project uses simplified technical English. The rules are aligned with the principles of ASD-STE100, but this project does not claim formal ASD-STE100 certification.

## Purpose

Use these rules for:

- README files
- User procedures
- Configuration instructions
- Test descriptions
- Error messages
- Issue templates
- Release notes

Do not change commands, file names, model IDs, API paths, or code to make them match normal English.

## Sentence rules

1. Use one instruction in each numbered step.
2. Use the active voice.
3. Use the imperative form for instructions.
4. Keep sentences short. Use a target of 20 words or fewer.
5. Put the condition before the action when the condition is important.
6. Do not omit articles when they make the sentence clearer.
7. Do not use contractions.
8. Do not use Latin abbreviations such as `e.g.` or `i.e.`. Use `for example` or `that is`.
9. Do not use informal phrases, idioms, or humor in procedures.
10. Use parallel grammar in lists and tables.

## Word rules

Use one approved term for one meaning.

| Use | Do not use |
|---|---|
| start | spin up, fire up |
| stop | kill, tear down, shut off |
| model file | weight blob, binary blob |
| candidate model | challenger, contender |
| active model | live model, production model, enabled model when the configuration meaning is not intended |
| host memory | RAM pool, system pool |
| device memory | VRAM when the memory is not discrete VRAM |
| remove | clean up, get rid of |
| move to quarantine | prune, delete, purge when the file is not deleted |
| permanently delete | purge |
| check | sanity-check, eyeball |
| error | issue, problem when an exact error condition exists |

`prune` is permitted only as a command name. In explanatory text, state whether the command lists, quarantines, or permanently deletes files.

## Procedure format

Use this order:

1. State the purpose.
2. State prerequisites and risks.
3. Give commands in numbered steps.
4. State the expected result after each important command.
5. Give rollback instructions when the action changes data.
6. Give troubleshooting information after the normal procedure.

Example:

```markdown
1. Load the environment file.

   ```bash
   set -a
   source .env
   set +a
   ```

2. Check the API.

   ```bash
   curl -fsS "$BASE/health"
   ```

   Expected result:

   ```text
   OK
   ```
```

## Warning format

Use these labels consistently:

- **Warning:** There is a risk of injury, security exposure, data loss, or service loss.
- **Caution:** There is a risk of configuration damage, failed operation, or resource exhaustion.
- **Note:** The information helps the user but does not describe a risk.

Put the warning before the related action.

## Numbers and units

- Use a space between a number and its unit: `16 GiB`, `8 tok/s`, `30 seconds`.
- Use `GiB` for values calculated with powers of 1024.
- Use `GB` only when a source uses decimal units or when you quote a product name.
- State whether a performance value is measured or estimated.
- Use numerals for technical quantities.
- Use an en dash for ranges: `8–12 GiB`.

## Commands and variables

- Put commands in fenced code blocks.
- Put file names, variables, model IDs, and API paths in backticks.
- Do not put prompts or placeholder secrets in normal prose when a code block is clearer.
- Use uppercase placeholders: `AI_HOST`, `MODEL_ID`, `API_KEY`.
- Do not show real credentials in examples.

## Model status terms

Use these project terms:

| Term | Meaning |
|---|---|
| active | The model is in the generated llama-swap configuration and has an executable test. |
| balanced | The candidate has a favorable license, runtime path, and expected utility. |
| experimental | The candidate has material runtime, memory, quality, or license uncertainty. |
| staged | The candidate needs an adapter, workflow, or complete artifact manifest. |
| promoted | The candidate passed its required tests and became active. |
| retired | The model is no longer active. Its files can remain in quarantine for rollback. |

## Tool recommendations

Describe `whichllm` and FreeLLMArena as advisory tools. Do not state that their estimates are local benchmark results.

Approved statement:

> Use `whichllm` and FreeLLMArena to make a candidate list. Use the local test protocol to approve a model.

## Review checklist

Before you merge documentation, check these items:

- The first paragraph states the purpose.
- Every procedure has prerequisites.
- Every destructive operation has a warning and a dry-run step.
- Commands use placeholders and do not contain secrets.
- Terms match this document.
- Links use descriptive text.
- Estimated and measured values are identified.
- Long paragraphs are divided into lists or short sections.
- The document links to the source of truth instead of copying volatile data when possible.
