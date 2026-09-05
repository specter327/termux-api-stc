# termux-api-stc — Baseline Specification

## 1. Normative upstream

The 3.x line is rebuilt against official Termux sources.

Priority:

1. `termux/termux-api-package` command source.
2. `termux/termux-api` Android companion implementation.
3. Official Termux/F-Droid release metadata.
4. Behavior observed on the pinned reference device/environment.

Pinned package tree:

```text
0e3f9222eea7760c76ea6368dadbdf884ab85fbf
```

Termux:API application baseline:

```text
v0.53.0
```

The package baseline exposes 57 command scripts. The exact inventory is encoded
in `termux_api_stc.official.OFFICIAL_COMMANDS`.

## 2. Execution boundary

`termux-api-stc` invokes the installed official `termux-*` executable. It does
not call private Android intents directly and never uses a shell for Python
subprocess execution.

Execution preserves:

- argv;
- stdin bytes;
- stdout bytes;
- stderr bytes;
- exit code;
- execution duration.

A non-zero command exit raises `ExecutionError` while preserving captured
stdout/stderr and return code.

## 3. Parsing

Parsing is explicit:

- `.bytes()` preserves stdout bytes;
- `.text()` performs strict UTF-8 decoding;
- `.json()` performs explicit JSON parsing and raises `ProtocolError` on invalid
  JSON.

The library does not auto-detect JSON. Raw execution preserves empty stdout as
`b""`. Callers that explicitly choose `.json_if_present()` receive `None` only
for a successful empty payload; `.json()` remains strict.

## 4. Command surface

Every command in the pinned baseline is accessible through:

```python
TermuxAPI()[binary]
```

Unknown binaries outside the pinned official inventory are rejected by the
facade.

Rich wrappers are only added after inspection of the corresponding upstream
script. `termux_api_stc.contracts.INSPECTED_CONTRACTS` records the inspected
source path and source SHA.

## 5. 3.1.0a5 inspected expansion

The current expansion adds source-backed wrappers for:

- brightness;
- call log;
- contacts;
- infrared frequencies/transmission;
- sensors;
- SMS listing/sending;
- toast;
- speech-to-text;
- storage picker;
- Android sharing;
- wallpaper;
- microphone recording;
- fingerprint authentication.

See `docs/upstream-contracts.md` for exact source identities.

## 6. Testing levels

### Unit / contract

Portable and runnable on normal Linux. These validate Python behavior, argv
construction, parsing, errors, sync/async behavior and subprocess lifecycle by
using controlled fake commands.

They do **not** prove Android behavior.

### Device / conformance

Run only inside real Termux. These execute the official `termux-*` commands and
exercise the Termux -> Termux:API -> Android path.

Read-only campaign:

```bash
./tests/run-device-tests.sh readonly
```

Guarded side-effect campaign:

```bash
TERMUX_API_STC_ENABLE_SIDE_EFFECTS=1 ./tests/run-device-tests.sh side-effects
```

### Evidence

Device campaigns write environment metadata, test output, exit status and
SHA-256 checksums under `tests/results/`.

## 7. Conformance rule

A compatibility claim for an operation requires all applicable layers:

```text
official source
    -> documented contract
    -> portable contract test
    -> real Termux execution
    -> evidence
```

Where observed runtime behavior disagrees with command source/documentation,
the discrepancy must be recorded rather than silently normalized.


## 8. Observation semantics

Command availability and capability availability are separate concepts.

```text
binary present
!= command succeeded
!= payload produced
!= hardware capability demonstrated
```

A successful empty payload is preserved as evidence and does not by itself
justify `UNSUPPORTED` or `UNAVAILABLE`. Capability classification remains
conservative until device evidence supports a stronger claim.
