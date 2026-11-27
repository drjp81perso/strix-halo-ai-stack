#!/usr/bin/env python3
"""
Sync-all: Unified reconciliation of registry, template, environment, and physical files.

This script performs a single, atomic reconciliation of all four configuration paths:
1. Registry (registry/models.yaml) - Canonical source of truth
2. Template (templates/llama-swap.yaml) - Runtime configuration template
3. Environment (.env) - Runtime parameters
4. Physical Files (MODEL_DIR/) - Actual model weights on disk

Usage:
    ./scripts/sync-all.py                  # Dry-run (default)
    ./scripts/sync-all.py --apply          # Apply changes
    ./scripts/sync-all.py --apply --sync-models --recreate  # Full sync with restart
"""
from pathlib import Path
import argparse, copy, datetime, json, os, shutil, subprocess, sys, time, yaml, re

ROOT = Path(__file__).resolve().parents[1]
IGNORED = {'.cache', '.locks', '.trash', '.staging', '.gitkeep'}

# Result tracking
results = {
    'registry': {'status': 'pending', 'errors': [], 'warnings': [], 'info': []},
    'template': {'status': 'pending', 'errors': [], 'warnings': [], 'info': []},
    'environment': {'status': 'pending', 'errors': [], 'warnings': [], 'info': []},
    'files': {'status': 'pending', 'errors': [], 'warnings': [], 'info': [], 'orphans': []},
    'config': {'status': 'pending', 'errors': [], 'warnings': [], 'info': []},
    'validation': {'status': 'pending', 'errors': [], 'warnings': [], 'info': []},
}

def log(level, component, message):
    """Log a message with level and component."""
    results[component]['info' if level == 'info' else 'warnings' if level == 'warn' else 'errors'].append(message)
    results[component]['status'] = 'error' if level == 'error' else 'warning' if level == 'warn' else results[component]['status']
    prefix = {'info': '✓', 'warn': '⚠', 'error': '✗'}[level]
    print(f"{prefix} {component.upper()}: {message}")

def load_env(path=None):
    """Load environment variables from a .env file."""
    d = {}
    p = path or ROOT / '.env'
    if p.exists():
        for line in p.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                d[k] = v.strip().strip('"').strip("'")
    return d

def load_registry():
    """Load the model registry."""
    p = ROOT / 'registry' / 'models.yaml'
    if not p.exists():
        raise FileNotFoundError(f"Registry not found: {p}")
    return yaml.safe_load(p.read_text())

def load_template():
    """Load the llama-swap template."""
    p = ROOT / 'templates' / 'llama-swap.yaml'
    if not p.exists():
        raise FileNotFoundError(f"Template not found: {p}")
    return yaml.safe_load(p.read_text())

def root_dir():
    """Get the model root directory."""
    env = load_env()
    return Path(os.environ.get('MODEL_DIR') or env.get('MODEL_DIR') or ROOT / 'models').expanduser().resolve()

def rel_local(m):
    """Get the relative directory for a model."""
    p = Path(m.get('local_dir', f"models/{m['id']}"))
    parts = p.parts
    return Path(*parts[1:]) if parts and parts[0] == 'models' else p

def expected_patterns(m):
    """Get expected file patterns for a model."""
    return list(m.get('files', [])) + list(m.get('include', [])) + list(m.get('artifacts', []))

def paths_for(m, base):
    """Get actual file paths for a model."""
    dest = base / rel_local(m)
    out = []
    for pat in expected_patterns(m):
        if isinstance(pat, str) and ('*' in pat or '?' in pat):
            out.extend(x for x in dest.glob(pat) if x.is_file())
        elif isinstance(pat, str):
            p = dest / (Path(pat).name if m.get('flatten') else pat)
            if p.is_file():
                out.append(p)
    return out

def all_payload_files(base):
    """Get all payload files in the model directory."""
    for p in base.rglob('*'):
        if not p.is_file():
            continue
        if any(part in IGNORED for part in p.relative_to(base).parts):
            continue
        if p.name == '.gitkeep':
            continue
        yield p.resolve()

def size(p):
    """Get size of a file or directory."""
    if p.is_file():
        return p.stat().st_size
    return sum(x.stat().st_size for x in p.rglob('*') if x.is_file())

