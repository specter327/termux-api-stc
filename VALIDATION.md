# Validation — 3.1.0a5 candidate

## Candidate identity

- authoritative version source: `termux_api_stc/_version.py`
- candidate runtime version: `3.1.0a5`
- setuptools project version: dynamic from `_version.py`
- minimum Python: `>=3.10`
- official command inventory: `57`
- inspected upstream contracts: `19`

## Evidence inherited from 3.1.0a2

The immediately preceding code line was validated by the operator on Linux Mint and
on the declared Android/Termux reference device:

- Linux Mint portable suite: `218/218 PASS`.
- Android/Termux portable suite: `218/218 PASS`.
- Android read-only conformance: `16/16 PASS`.
- Reference device: Samsung SM-A045M, Android 14/API 34, aarch64,
  Termux 0.118.3, Python 3.14.6, Termux:API app 0.53.0,
  `termux-api` package 0.59.1-1.

Those results are historical evidence for `3.1.0a2`; they are not silently promoted
into evidence for `3.1.0a5`.

## 3.1.0a5 changes requiring fresh qualification

This candidate hardens release/test tooling and adds device campaigns. It does not
claim device qualification until the exact `3.1.0a5` commit is tested.

Static/build-runtime checks performed while preparing the candidate:

- Python compilation of package/scripts/tests: PASS.
- shell syntax of unit/device runners: PASS.
- changed/new 3.1 public/version/capability tests: `22 PASS`.
- device test collection: `40` tests.
- unit test collection: `227` tests.
- new device suites collect successfully.
- release console `check --dry-run` source/version preflight: PASS with dirty-tree
  override used only in the artifact construction environment.

The artifact-construction runtime showed the same intermittent subprocess slowdown
previously observed when attempting the monolithic legacy unit suite. This is not
counted as candidate conformance evidence. The exact candidate must therefore be
validated on the operator environments below.

## Required before PyPI

On Linux Mint / CI:

```bash
python -m pip install -e '.[test]'
./tests/run-tests.sh
```

On the real Termux reference device:

```bash
python -m pip install -e '.[test]'
./tests/run-tests.sh
./tests/run-device-tests.sh readonly
./tests/run-device-tests.sh safe-effects
./tests/run-device-tests.sh qualification
```

Then run the explicit interactive campaign where hardware/permissions are available:

```bash
./tests/run-device-tests.sh interactive
```

Sensitive/stateful/external actions remain separately gated. See
`tests/device/README.md` and `PRE_RELEASE.md`.

## Release invariants

A real GitHub/PyPI publication must satisfy:

```text
Git tree = clean
HEAD = remote origin/main
release tag target = HEAD
runtime version = distribution version
isolated wheel import path != source checkout
```

## Evidence discovered during 3.1.0a3 qualification

Reference-device testing of `3.1.0a3` produced:

- Android portable: `218/218 PASS`.
- Android read-only + async: `19/19 PASS`.
- Safe/reversible effects: `7/10 PASS` before test corrections.

The three failures did not demonstrate library defects:

1. camera test incorrectly expected `ExecutionResult` although `camera.photo()` contractually returns `str`;
2. clipboard sync round-trip assumed successful set must be immediately readable;
3. clipboard async repeated the same unsupported assumption.

Native differential evidence on the same Android 14 device showed all three official CLI cases returning an empty clipboard payload after successful native writes: argument input, stdin input, and delayed read. `3.1.0a5` therefore tests native/STC parity instead of inventing a stronger clipboard guarantee.

Fresh evidence is required for the exact `3.1.0a5` candidate before PyPI.

## 3.1.0a5 artifact-construction validation

The construction environment collected `227` portable tests. All test cases passed when executed in bounded groups, including all `91` cases in `test_new_contracts.py` split by contract family. The construction environment still exhibits the previously observed slowdown when that legacy file is executed as one monolithic process; that timeout is not promoted to conformance evidence.

Additional checks performed:

- package/scripts/tests compile: PASS;
- shell syntax for both runners: PASS;
- strict pytest markers enabled;
- wheel metadata/version/Requires-Python inspection: PASS;
- sdist content inspection: PASS;
- MIT `LICENSE` present in wheel and sdist: PASS;
- isolated wheel install outside checkout: PASS;
- runtime/distribution version parity from installed wheel: PASS;
- `pip check` in isolated wheel environment: PASS.

The isolated sdist *installation* smoke is implemented in CI/release tooling but could not be executed in the offline artifact-construction container because its fresh venv cannot download build requirements. It remains a mandatory CI/release gate.


## Manual evidence motivating 3.1.0a5

On the preceding `3.1.0a4` reference-device campaign, native differential evidence
showed:

- `termux-fingerprint`: exit 0 with `ERROR_NO_HARDWARE`,
  `ERROR_NO_ENROLLED_FINGERPRINTS`, and `AUTH_RESULT_UNKNOWN`;
- `termux-storage-get`: exit 0 without materializing the selected output file, matching
  STC `storage.get()` behavior;
- `termux-speech-to-text`: exit 0 with empty stdout, matching STC empty text;
- microphone recording: native and STC both materialized non-empty MP4/AAC artifacts;
- infrared frequencies: exit 0 with empty stdout on a device without IR hardware.

Those observations prove that exit code 0 and Python return type alone are insufficient
interactive-conformance criteria. Fresh evidence is required for the exact 3.1.0a5
candidate.
