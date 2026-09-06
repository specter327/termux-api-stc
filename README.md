<div align="center">

# TermuxAPI-stc

### A strict Python interface to the official Termux:API command layer.

**Source-backed contracts · Explicit execution · Async support · Real-device conformance**

```text
Python  →  TermuxAPI-stc  →  official termux-* CLI  →  Termux:API  →  Android
```

`pip install termux-api-stc`

**Current release:** `3.1.0a5` · **Python:** `3.10+` · **License:** `MIT`

</div>

---

## Android capabilities, without making the CLI your application architecture

Termux:API provides an unusually useful bridge between the Termux environment and Android:

* battery information;
* cameras;
* location;
* sensors;
* SMS;
* telephony;
* microphone;
* notifications;
* clipboard;
* storage;
* Wi-Fi;
* audio;
* and other device capabilities.

Its public integration boundary is largely a collection of executable commands:

```bash
termux-battery-status
termux-camera-photo
termux-location
termux-sensor
termux-sms-list
termux-volume
```

Those commands work well interactively.

A Python application, however, needs more than command strings.

It needs a predictable boundary for:

```text
arguments
stdin / stdout / stderr
return codes
timeouts
process lifetime
JSON parsing
empty responses
async execution
streams
missing commands
hardware absence
permissions
semantic failures
```

**TermuxAPI-stc provides that boundary.**

---

# At a glance

|                                  | TermuxAPI-stc                                                  |
| -------------------------------- | -------------------------------------------------------------- |
| **Purpose**                      | Consume the official Termux:API CLI from Python                |
| **Abstraction**                  | Strict execution layer + source-backed higher-level interfaces |
| **Official command baseline**    | 57 commands                                                    |
| **Inspected upstream contracts** | 19                                                             |
| **Execution**                    | Sync, async and streaming                                      |
| **Parsing**                      | Bytes, strict UTF-8 text, JSON, optional JSON                  |
| **Shell execution**              | No                                                             |
| **Environment inspection**       | Yes                                                            |
| **Capability observation**       | Conservative / evidence-oriented                               |
| **Portable qualification**       | 227 tests                                                      |
| **Real Android qualification**   | Yes                                                            |
| **Python**                       | 3.10+                                                          |
| **License**                      | MIT                                                            |

---

# Design

TermuxAPI-stc is deliberately positioned between an application and the official command interface.

```text
┌─────────────────────────────────────────────┐
│              Python application             │
│                                             │
│  automation · services · agents · tooling   │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│                TermuxAPI-stc                │
│                                             │
│  contracts · execution · parsing · async    │
│  streams · errors · environment evidence    │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│          official termux-* commands         │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│                  Termux:API                 │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│                    Android                  │
└─────────────────────────────────────────────┘
```

The library does not replace any layer below it.

It gives Python software a controlled interface to them.

---

# Installation

```bash
pip install termux-api-stc
```

Current alpha:

```bash
pip install termux-api-stc==3.1.0a5
```

For real Android operations you also need a functioning Termux environment with the official Termux:API components installed.

---

# Start with the high-level API

## Battery

```python
from termux_api_stc import battery

status = battery.status()

print(status)
```

Underlying official command:

```text
termux-battery-status
```

---

## Camera

```python
from termux_api_stc import camera

print(camera.info())

path = camera.photo(
    "/data/data/com.termux/files/home/photo.jpg",
    camera_id=0,
)

print(path)
```

TermuxAPI-stc handles the command boundary.

Android still determines whether:

* a camera exists;
* access is permitted;
* the requested camera ID is valid;
* the operation can actually complete.

---

## Location

```python
from termux_api_stc import location

position = location.get(
    provider="gps",
    request="once",
)

print(position)
```

Inspected provider values:

```text
gps
network
passive
```

Bounded request modes exposed by the high-level API include:

```text
once
last
```

---

## Continuous location updates

Continuous upstream behavior remains continuous at the Python boundary:

```python
from termux_api_stc import location

for update in location.stream_updates(provider="gps"):
    print(update)
```

TermuxAPI-stc does not silently convert an upstream stream into polling.

---

# Async where process lifecycle matters

```python
import asyncio

from termux_api_stc import battery


async def main():
    status = await battery.status_async()
    print(status)


asyncio.run(main())
```