def human(n):
    """Format bytes as human-readable string."""
    for u in ('B', 'KiB', 'MiB', 'GiB', 'TiB'):
        if n < 1024:
            return f'{n:.1f} {u}'
        n /= 1024
    return f'{n:.1f} PiB'

def validate_registry():
    """Validate the registry structure and test coverage."""
    log('info', 'registry', 'Loading registry...')
    registry = load_registry()
    models = registry.get('models', [])
    
    # Check for duplicate IDs
    ids = [m['id'] for m in models]
    if len(ids) != len(set(ids)):
        log('error', 'registry', 'Duplicate model IDs found')
        return False
    
    log('info', 'registry', f'Found {len(models)} models')
    
    # Check test coverage
    try:
        active_tests = yaml.safe_load((ROOT / 'tests' / 'models.yaml').read_text())['tests']
        planned_tests = yaml.safe_load((ROOT / 'tests' / 'planned-models.yaml').read_text())['planned_tests']
    except FileNotFoundError as e:
        log('warn', 'registry', f'Test files not found: {e}')
        return True
    
    active_ids = [m['id'] for m in models if m.get('enabled')]
    candidate_ids = [m['id'] for m in models if not m.get('enabled')]
    
    for mid in active_ids:
        if mid not in active_tests:
            log('error', 'registry', f'Active model missing executable test: {mid}')
            return False
        model = next(m for m in models if m['id'] == mid)
        if model.get('test_status') != 'implemented':
            log('error', 'registry', f'Active model test_status not implemented: {mid}')
            return False
    
    for mid in candidate_ids:
        if mid not in planned_tests:
            log('error', 'registry', f'Candidate missing planned test: {mid}')
            return False
        model = next(m for m in models if m['id'] == mid)
        if model.get('test_status') != 'planned':
            log('error', 'registry', f'Candidate test_status not planned: {mid}')
            return False
    
    log('info', 'registry', f'✓ All active models have executable tests ({len(active_ids)})')
    log('info', 'registry', f'✓ All candidates have planned tests ({len(candidate_ids)})')
    return True

def compare_registry_template():
    """Compare registry enabled models with template entries."""
    log('info', 'template', 'Comparing registry with template...')
    registry = load_registry()
    template = load_template()
    
    enabled_ids = {m['id'] for m in registry['models'] if m.get('enabled')}
    template_ids = set(template.get('models', {}).keys())
    
    # Check for enabled models missing from template
    missing = enabled_ids - template_ids
    if missing:
        log('warn', 'template', f'Enabled models missing from template: {", ".join(sorted(missing))}')
        return False
    
    # Check for template entries without enabled models
    extra = template_ids - enabled_ids
    if extra:
        log('warn', 'template', f'Template entries without enabled models: {", ".join(sorted(extra))}')
        return False
    
    log('info', 'template', f'✓ Template matches registry ({len(enabled_ids)} enabled models)')
    return True

def compare_template_environment():
    """Validate that all template variables exist in environment."""
    log('info', 'environment', 'Validating environment variables...')
    template = load_template()
    env = load_env()
    env_example = load_env(ROOT / '.env.example')
    
    # Collect all ${profile.*} and ${env.*} references
    text = yaml.dump(template)
    profile_vars = set(re.findall(r'\$\{profile\.([A-Z0-9_]+)\}', text))
    env_vars = set(re.findall(r'\$\{env\.([A-Z0-9_]+)\}', text))
    
    # Check profile variables
    missing_profile = []
    for var in profile_vars:
        if var not in env and var not in env_example:
            missing_profile.append(var)
    
    if missing_profile:
        log('warn', 'environment', f'Missing profile variables: {", ".join(sorted(missing_profile))}')
        return False
    
    # Check env variables
    missing_env = []
    for var in env_vars:
        if var not in env and var not in env_example:
            missing_env.append(var)
    
    if missing_env:
        log('error', 'environment', f'Missing required environment variables: {", ".join(sorted(missing_env))}')
        return False
    
    log('info', 'environment', f'✓ All {len(profile_vars)} profile and {len(env_vars)} env variables resolved')
    return True

