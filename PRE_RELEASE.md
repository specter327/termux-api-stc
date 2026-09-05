# Pre-release qualification gate

A PyPI publication is allowed only after the following evidence exists for the exact
candidate commit and version.

## Mandatory portable evidence

- Linux unit/contract suite: PASS.
- GitHub Actions Python 3.10, 3.11, 3.12, 3.13 and 3.14: PASS.
- clean sdist + wheel build: PASS.
- `twine check`: PASS.
- isolated wheel import from outside the source checkout: PASS.
- runtime version == distribution version.

## Mandatory reference-device evidence

On the declared Android/Termux reference device:

```bash
./tests/run-tests.sh
./tests/run-device-tests.sh readonly
./tests/run-device-tests.sh safe-effects
./tests/run-device-tests.sh qualification
```

All mandatory campaigns must be PASS and identify the exact candidate Git commit,
version, Termux version, Android/API level, Termux:API package version and Python
runtime.

## Interactive evidence

Run on the reference device where the required hardware and permissions exist:

```bash
./tests/run-device-tests.sh interactive
```

A SKIP is acceptable only when the reason is an explicitly unavailable device
capability or operator interaction that is not part of the declared compatibility
claim. Unexpected failures are release blockers.

## Sensitive evidence

Sensitive/stateful/external tests are never enabled automatically. They require
per-operation restoration/target variables and are not a blanket PyPI requirement.
Any capability advertised as device-validated must have corresponding evidence.

## Git/release invariants

Before publication:

```text
working tree = clean
HEAD = origin/main
release tag target = HEAD
runtime version = distribution version
```

Generated test evidence and build artifacts must not be tracked by Git.