Async support uses asynchronous subprocess management.

It is not implemented by simply hiding synchronous execution behind a convenience function.

---

# Need the official command directly?

Use the raw facade.

```python
from termux_api_stc import TermuxAPI

api = TermuxAPI()

result = api["termux-battery-status"].json()

print(result)
```

This gives access to the complete pinned official command inventory even where no specialized wrapper has been defined.

Unknown commands are rejected:

```python
api["not-an-official-termux-command"]
# KeyError
```

That restriction is intentional.

The raw facade represents a known official baseline, not an arbitrary command executor.

---

# Two surfaces, one boundary

TermuxAPI-stc intentionally provides two different levels of access.

```text
                    TermuxAPI-stc
                         │
            ┌────────────┴────────────┐
            │                         │
            ▼                         ▼
   High-level wrappers          Raw command facade
            │                         │
  inspected semantics           official inventory
  validated arguments             57 commands
  parsed responses                   │
            │                         │
            └────────────┬────────────┘
                         │
                         ▼
                 Executor / Command
                         │
                         ▼
                official termux-* CLI
```

This prevents a false tradeoff between:

* exposing the complete official surface; and
* pretending every command already has a fully inspected rich contract.

---

# Explicit execution semantics

At the core:

```text
TermuxAPI
    ↓
Command
    ↓
Executor
    ↓
official executable
```

Commands are executed directly as argument vectors.

```text
shell = false
```

There is no intermediate shell interpretation.

Execution can preserve:

```text
argv
return code
stdout
stderr
duration
```

through `ExecutionResult`.

---

# Parsing is never guessed

A command result can be requested explicitly as:

```python
command.bytes()
command.text()
command.json()
command.json_if_present()
```

### Bytes

```python
payload = command.bytes()
```

Raw stdout.

---

### Text

```python
text = command.text()
```

Strict UTF-8.

Invalid encoding does not get silently repaired into a different result.

---

### JSON

```python
data = command.json()
```

Non-empty malformed JSON raises:

```python
ProtocolError
```

---

### Optional JSON

Some successful commands can legitimately emit nothing.

```python
data = command.json_if_present()
```

Semantics:

```text
empty stdout
    ↓
None

non-empty valid JSON
    ↓
parsed value

non-empty invalid JSON
    ↓
ProtocolError
```

No implicit fallback.

---

# Process success is not capability success

One of the central rules of TermuxAPI-stc is:

```text
command exists
        ≠
command works

command works
        ≠
payload exists

exit code = 0
        ≠
semantic success

official executable exists
        ≠
hardware exists

hardware exists
        ≠
permission granted
```

This matters on Android.

A process can successfully communicate with Termux:API while the returned payload reports, for example, that the requested hardware does not exist.

TermuxAPI-stc does not erase that distinction.

---

# Capability observation

```python
from termux_api_stc import observe_command

observation = observe_command(
    "termux-infrared-frequencies"
)

print(observation.state)
print(observation.evidence)
```

Capability states include:

```text
AVAILABLE
UNAVAILABLE
PERMISSION_REQUIRED
UNSUPPORTED
UNKNOWN
```

The model is deliberately conservative.

For example:

```text
return code = 0
stdout = empty
```

does not automatically prove:

```text
AVAILABLE
```

if useful output is required to establish that conclusion.

---

# Know the environment you are running in

```python
from termux_api_stc import inspect_environment

environment = inspect_environment()

print(environment)
```

`EnvironmentReport` can expose evidence including:

```text
Termux environment
Termux prefix
home directory
Android release
Android API level
manufacturer
device model
ABI
Termux version
termux-api package version
official command availability
```

Environment inspection answers:

> **What is present?**

It does not automatically answer:

> **What will work?**

That distinction is preserved throughout the library.

---

# High-level capability areas

TermuxAPI-stc currently exposes structured interfaces across areas including:

| Capability                | Interface examples                         |
| ------------------------- | ------------------------------------------ |
| **Battery**               | status                                     |
| **Audio**                 | device audio information                   |
| **Volume**                | inspect and modify audio streams           |
| **Brightness**            | display brightness                         |
| **Camera**                | camera information, capture                |
| **Clipboard**             | read, write                                |
| **Contacts**              | list                                       |
| **Calls**                 | call log                                   |
| **Location**              | once, last, updates                        |
| **Sensors**               | list, read, continuous output              |
| **Microphone**            | recording lifecycle                        |
| **Fingerprint**           | authentication request                     |
| **Infrared**              | frequency inspection, transmission         |
| **Notifications**         | create, list, remove                       |
| **Notification channels** | create, remove                             |
| **SMS**                   | list, send                                 |
| **Speech**                | speech-to-text                             |
| **Sharing**               | Android share interface                    |
| **Storage**               | Android storage interaction                |
| **Telephony**             | call, cell and device information          |
| **Toast**                 | transient Android messages                 |
| **Torch**                 | flashlight control                         |
| **TTS**                   | engines, speech                            |
| **Vibration**             | vibration                                  |
| **Wallpaper**             | local file or URL                          |
| **Wi-Fi**                 | connection, scan information, enable state |

This is a library surface description.

It is **not** a claim that every listed Android capability exists or is usable on every device.

---

# Source-backed contracts

A rich wrapper should not exist because an API shape seemed convenient.

For inspected commands, TermuxAPI-stc records upstream evidence.

```python
from termux_api_stc import INSPECTED_CONTRACTS

for command, contract in INSPECTED_CONTRACTS.items():
    print(command, contract)
```

The current 3.1 line distinguishes:

```text
57
official commands in the pinned raw inventory

19
source-identified upstream contracts inspected for richer modeling
```

These are intentionally separate numbers.

```text
official inventory
        ↓
raw accessibility

inspected contract
        ↓
stronger high-level modeling
```

---

# Upstream baseline

The 3.1 line was developed against a pinned official baseline.

```text
Termux:API
v0.53.0

termux/termux-api-package
pinned package tree SHA:
0e3f9222eea7760c76ea6368dadbdf884ab85fbf

official command inventory:
57
```

The pinned identifier is a **package tree SHA**, not a claim that it is the repository commit SHA.

---

# Error model

```python
from termux_api_stc import (
    CommandUnavailableError,
    ExecutionError,
    ExecutionTimeoutError,
    ProtocolError,
)
```

### `CommandUnavailableError`

The executable cannot be found.

---

### `ExecutionError`

The executable ran but returned a non-zero status.

Its execution evidence is preserved.

---

### `ExecutionTimeoutError`

The process exceeded its configured timeout.

---

### `ProtocolError`

The selected parser received a non-empty payload that violated the expected representation.

For example:

```text
expected JSON
received malformed non-empty output
```

---

## Android semantic errors are different

Not every Android failure is an execution failure.

For example:

```text
process
    rc = 0

payload
    ERROR_NO_HARDWARE
```

is fundamentally different from:

```text
process
    rc != 0
```

TermuxAPI-stc preserves that information rather than collapsing both into the same exception.

---

# Validation is layered

A portable Python test and a real Android operation answer different questions.

TermuxAPI-stc treats them separately.

```text
┌──────────────────────┐
│ Portable validation  │
└──────────┬───────────┘
           │
           │ validates
           ▼
 Python contracts
 argv construction
 parsing
 errors
 async lifecycle
 timeout behavior
 subprocess cleanup
 streaming
 registries


┌──────────────────────┐
│ Device conformance   │
└──────────┬───────────┘
           │
           │ validates
           ▼
 STC
   ↓
 official CLI
   ↓
 Termux:API
   ↓
 actual Android device
```

Passing the first does not imply passing the second.

---

# `3.1.0a5` qualification snapshot

The current alpha was validated through multiple layers.

| Qualification                       |             Result |
| ----------------------------------- | -----------------: |
| Portable Python suite               | **227 / 227 PASS** |
| CI Python 3.10                      |           **PASS** |
| CI Python 3.11                      |           **PASS** |
| CI Python 3.12                      |           **PASS** |
| CI Python 3.13                      |           **PASS** |
| CI Python 3.14                      |           **PASS** |
| Android readonly                    |   **19 / 19 PASS** |
| Android safe-effects                |   **10 / 10 PASS** |
| Android qualification               |   **29 / 29 PASS** |
| Installed wheel qualification       |   **29 / 29 PASS** |
| Repeated installed qualification    |   **29 / 29 PASS** |
| Clean PyPI installation             |           **PASS** |
| `pip check` after PyPI installation |           **PASS** |

Real-device qualification was performed against a defined reference environment.