def compare_registry_files():
    """Check physical files against registry expectations."""
    log('info', 'files', 'Checking physical files...')
    registry = load_registry()
    base = root_dir()
    
    if not base.exists():
        log('warn', 'files', f'Model directory does not exist: {base}')
        return True
    
    enabled_models = [m for m in registry['models'] if m.get('enabled')]
    all_models = registry['models']
    
    # Check enabled models
    missing_files = []
    for m in enabled_models:
        found = paths_for(m, base)
        patterns = expected_patterns(m)
        if not patterns:
            continue
        for pat in patterns:
            text = str(pat)
            if '*' in text or '?' in text:
                if not list((base / rel_local(m)).glob(text)):
                    missing_files.append(f"{m['id']}: {pat}")
            else:
                target = base / rel_local(m) / (Path(text).name if m.get('flatten') else text)
                if not target.is_file():
                    missing_files.append(f"{m['id']}: {pat}")
    
    if missing_files:
        log('error', 'files', f'Missing files for enabled models: {", ".join(missing_files[:5])}')
        if len(missing_files) > 5:
            log('warn', 'files', f'... and {len(missing_files) - 5} more')
        return False
    
    # Check for orphan files
    expected_set = set()
    for m in all_models:
        expected_set.update(paths_for(m, base))
    
    orphans = sorted(set(all_payload_files(base)) - expected_set)
    if orphans:
        total_size = sum(size(p) for p in orphans)
        log('warn', 'files', f'Found {len(orphans)} orphan files ({human(total_size)})')
        results['files']['orphans'] = [str(p.relative_to(base)) for p in orphans]
        if len(orphans) <= 10:
            for o in orphans:
                log('info', 'files', f'  ORPHAN: {o.relative_to(base)}')
        else:
            for o in orphans[:10]:
                log('info', 'files', f'  ORPHAN: {o.relative_to(base)}')
            log('info', 'files', f'  ... and {len(orphans) - 10} more')
    else:
        log('info', 'files', '✓ No orphan files found')
    
    log('info', 'files', f'✓ All enabled model artifacts present')
    return True

def generate_config():
    """Generate the config file from template."""
    log('info', 'config', 'Generating config...')
    try:
        result = subprocess.run(
            ['./scripts/generate-config'],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True
        )
        log('info', 'config', 'Config generated successfully')
        return True
    except subprocess.CalledProcessError as e:
        log('error', 'config', f'Config generation failed: {e.stderr}')
        return False

def validate_config():
    """Run validation checks."""
    log('info', 'validation', 'Running validation...')
    try:
        result = subprocess.run(
            ['./scripts/validate'],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True
        )
        log('info', 'validation', 'Validation passed')
        return True
    except subprocess.CalledProcessError as e:
        log('error', 'validation', f'Validation failed: {e.stderr}')
        return False

def sync_models(track='active'):
    """Sync model files from registry."""
    log('info', 'files', f'Syncing models for track: {track}...')
    try:
        result = subprocess.run(
            ['./scripts/ai-stack', 'model-sync', track],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True
        )
        log('info', 'files', 'Models synced successfully')
        return True
    except subprocess.CalledProcessError as e:
        log('error', 'files', f'Model sync failed: {e.stderr}')
        return False

def quarantine_orphans():
    """Quarantine orphan files."""
    log('info', 'files', 'Quarantining orphan files...')
    try:
        result = subprocess.run(
            ['./scripts/ai-stack', 'model-prune', 'all', '--apply'],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True
        )
        log('info', 'files', 'Orphans quarantined successfully')
        return True
    except subprocess.CalledProcessError as e:
        log('error', 'files', f'Quarantine failed: {e.stderr}')
        return False

def recreate_gateway():
    """Recreate the gateway container."""
    log('info', 'config', 'Recreating gateway container...')
    try:
        result = subprocess.run(
            ['docker', 'compose', 'up', '-d', '--force-recreate', 'gateway'],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True
        )
        log('info', 'config', 'Gateway recreated successfully')
        time.sleep(3)
        return True
    except subprocess.CalledProcessError as e:
        log('error', 'config', f'Gateway recreation failed: {e.stderr}')
        return False

