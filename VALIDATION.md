# Validation — 3.1.0a3 candidate

## Candidate identity

- authoritative version source: `termux_api_stc/_version.py`
- candidate runtime version: `3.1.0a3`
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
into evidence for `3.1.0a3`.

## 3.1.0a3 changes requiring fresh qualification

This candidate hardens release/test tooling and adds device campaigns. It does not
claim device qualification until the exact `3.1.0a3` commit is tested.

Static/build-runtime checks performed while preparing the candidate:

- Python compilation of package/scripts/tests: PASS.
- shell syntax of unit/device runners: PASS.
- changed/new 3.1 public/version/capability tests: `22 PASS`.
- device test collection: `40` tests.
- unit test collection: `218` tests.
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
