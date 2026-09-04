# Real Termux device conformance

These tests are intentionally separate from portable unit tests.

## Read-only campaign

```bash
./tests/run-device-tests.sh readonly
```

This executes real `termux-*` commands through the Android/Termux:API stack.
It includes native CLI vs STC comparisons for stable JSON-producing commands.

## Guarded side-effect campaign

```bash
TERMUX_API_STC_ENABLE_SIDE_EFFECTS=1 ./tests/run-device-tests.sh side-effects
```

This may show toasts, vibrate, use clipboard, capture a camera photo, or invoke
interactive Android UI depending on available hardware/permissions.

SMS transmission requires an additional explicit opt-in:

```bash
export TERMUX_API_STC_ENABLE_SIDE_EFFECTS=1
export TERMUX_API_STC_ENABLE_COMMUNICATION_SIDE_EFFECTS=1
export TERMUX_API_STC_SMS_RECIPIENT='+52...'
./tests/run-device-tests.sh side-effects
```

Every campaign writes evidence under `tests/results/` and generates
`SHA256SUMS`.
