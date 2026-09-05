# Real Termux device conformance

Device campaigns are risk-tiered. A PyPI qualification must not collapse read-only,
reversible, interactive, and sensitive behavior into one undifferentiated test run.

## 1. Read-only conformance — mandatory

```bash
./tests/run-device-tests.sh readonly
```

Compares native Termux:API behavior with STC and includes real Android async smoke tests.

## 2. Safe/reversible effects — mandatory for release qualification

```bash
./tests/run-device-tests.sh safe-effects
```

Covers temporary or restored effects: clipboard round-trip, camera tempfile,
notification lifecycle, notification-channel lifecycle, reversible volume change,
vibration, toast, TTS, and real async side-effect paths.

`side-effects` is retained as an alias of `safe-effects`.

## 3. Interactive actions — explicit operator campaign

```bash
./tests/run-device-tests.sh interactive
```

May require biometric interaction, speech, Android chooser/file picker, microphone
permission, or other explicit operator interaction.

## 4. Sensitive/stateful/external actions — never automatic

```bash
./tests/run-device-tests.sh sensitive
```

Every sensitive test has an additional per-operation gate where restoration or an
external target is required. Examples:

```bash
export TERMUX_API_STC_BRIGHTNESS_TEST_VALUE=128
export TERMUX_API_STC_BRIGHTNESS_RESTORE_VALUE=auto
export TERMUX_API_STC_TORCH_RESTORE_STATE=false
export TERMUX_API_STC_WIFI_RESTORE_STATE=true
```

External communications require a second opt-in:

```bash
export TERMUX_API_STC_ENABLE_EXTERNAL_COMMUNICATIONS=1
export TERMUX_API_STC_SMS_RECIPIENT='+52...'
export TERMUX_API_STC_CALL_NUMBER='+52...'
```

Infrared transmission is hardware-specific and requires:

```bash
export TERMUX_API_STC_IR_FREQUENCY_HZ=38000
export TERMUX_API_STC_IR_PATTERN='1000,1000'
```

## 5. Non-interactive release qualification

```bash
./tests/run-device-tests.sh qualification
```

This combines read-only + safe-effects. It is the minimum real-device gate before
PyPI publication. Interactive evidence should also be collected on the reference
device where hardware/permissions allow it.

Every campaign writes an evidence directory under `tests/results/` containing the
exact Git commit, source/distribution versions, environment, packages, raw pytest
output, exit code, summary, and SHA-256 manifest.