def print_summary(dry_run=True):
    """Print a summary of the sync-all results."""
    print("\n" + "=" * 60)
    print("SYNC-ALL SUMMARY")
    print("=" * 60)
    
    overall_status = 'DRY-RUN' if dry_run else 'APPLIED'
    has_errors = any(r['errors'] for r in results.values())
    has_warnings = any(r['warnings'] for r in results.values())
    
    if has_errors:
        overall_status += ' (ERRORS)'
    elif has_warnings:
        overall_status += ' (WARNINGS)'
    else:
        overall_status += ' (SUCCESS)'
    
    print(f"\nStatus: {overall_status}")
    
    for component, data in results.items():
        if data['info'] or data['warnings'] or data['errors']:
            print(f"\n{component.upper()}:")
            for msg in data['info']:
                print(f"  ✓ {msg}")
            for msg in data['warnings']:
                print(f"  ⚠ {msg}")
            for msg in data['errors']:
                print(f"  ✗ {msg}")
    
    if dry_run:
        print("\n" + "-" * 60)
        print("RECOMMENDED ACTIONS:")
        print("  --apply           Apply changes")
        print("  --sync-models     Also download missing candidate artifacts")
        print("  --quarantine      Also quarantine orphan files")
        print("  --recreate        Also restart the gateway container")
    
    print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description='Unified sync for registry, template, environment, and files')
    parser.add_argument('--apply', action='store_true', help='Apply changes instead of dry-run')
    parser.add_argument('--sync-models', action='store_true', help='Sync model files from registry')
    parser.add_argument('--quarantine', action='store_true', help='Quarantine orphan files')
    parser.add_argument('--recreate', action='store_true', help='Recreate gateway container')
    parser.add_argument('--track', default='active', choices=['active', 'balanced', 'experimental', 'staged', 'all'],
                        help='Track to sync when --sync-models is used')
    parser.add_argument('--output', type=str, help='Output directory for results log')
    
    args = parser.parse_args()
    
    # Create output directory
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    output_dir = Path(args.output) if args.output else ROOT / 'benchmark-results' / f"sync-all-{stamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\nSYNC-ALL {'DRY-RUN' if not args.apply else 'APPLY'}")
    print(f"Timestamp: {stamp}")
    print(f"Output: {output_dir}")
    print("=" * 60)
    
    # Step 1: Validate registry
    if not validate_registry():
        print("\n✗ Registry validation failed. Aborting.")
        print_summary(args.apply)
        return 1
    
    # Step 2: Compare registry with template
    template_ok = compare_registry_template()
    if not template_ok:
        print("\n⚠ Template mismatch detected. Review warnings above.")
        if not args.apply:
            print_summary(True)
            return 0
    
    # Step 3: Compare template with environment
    if not compare_template_environment():
        print("\n✗ Environment validation failed. Aborting.")
        print_summary(args.apply)
        return 1
    
    # Step 4: Compare registry with physical files
    files_ok = compare_registry_files()
    if not files_ok:
        print("\n✗ File validation failed. Aborting.")
        print_summary(args.apply)
        return 1
    
    # Step 5: Generate config
    if not generate_config():
        print("\n✗ Config generation failed. Aborting.")
        print_summary(args.apply)
        return 1
    
    # Step 6: Validate config
    if not validate_config():
        print("\n✗ Config validation failed. Aborting.")
        print_summary(args.apply)
        return 1
    
    # Apply actions if requested
    if args.apply:
        if args.sync_models:
            if not sync_models(args.track):
                print("\n✗ Model sync failed. Aborting.")
                print_summary(True)
                return 1
        
        if args.quarantine and results['files']['orphans']:
            if not quarantine_orphans():
                print("\n✗ Quarantine failed. Aborting.")
                print_summary(True)
                return 1
        
        if args.recreate:
            if not recreate_gateway():
                print("\n✗ Gateway recreation failed. Aborting.")
                print_summary(True)
                return 1
    
    # Save results to output file
    results_file = output_dir / 'results.json'
    results_file.write_text(json.dumps(results, indent=2))
    print(f"\nResults saved to: {results_file}")
    
    print_summary(args.apply)
    return 0

if __name__ == '__main__':
    sys.exit(main())
