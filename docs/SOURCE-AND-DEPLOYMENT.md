# Source and deployment directories

You can keep the Git repository separate from the runtime deployment directory.

Example:

```text
/home/user/src/strix-halo-ai-stack/        Source repository
/media/pool2p/dockermount108/strix-halo-ai-stack/  Runtime deployment
/nvmihd/dockerdata/models/                 Model library
```

The interactive runtime scripts do not require Git or a `.git` directory.

## Synchronize source files

Run `rsync` from the source directory.

```bash
rsync -av --delete \
  --exclude='.git/' \
  --exclude='.env' \
  --exclude='.env.*' \
  --exclude='models/' \
  --exclude='outputs/' \
  --exclude='state/' \
  --exclude='benchmark-results/' \
  --exclude='upgrade-results/' \
  --exclude='tests/fixtures/*.wav' \
  ./ \
  AI_HOST:/media/pool2p/dockermount108/strix-halo-ai-stack/
```

> **Warning:** Review the source tree before you use `--delete`. A missing source directory can delete the corresponding runtime directory.

Use a dry run first:

```bash
rsync -avn --delete \
  --exclude='.git/' \
  --exclude='.env' \
  --exclude='.env.*' \
  --exclude='models/' \
  --exclude='outputs/' \
  --exclude='state/' \
  --exclude='benchmark-results/' \
  --exclude='upgrade-results/' \
  --exclude='tests/fixtures/*.wav' \
  ./ \
  AI_HOST:/media/pool2p/dockermount108/strix-halo-ai-stack/
```

## Keep machine-local data

Do not overwrite these paths during synchronization:

- `.env`
- `MODEL_DIR`
- `outputs/`
- `state/`
- `benchmark-results/`
- `upgrade-results/`
- Generated WAV fixtures

## Validate the deployment

On the runtime host, run:

```bash
cd /media/pool2p/dockermount108/strix-halo-ai-stack
./scripts/validate
```

If `.env` changed, recreate the gateway:

```bash
docker compose up -d --force-recreate gateway
```

If only the mounted llama-swap template changed, regenerate the configuration first:

```bash
./scripts/generate-config
./scripts/validate
docker compose up -d --force-recreate gateway
```

## Rollback without Git

Interactive scripts create snapshots where a rollback is necessary.

The LLM upgrade script writes snapshots to:

```text
upgrade-results/YYYYMMDD-HHMMSS/backup/
```

The model manager moves unreferenced model files to:

```text
MODEL_DIR/.trash/YYYYMMDD-HHMMSS/
```

Use these 2 locations to restore the runtime configuration and model files.
