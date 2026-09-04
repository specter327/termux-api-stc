# termux-api-stc

`termux-api-stc` is a Python 3 library that consumes the official Termux:API
command interface. The 3.x development line is rebuilt from a pinned upstream
baseline rather than from historical wrapper behavior.

## Baseline

- Termux:API application baseline: `v0.53.0`
- `termux/termux-api-package` pinned tree:
  `0e3f9222eea7760c76ea6368dadbdf884ab85fbf`
- Official command inventory: 57 installed scripts

## Architecture

```text
Python wrapper
    -> Command
        -> Executor
            -> official termux-* executable
                -> Termux:API backend
                    -> Android
```

The subprocess boundary never invokes a shell. `argv`, stdin, stdout, stderr,
return code and duration are preserved by `ExecutionResult`.

## API levels

Every command in the pinned baseline is available through the raw facade:

```python
from termux_api_stc import TermuxAPI
api = TermuxAPI()
result = api["termux-battery-status"].json()
```

Inspected commands additionally receive richer sync/async wrappers. Version
`3.0.0a2` expands this surface with brightness, call log, contacts, infrared,
sensors, SMS, toast, speech-to-text, storage picker, sharing, wallpaper,
microphone recording and fingerprint authentication.

## Portable tests

```bash
./tests/run-tests.sh
```

Portable tests validate Python logic and command contracts with fake binaries;
they do not prove Android behavior.

## Real Termux conformance

```bash
./tests/run-device-tests.sh readonly
```

Guarded side effects:

```bash
TERMUX_API_STC_ENABLE_SIDE_EFFECTS=1 ./tests/run-device-tests.sh side-effects
```

See `tests/device/README.md`.
