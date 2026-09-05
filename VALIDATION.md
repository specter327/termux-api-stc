# Validation — 3.1.0a2

## Repository consistency

- authoritative version source: `termux_api_stc/_version.py`
- package runtime version: `3.1.0a2`
- setuptools project version: dynamic from `_version.py`
- minimum Python: `>=3.10`
- official command inventory: `57`
- inspected upstream contracts: `19`

## Corrected regression from supplied snapshot

The supplied execution showed:

```text
197 passed
1 failed
```

The failure was only:

```text
test_public_surface.py::test_version
expected 3.0.0a2
runtime  3.1.0a1
```

This repository removes that duplicated stale version assertion and makes
`_version.py` authoritative.

## Validation performed while building this replacement

PASS:

- `test_public_surface.py`: 2 tests
- `test_evolution_3_1.py`: 7 tests
- `test_notification_channel.py`: 10 tests
- `test_versioning.py`: 3 tests
- Python compilation for package/scripts/tests
- shell syntax for `tests/run-tests.sh`
- shell syntax for `tests/run-device-tests.sh`
- `scripts/verification.py` execution
- wheel build
- clean wheel installation outside source checkout
- runtime/distribution version parity after wheel install
- `notification_channel` import from installed wheel
- official command count from installed wheel: 57
- inspected contract count from installed wheel: 19

## Build-environment note

The full monolithic pytest execution in the artifact build runtime experienced
an external/intermittent slowdown in the pre-existing `test_new_contracts.py`
suite. The supplied user's Linux Mint evidence already showed all of those
pre-existing contract tests passing before the stale version assertion.

Do not treat this build-runtime timeout as Termux conformance evidence. The
authoritative next validation is:

```bash
python -m pip uninstall -y termux-api-stc
python -m pip install -e '.[test]'
./tests/run-tests.sh
./tests/run-device-tests.sh readonly
```

## Device conformance policy

`tests/run-device-tests.sh readonly` compares the native Termux command path
against STC. Optional-payload commands such as infrared are compared raw-first;
JSON is only required when the native command actually emitted a payload.
