# Release Notes

All notable changes to this project are documented below. This changelog follows [Semantic Versioning](https://semver.org/) conventions.

## [0.0.1] - 2026-11-19

**Commit:** `9a32d49`

### Initial Release

Initial creation of the Strix Halo local AI stack project.

**Features:**
- Complete project scaffolding and directory structure
- Docker and Docker Compose configuration for containerized deployment
- Base model registry with support for three tiers: stable, frontier, and lab models
- Initial environment configuration templates
- Core CLI scripts for stack management (admit-run, ai-stack, check-models, download-models, generate-config)
- Architecture and operations documentation
- Validation and testing documentation

**Files Added:**
- Project root: `.env.example`, `.gitignore`, `README.md`, `LICENSE`, `Dockerfile`, `compose.yaml`
- Configuration: `config/audiocpp.json`, `config/llama-swap.yaml`
- Registry: `registry/models.yaml`, `registry/models-v2.2026-11-stable.yaml`, `registry/models-v3.2026-11-frontier.yaml`, `registry/models-v4.2026-11-lab.yaml`
- Scripts: Core CLI framework and utilities
- Documentation: Architecture, operations, testing, and validation guides

---

## [0.0.2] - 2026-11-19

**Commit:** `71980d6`

### Content Synchronization

Updated and synchronized all configuration files and documentation across the project.

**Changes:**
- Updated environment examples and Docker configuration
- Refined model registry definitions across all tiers
- Enhanced documentation with operational insights
- Synchronized configuration files with current stack state

---

## [0.0.3] - 2026-11-19

**Commit:** `e185a96`

### Coding Robustness and Hardware Profiles

Added comprehensive testing protocols, hardware profiles, and operational documentation.

**Features:**
- Hardware profile configurations for discrete GPUs (8GB, 12GB, 16GB, 24GB, 48GB) and unified memory systems (32GB, 64GB, 128GB)
- New scripts: `apply-profile` command for hardware-aware configuration
- Automated test protocol documentation for validation workflows

**Documentation Added:**
- `AUTOMATED-TEST-PROTOCOL.md` - Test execution and validation procedures
- `CUSTOMIZING.md` - Customization guidelines
- `EXPOSED-MODEL-TEST.md` - Model exposure testing procedures
- `HARDWARE-PROFILES.md` - Hardware configuration profiles
- `MODEL-ROSTER.md` - Available model specifications
- `OPEN-WEBUI.md` - Open WebUI integration guide
- `REFERENCE-STRIX-HALO.md` - Reference documentation

**Files Modified:**
- Enhanced scripts for robustness and error handling
- Updated environment configuration examples
- Improved testing procedures

---

## [0.0.4] - 2026-11-21

**Commit:** `e075b8e`

### Community Standards and GitHub Configuration

Added community contribution standards, issue templates, and GitHub Actions workflows.

**Features:**
- GitHub Actions static validation workflow for automated testing
- Issue templates for bug reports, documentation, and model candidate submissions
- Pull request templates
- Community contribution guidelines and code of conduct
- Security policy documentation
- Dependabot configuration for automatic dependency updates

**Documentation Added:**
- `CODE_OF_CONDUCT.md` - Community code of conduct
- `CONTRIBUTING.md` - Contribution guidelines
- `SECURITY.md` - Security policy
- `HARDWARE-MODEL-SELECTION-2026-11-21.md` - Model selection guidance
- `MODEL-LIFECYCLE.md` - Model lifecycle management
- `MODEL-SELECTION-TOOLS.md` - Tools for model selection
- `OPEN-WEBUI-PRESETS.md` - WebUI preset configurations
- `WRITING-STANDARD.md` - Documentation writing standards

**GitHub Infrastructure:**
- `.github/workflows/static-validation.yml` - CI/CD workflow
- `.github/dependabot.yml` - Automated dependency updates
- Issue and PR templates for consistent community interactions

---

## [0.0.5] - 2026-11-21

**Commit:** `cce0d9f`

### GitHub Actions Upgrade: actions/checkout v7

Updated GitHub Actions to use latest versions for improved security and compatibility.

**Changes:**
- Bumped `actions/checkout` from v4 to v7 in CI/CD workflows
- Improved GitHub Actions security and performance

---

## [0.0.6] - 2026-11-21

**Commit:** `bea2a44`

### GitHub Actions Upgrade: actions/setup-python v7

Updated Python setup action to latest stable version.

**Changes:**
- Bumped `actions/setup-python` from v5 to v7 in CI/CD workflows
- Enhanced Python environment setup reliability

---

## [0.0.7] - 2026-11-21

**Commit:** `367b3b8`

### Merge: Dependabot PR #1

Merged automated actions/checkout dependency update.

**Changes:**
- Integration of GitHub Actions v7 upgrades from dependabot PR #1

---

## [0.0.8] - 2026-11-21

**Commit:** `7d62832`

### GitHub Actions Upgrade: actions/setup-python v7 (Retry)

Additional update of setup-python action configuration.

**Changes:**
- Refined `actions/setup-python` configuration to v7
- Ensured consistent CI/CD environment across workflows

---

## [0.0.9] - 2026-11-21

**Commit:** `0a37d32`

### Merge: Dependabot PR #2

Merged automated actions/setup-python dependency update.

**Changes:**
- Integration of GitHub Actions setup-python v7 upgrades from dependabot PR #2

---

## [0.0.10] - 2026-11-21

**Commit:** `f1b193b`

### Merge: CI/CD Conflict Resolution

Resolved merge conflicts between dependabot branch and main GitHub Actions workflows.

**Changes:**
- Reconciled `.github/workflows/static-validation.yml` between branches
- Ensured consistent CI/CD configuration

---

## [0.0.11] - 2026-11-21

**Commit:** `3f674cd`

### Bash Script Fixes

Fixed shell script syntax and compatibility issues across CLI tools and tests.

**Changes:**
- Fixed bash syntax errors in all scripts directory tools
- Updated `admit-run`, `ai-stack`, `apply-profile`, `check-docs.py`, `check-models`, `check-runtime-flags`, `download-models`, `generate-config`, `model-manager.py`, `preflight`, `registry-report`, `start`, `status`, `stop`, `test-api`, `test-coverage`, `test-environment`, `test-protocol`, `unload`, and `validate`
- Fixed test suite scripts (`tests/exposed.py`, `tests/openwebui_burst.py`, `tests/run.py`)
- Improved shell script robustness and error handling

---

## [0.0.12] - 2026-11-21

**Commit:** `c8f456e`

### Additional Bash Script Corrections

Further refinement of shell script compatibility and CI/CD integration.

**Changes:**
- Additional corrections to bash script syntax across tools and tests
- Updated `.github/workflows/static-validation.yml` for improved linting
- Enhanced script compatibility and validation procedures
- Refined test execution procedures

---

## [0.0.13] - 2026-11-21

**Commit:** `e81b9b9`

### Restore Script Executable Permissions

Restored executable file permissions on all CLI scripts for proper execution.

**Changes:**
- Fixed executable permissions on all bash scripts in `scripts/` directory
- Restored executable permissions on test scripts
- Ensured scripts are runnable via `./scripts/command` syntax
- All 20+ CLI tools and utilities now have correct permissions

---

## [0.0.14] - 2026-11-21

**Commit:** `1d3f0f9`

### EditorConfig and Git Attributes

Added editor configuration standards and git attributes for consistent formatting.

**Features:**
- `.editorconfig` - Editor configuration for consistent code style across different editors
- `.gitattributes` - Git attributes for proper line ending handling and file classification
- Ensures consistent formatting across team and development environments

---

## [0.0.15] - 2026-11-21

**Commit:** `49c6aed`

### One-Command LLM Upgrade Feature

Introduced simplified LLM model upgrade workflow with new CLI command.

**Features:**
- New script: `scripts/upgrade-target-llms.py` - Automated LLM upgrade orchestration
- Unified upgrade command accessible via `./scripts/ai-stack upgrade`
- Simplified process for upgrading language models in the stack

**Documentation Added:**
- `docs/ONE-COMMAND-LLM-UPGRADE.md` - Complete upgrade workflow and usage guide

**Files Modified:**
- Updated `README.md` with upgrade command documentation

---

## [0.0.16] - 2026-11-21

**Commit:** `001a496`

### Transactional LLM Upgrades with Rollback Support

Enhanced LLM upgrade functionality with git-independent transactional semantics and rollback capabilities.

**Features:**
- Transactional upgrade mechanism for safe, recoverable model updates
- Git-independent deployment workflow for production environments
- Local file snapshots for automatic rollback on upgrade failure
- Explicit semantic diagnostics for failed model responses
- Enhanced test coverage for upgrade procedures

**Documentation Added:**
- `docs/SOURCE-AND-DEPLOYMENT.md` - Source-to-deployment architecture and rsync separation
- `docs/UPGRADE-RESULTS.md` - Upgrade result analysis and performance metrics

**Files Modified:**
- Enhanced `scripts/upgrade-target-llms.py` with transaction management
- Updated upgrade documentation with new capabilities
- Improved test suite for upgrade validation

**Key Changes:**
- Separation of source (registry) and runtime (deployment) model paths
- Local snapshots enable safe rollback without git history modifications
- Qualified deployment workflow for production environments

---

## [0.0.17] - 2026-11-21

**Commit:** `fe6f38c`

### Test Fixes and Stability Improvements

Fixed test execution issues and improved model testing stability.

**Changes:**
- Fixed model manager testing procedures in `scripts/model-manager.py`
- Corrected upgrade test flows in `scripts/upgrade-target-llms.py`
- Updated test model specifications in `tests/models.yaml`
- Enhanced test runner with improved error handling in `tests/run.py`
- Updated upgrade documentation for clarity

---

## [0.0.18] - 2026-11-21

**Commit:** `4917fe9`

### Copilot Recommended Improvements

Applied code quality and configuration improvements recommended by Copilot AI analysis.

**Features:**
- Added `LICENSE` file for explicit software licensing
- New script: `scripts/update-manifest` - Automated manifest validation and updates
- Improved environment configuration examples

**Changes:**
- Enhanced `scripts/test-environment` with better diagnostics
- Improved `scripts/upgrade-target-llms.py` with robustness enhancements
- Updated test runner with improved reliability
- Refined `.env.example` with better documentation
- Updated `README.md` with improved clarity

---

## [0.0.19] - 2026-11-27

**Commit:** `92352d4`

### Configuration Synchronization Foundation

Introduced the foundation for unified configuration management with initial sync-all command infrastructure.

**Features:**
- New script: `scripts/sync-all.py` (498 lines) - Main orchestration for configuration synchronization
- Added `sync-all` command routing in `scripts/ai-stack`
- Initial implementation of four-path configuration reconciliation

**Documentation Added:**
- `docs/SYNC-ALL.md` - Comprehensive sync-all usage and workflow documentation

**Key Capabilities (Foundation):**
- Registry (registry/models.yaml) validation
- Template (templates/llama-swap.yaml) reconciliation
- Environment (.env) variable validation
- Physical file (MODEL_DIR/) detection

---

## [0.0.20] - 2026-11-27

**Commit:** `894f4c4`

### Complete Configuration Synchronization System

Fully implemented unified configuration reconciliation system with comprehensive validation and synchronization.

**Features:**
- Complete `sync-all` command for reconciling all four configuration paths
- Dry-run mode by default (safe inspection without changes)
- Registry structure and test coverage validation
- Template-registry alignment verification for enabled models
- Environment variable reference validation
- Missing model artifacts and orphan file detection
- Automatic `config/llama-swap.yaml` generation and validation
- Optional actions: `--apply`, `--sync-models`, `--quarantine`, `--recreate`
- Timestamped results saved to `benchmark-results/sync-all-*/results.json`

**Documentation Enhancements:**
- Updated all architecture and configuration documentation
- Added `docs/ENVIRONMENT.md` - Complete environment variable reference
- Added `docs/MODEL-RUNTIME-CONFIG.md` - Runtime model configuration guide
- Enhanced existing documentation with sync-all integration guidance

**Use Cases Enabled:**
- Daily health checks before making changes
- Pre-deployment validation to catch configuration drift early
- Adding/promoting new models with full validation
- Recovering from configuration drift scenarios
- Complete synchronized deployment with model downloads and gateway restart

**Files Modified:**
- Updated `.env.example` with comprehensive environment variable documentation
- Enhanced `compose.yaml` with improved service configuration
- Updated `config/llama-swap.yaml` with current schema
- Comprehensive documentation updates across 15+ docs files
- Updated registry with refined model definitions

---

## [0.0.21] - 2026-11-27

**Commit:** `b5ef7ab`

### Baseline Checkpoint

Agent host baseline checkpoint capturing complete project state.

**Changes:**
- Full project snapshot captured at agent host session `575b8aa7-25cf-4cb5-aac8-2e40341e54ac`
- Represents complete validated state of all project components
- All prior features and fixes consolidated in this checkpoint

---

## Summary by Feature Category

### Infrastructure & Deployment
- Docker and Docker Compose configuration
- Hardware profile system for GPU/memory variants
- Transactional upgrade mechanism with rollback support
- Configuration synchronization system (sync-all)

### CLI Tools & Scripts
- 20+ command-line utilities
- Hardware profile application
- Model management and upgrading
- Configuration validation and synchronization
- Testing and validation frameworks

### Documentation
- Architecture and design documentation
- Operations and deployment guides
- API and model registry references
- Hardware selection and configuration guides
- Testing and validation procedures
- Community contribution standards

### Community & Quality
- Code of conduct and contribution guidelines
- Security policy
- Issue and PR templates
- Automated CI/CD validation
- Dependabot integration for dependency management

### Testing & Validation
- Automated test protocols
- Model exposure testing
- Performance benchmarking
- Configuration validation
- Upgrade verification procedures

---

**Latest Release:** v0.0.21 (2026-11-27)
