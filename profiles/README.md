# Hardware profiles

These files contain **memory-policy starting points**, not model manifests and not performance guarantees. Apply one profile after creating `.env`:

```bash
cat profiles/discrete-24gb.env >> .env
./scripts/preflight
./scripts/generate-config
./scripts/validate
```

If `.env` already has these keys, replace them rather than appending duplicates:

```bash
./scripts/apply-profile profiles/discrete-24gb.env
```

Then choose model artifacts appropriate to the profile using `docs/HARDWARE-PROFILES.md` and update `registry/` plus `templates/llama-swap.yaml`. The checked-in model roster is too large for most profiles below unified 128 GB.
