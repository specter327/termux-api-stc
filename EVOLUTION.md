# Evolution 3.1.0a2

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

Version: `3.1.0a2`
Python: `>=3.10`
Termux:API app baseline: `0.53.0`
Pinned `termux-api-package` tree:
`0e3f9222eea7760c76ea6368dadbdf884ab85fbf`
