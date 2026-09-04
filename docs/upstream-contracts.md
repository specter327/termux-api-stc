# Inspected upstream command contracts

This document records command scripts inspected directly from the pinned
`termux/termux-api-package` baseline. Source identity is also encoded in
`termux_api_stc.contracts.INSPECTED_CONTRACTS`.

## Newly implemented in 3.0.0a2

| Command | Upstream source | SHA |
|---|---|---|
| `termux-brightness` | `scripts/termux-brightness.in` | `799cef57d2254c1faf6924e3aebdf9a5c4b5e8bc` |
| `termux-call-log` | `scripts/termux-call-log.in` | `0d09d3aa0245643cf6c487d0f85b6fffbb2fde38` |
| `termux-contact-list` | `scripts/termux-contact-list.in` | `90b1024a7acf4fb07d17a8c89f5c72719ab39856` |
| `termux-infrared-frequencies` | `scripts/termux-infrared-frequencies.in` | `f7a494c891a79270a918e0196163efd7c7d1520f` |
| `termux-infrared-transmit` | `scripts/termux-infrared-transmit.in` | `81c912a66391b4bce10b3334e5bbe5b2e1d2f638` |
| `termux-sensor` | `scripts/termux-sensor.in` | `6f29c6057d15db7cfc02b272cb3a0354c0465d94` |
| `termux-sms-list` | `scripts/termux-sms-list.in` | `5409e870a9b682cf5a17436dedfe17037586f58d` |
| `termux-sms-send` | `scripts/termux-sms-send.in` | `8a1bd4cc09514b0eb8dc3686db535a961256b208` |
| `termux-toast` | `scripts/termux-toast.in` | `58e8843dbe9b252dbd39398e849502b3920ba8d4` |
| `termux-speech-to-text` | `scripts/termux-speech-to-text.in` | `4bc7fd0f913c1714f47995ce355be1ae20c2d7cb` |
| `termux-storage-get` | `scripts/termux-storage-get.in` | `86b236edcc3ccacb21e158e25b657bf45c4848e6` |
| `termux-share` | `scripts/termux-share.in` | `90177d55344ab7373f29a65554d6db73821b5300` |
| `termux-wallpaper` | `scripts/termux-wallpaper.in` | `247bc725e0dfb8ba9651f1da76bded85b0288aef` |
| `termux-microphone-record` | `scripts/termux-microphone-record.in` | `2cb7b3999096cce25a5dee75b4c2820a011eebc0` |
| `termux-fingerprint` | `scripts/termux-fingerprint.in` | `ecb40b8e86365e8a0c5bef953c66bf59ab1f40cd` |

## Rule

Where the upstream shell script establishes argument validation, the wrapper
models that contract. Where the script does not establish a stdout schema,
the default high-level operation returns `ExecutionResult`; parsing is exposed
separately only when explicitly selected.
