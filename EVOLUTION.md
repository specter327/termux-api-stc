# Evolution 3.1.0a4

This repository is a complete replacement snapshot.

## Corrected

- Removed the stale `3.0.0a2` test expectation.
- Removed version duplication between `pyproject.toml` and package runtime.
- Added `termux_api_stc/_version.py` as the authoritative version source.
- `pyproject.toml` now reads the package version dynamically.
- Replaced the truncated `scripts/verification.py`.
- Updated release tooling to read the authoritative version source.
- Hardened portable/device test preflight for `pytest-asyncio`.
- Hardened test campaigns against installed/runtime version mismatch.
- Corrected native infrared conformance to compare raw payload presence before JSON.

## Evolved

- Payload state: `EMPTY` / `NONEMPTY`.
- Conservative capability observations.
- `json_if_present()` sync/async.
- Richer Android/Termux environment report.
- Notification create/list/remove.
- Notification channel create/delete.
- 57-command raw baseline remains available.
- 19 upstream command contracts are now source-identified.

## Target

Version: `3.1.0a4`
Python: `>=3.10`
Termux:API app baseline: `0.53.0`
Pinned `termux-api-package` tree:
`0e3f9222eea7760c76ea6368dadbdf884ab85fbf`

## 3.1.0a4 release-qualification hardening

- Split real-device validation into read-only, safe/reversible, interactive, and sensitive risk tiers.
- Added 3 real Android async conformance tests.
- Added 10 safe/reversible side-effect tests with restoration or temporary artifacts where possible.
- Added 5 explicit interactive tests and 6 separately gated sensitive/stateful/external tests.
- Added a `qualification` device campaign combining read-only and safe/reversible evidence.
- Device evidence now records exact Git commit/tree state, runtime/distribution versions and Python packages.
- Added Linux CI matrix for Python 3.10 through 3.14 plus clean package metadata/wheel smoke.
- Release publication now requires the local candidate HEAD to match remote `origin/main` using a read-only remote query.
- Fixed wheel installation smoke so imports execute outside the source checkout.
- Dry-run release messages now distinguish simulated tag/push/publication actions.
- Updated project license metadata to the SPDX string form.

## 3.1.0a4 observed-behavior and qualification hardening

- Corrected camera side-effect conformance to the actual public return contract (`str`), while still verifying a real JPEG artifact.
- Replaced clipboard round-trip assumptions with native-CLI/STC differential parity after Android 14 reference-device evidence showed empty native reads after successful native writes.
- Mandatory `readonly`, `safe-effects`, and `qualification` campaigns now reject silent SKIPs.
- `qualification` refuses a dirty Git tree and requires an exact Git commit identity.
- Device evidence now includes JUnit XML and machine-readable test/failure/error/skip counts, all covered by SHA-256 evidence.
- Pytest markers are strict, preventing accidental misspelled/undeclared campaign markers.
- CI now compiles sources, runs `pip check`, validates Python 3.10–3.14, and smoke-installs both wheel and sdist outside the checkout.
- Release tooling now smoke-installs the sdist as well as the wheel before publication.
- Added regression tests for camera return semantics, clipboard stdin semantics, and evidence-count parsing.

The design rule remains: observed upstream behavior may narrow STC claims; STC must not invent stronger guarantees than the official CLI demonstrates on the reference device.
