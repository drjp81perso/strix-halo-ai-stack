# Review LLM upgrade results

The upgrade stores transaction files in:

```text
upgrade-results/YYYYMMDD-HHMMSS/
```

The semantic test runner stores complete JSON responses in:

```text
benchmark-results/candidate__MODEL-YYYYMMDD-HHMMSS.json
```

## Qualification summary

```bash
TX="upgrade-results/YYYYMMDD-HHMMSS"
jq . "$TX/qualification.json"
```

Show the model, test, result, speed, duration, and log:

```bash
jq -r '
  to_entries[] as $model
  | $model.value.results[]
  | [
      $model.key,
      .test,
      .passed,
      (.generation_tps // "not recorded"),
      .seconds,
      .log
    ]
  | @tsv
' "$TX/qualification.json" |
column -t -s $'\t'
```

## Failed semantic test

Open the test log:

```bash
less "$TX/candidate__qwen38-27b-q5--llm__coder.log"
```

Find the newest raw response:

```bash
RESULT=$(
  find benchmark-results \
    -name 'candidate__qwen38-27b-q5-*.json' \
    -printf '%T@ %p\n' \
  | sort -n \
  | tail -1 \
  | cut -d' ' -f2-
)

echo "$RESULT"
```

Show the explicit test error:

```bash
jq '{
  model,
  spec_id,
  passed,
  error,
  wall_seconds,
  status
}' "$RESULT"
```

Show the complete model answer:

```bash
jq -r '
  .response.choices[0].message.content
  // .response
' "$RESULT"
```

Show generation performance:

```bash
jq '{
  prompt_tps: .response.timings.prompt_per_second,
  generation_tps: .response.timings.predicted_per_second,
  prompt_tokens: .response.usage.prompt_tokens,
  completion_tokens: .response.usage.completion_tokens,
  finish_reason: .response.choices[0].finish_reason
}' "$RESULT"
```

## Coding-test requirements

The coding test requires the answer to:

- Contain one fenced Python block
- Contain exactly 3 literal `assert` statements
- Execute without an exception
- Define a callable `merge_intervals`
- Return `[(1, 7)]` for the independent unsorted-overlap test
- Keep the input list unchanged

A failure to include exactly 3 assertions is an instruction-following failure. It does not necessarily mean that the function algorithm is incorrect.

## New diagnostic behavior

The runner now saves the raw response before semantic validation. It also raises a specific error, for example:

```text
RuntimeError: python-code expected exactly 3 assert statements, found 2
```

or:

```text
RuntimeError: merge_intervals returned [(1, 6), (7, 7)]; expected [(1, 7)]
```

This replaces an unqualified `AssertionError`.

## Rerun one candidate test

After you synchronize the updated test runner to the deployment directory:

```bash
set -a
source .env
set +a

python3 tests/run.py \
  candidate/qwen38-27b-q5 \
  --spec-id llm/coder \
  --base "http://127.0.0.1:${AI_PORT:-9292}" \
  --key "$AI_API_KEY"
```

The command saves a JSON result even when semantic validation fails.
