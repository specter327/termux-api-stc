# Validation — 3.0.0a2

## Portable unit/contract validation

Collected tests:

```text
198 tests
```

Validated groups in the build environment:

```text
61 passed  — new brightness/call-log/contacts/infrared/sensor/SMS contracts
25 passed  — toast/speech/storage/share/wallpaper/microphone/fingerprint contracts
5 passed   — new sync/async parity additions
107 passed — existing core, registry, location, streaming and contract registry
```

Total logical coverage in these non-overlapping groups:

```text
198 PASS
```

## Device suite on non-Termux host

```text
23 skipped
```

Expected: device tests require real Termux.

## Packaging

A wheel was built with `pip wheel --no-build-isolation`, installed into a clean
virtual environment, and imported outside the source checkout.

Verified from the installed wheel:

```text
termux-api-stc version: 3.0.0a2
official commands: 57
inspected contracts: 15
termux_api_stc.core included: yes
new modules included: yes
```

## Required real-device validation

Run in Termux:

```bash
./tests/run-tests.sh
./tests/run-device-tests.sh readonly
```

Then guarded side effects:

```bash
TERMUX_API_STC_ENABLE_SIDE_EFFECTS=1 ./tests/run-device-tests.sh side-effects
```

Do not claim full Android conformance until the device campaigns have completed
and their evidence has been reviewed.