These results are evidence for the tested configuration.

They are **not a universal Android compatibility claim**.

---

# Device tests are risk-separated

Android tests are grouped according to what they actually do.

```text
readonly
safe-effects
qualification
interactive
sensitive
```

This matters because testing:

```text
battery status
```

is operationally different from testing:

```text
camera
microphone
SMS
sharing
biometrics
```

Potentially interactive or externally visible operations are not silently hidden inside ordinary test execution.

---

# Designed for software above it

TermuxAPI-stc deliberately stops at the Android command boundary.

That makes it suitable as a dependency for larger systems.

```text
┌───────────────────────────────────────┐
│            Your application           │
├───────────────────────────────────────┤
│ authorization                         │
│ networking                            │
│ RPC                                   │
│ persistence                           │
│ business logic                        │
│ UI                                    │
├───────────────────────────────────────┤
│             TermuxAPI-stc             │
├───────────────────────────────────────┤
│ argument contracts                    │
│ subprocess execution                  │
│ parsing                               │
│ async lifecycle                       │
│ streams                               │
│ environment observation               │
├───────────────────────────────────────┤
│              Termux:API               │
├───────────────────────────────────────┤
│                Android                │
└───────────────────────────────────────┘
```

TermuxAPI-stc does not absorb concerns that belong to the application consuming it.

---

# What the library intentionally does not do

TermuxAPI-stc is not:

* an Android SDK;
* an Android automation framework;
* a replacement for Termux;
* a replacement for Termux:API;
* a replacement for `termux-api-package`;
* a private Android Intent/Binder implementation;
* a remote administration protocol;
* an authorization system;
* a permission manager;
* a device compatibility database;
* a guarantee that hardware exists;
* a guarantee that Android will grant a permission;
* a normalization layer that fabricates consistent semantics where upstream does not provide them.

Its job is narrower:

> **Provide a strict Python boundary around the official Termux:API command interface.**

---

# Runtime requirements

Actual Android operations generally require:

```text
Android
  ↓
Termux
  ↓
Termux:API companion application
  ↓
termux-api package
  ↓
Python 3.10+
  ↓
TermuxAPI-stc
```

Specific operations can additionally depend on:

```text
Android API level
permissions
hardware
manufacturer behavior
user interaction
current device state
```

---

# Development

Install the project with test dependencies:

```bash
python -m pip install -e '.[test]'
```

Run the portable suite:

```bash
./tests/run-tests.sh
```

Real Termux environment:

```bash
./tests/run-device-tests.sh readonly

./tests/run-device-tests.sh safe-effects

./tests/run-device-tests.sh qualification
```

Interactive and sensitive campaigns remain separate by design.

---

# Validation documentation

For deeper technical detail:

```text
PRE_RELEASE.md
VALIDATION.md
EVOLUTION.md
specification.md
docs/upstream-contracts.md
tests/device/README.md
```

These documents describe the qualification model, upstream evidence and evolution of the 3.x contract surface.

---

# Package identity

| Context                  | Name             |
| ------------------------ | ---------------- |
| **Project presentation** | `TermuxAPI-stc`  |
| **PyPI distribution**    | `termux-api-stc` |
| **Python import**        | `termux_api_stc` |
| **Current version**      | `3.1.0a5`        |

Install:

```bash
pip install termux-api-stc
```

Import:

```python
import termux_api_stc
```

---

# Release status

```text
3.1.0a5
ALPHA
```

The alpha label is deliberate.

The release has substantial automated and real-device qualification, but the richer source-backed API surface is still evolving.

A qualified reference device does not justify claiming universal Android behavior.

---

# Philosophy

TermuxAPI-stc follows a simple rule:

```text
NO SPECIFICATION
        ↓
NO IMPLEMENTATION

NO EVIDENCE
        ↓
NO COMPATIBILITY CLAIM

NO UPSTREAM CONTRACT
        ↓
NO PUBLIC HIGH-LEVEL API
```

When the official command interface provides a contract, the library can model it.

When runtime observation provides evidence, the library can report it.

When neither exists, the library should not invent certainty.

---

<div align="center">

## TermuxAPI-stc

**Python above. Android below. A strict boundary in between.**

```bash
pip install termux-api-stc
```

MIT Licensed · Python 3.10+

</div>
