# Environment handling

The deployment `.env` file is the source for machine-local settings.

Do not run this command in an interactive administration shell:

```bash
set -a
source .env
set +a
```

`set +a` disables automatic export for later assignments. It does not remove variables that `.env` already exported. Exported variables remain in the shell and override Docker Compose `.env` interpolation.

## Run Compose safely

Use the project wrapper:

```bash
./scripts/ai-stack compose config --environment
./scripts/ai-stack compose up -d --force-recreate gateway
./scripts/ai-stack compose logs --since 5m gateway
```

The wrapper removes every variable named in `.env` from its inherited process environment. Docker Compose then reads the deployment `.env` file without stale shell overrides.

The wrapper does not change the parent shell.

## Remove exported project variables

If you previously sourced `.env`, print and evaluate the cleanup commands:

```bash
eval "$(./scripts/ai-stack env-clean)"
```

Confirm that a variable is absent:

```bash
printenv GLOBAL_CONCURRENCY_LIMIT \
  || echo "Shell override is absent"
```

The cleanup command removes all variable names defined in the deployment `.env` file. It does not print secret values.

## Run one command with `.env`

Prefer a project script. Project scripts load `.env` in their child process and cannot modify the interactive parent shell.

For an ad hoc command, use a subshell:

```bash
(
  set -a
  source .env
  set +a
  curl -fsS \
    -H "Authorization: Bearer $AI_API_KEY" \
    "http://127.0.0.1:${AI_PORT:-9292}/v1/models"
)
```

The variables disappear when the subshell exits.

## Verify Compose interpolation

```bash
GLOBAL_CONCURRENCY_LIMIT=4 \
  ./scripts/ai-stack compose \
  config \
  --environment |
grep '^GLOBAL_CONCURRENCY_LIMIT='
```

If `.env` contains `GLOBAL_CONCURRENCY_LIMIT=16`, the result must be:

```text
GLOBAL_CONCURRENCY_LIMIT=16
```

This test proves that the wrapper ignores the deliberately stale shell value.
