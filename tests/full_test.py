#!/usr/bin/env python3
"""
termux-api-stc — full repository/device test
=============================================

Place this file at:

    tests/full_test.py

Run inside Termux from the repository root:

    python tests/full_test.py

Useful modes:

    python tests/full_test.py --safe
    python tests/full_test.py --interactive
    python tests/full_test.py --destructive
    python tests/full_test.py --all

Optional values for the full side-effect suite:

    --phone-number "+521234567890"
    --sms-number "+521234567890"
    --sms-text "termux-api-stc test"
    --share-file "/path/to/file"
    --wallpaper-file "/path/to/image.jpg"
    --download-url "https://example.com/file"
    --open-url "https://example.com"

The default run is SAFE:
- validates package/import structure;
- validates all exported modules;
- validates public callable discovery;
- validates the asynchronous API shape;
- checks every Termux:API binary declared by the package;
- exercises read-only/non-destructive APIs when available;
- checks core execution/error semantics.

Interactive and destructive tests are opt-in because they can:
- open Android dialogs;
- activate camera/microphone/flash/vibration;
- change brightness/volume/wallpaper/Wi-Fi;
- send SMS;
- initiate a phone call;
- create notifications/files/jobs/keystore entries.

This script has no third-party dependency.
"""

from __future__ import annotations

# ==============
# Library import
# ==============
import argparse
import asyncio
import contextlib
import inspect
import json
import os
import shutil
import sys
import tempfile
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Coroutine

# ====================
# Constants definition
# ====================
EXPECTED_VERSION = "2.1.0"

EXPECTED_MODULES = [
    "audio",
    "battery",
    "brightness",
    "call_log",
    "camera",
    "clipboard",
    "contacts",
    "dialog",
    "download",
    "fingerprint",
    "infrared",
    "job_scheduler",
    "keystore",
    "location",
    "media_player",
    "media_scanner",
    "microphone",
    "nfc",
    "notification",
    "opener",
    "saf",
    "sensor",
    "share",
    "sms",
    "speech_to_text",
    "storage",
    "telephony",
    "toast",
    "torch",
    "tts",
    "usb",
    "vibrate",
    "volume",
    "wallpaper",
    "wifi",
]

READ_ONLY_CANDIDATES = {
    "audio": [
        ("info_async", (), {}),
        ("info", (), {}),
    ],
    "battery": [
        ("status_async", (), {}),
        ("status", (), {}),
    ],
    "call_log": [
        ("list_async", (), {}),
        ("list_calls_async", (), {}),
        ("list_calls", (), {}),
        ("list", (), {}),
    ],
    "camera": [
        ("info_async", (), {}),
        ("info", (), {}),
    ],
    "clipboard": [
        ("get_async", (), {}),
        ("get", (), {}),
    ],
    "contacts": [
        ("list_contacts_async", (), {}),
        ("list_contacts", (), {}),
    ],
    "infrared": [
        ("frequencies_async", (), {}),
        ("frequencies", (), {}),
    ],
    "location": [
        ("get_async", (), {"provider": "network", "request": "last"}),
        ("get", (), {"provider": "network", "request": "last"}),
    ],
    "media_player": [
        ("info_async", (), {}),
        ("info", (), {}),
    ],
    "microphone": [
        ("info_async", (), {}),
        ("info", (), {}),
    ],
    "notification": [
        ("list_async", (), {}),
        ("list_notifications_async", (), {}),
        ("list_notifications", (), {}),
        ("list", (), {}),
    ],
    "sensor": [
        ("list_sensors_async", (), {}),
        ("list_sensors", (), {}),
    ],
    "telephony": [
        ("device_info_async", (), {}),
        ("device_info", (), {}),
        ("cell_info_async", (), {}),
        ("cell_info", (), {}),
    ],
    "tts": [
        ("engines_async", (), {}),
        ("engines", (), {}),
    ],
    "usb": [
        ("list_async", (), {}),
        ("list_devices_async", (), {}),
        ("list_devices", (), {}),
        ("list", (), {}),
    ],
    "volume": [
        ("get_async", (), {}),
        ("get", (), {}),
    ],
    "wifi": [
        ("connection_info_async", (), {}),
        ("connection_info", (), {}),
        ("scan_info_async", (), {}),
        ("scan_info", (), {}),
    ],
}

# ==================
# Classes definition
# ==================
@dataclass
class TestResult:
    name: str
    status: str
    detail: str = ""
    duration: float = 0.0


@dataclass
class TestReport:
    results: list[TestResult] = field(default_factory=list)

    def add(
        self,
        name: str,
        status: str,
        detail: str = "",
        duration: float = 0.0,
    ) -> None:
        self.results.append(
            TestResult(
                name=name,
                status=status,
                detail=detail,
                duration=duration,
            )
        )

    @property
    def failed(self) -> int:
        return sum(
            1
            for current in self.results
            if current.status == "FAIL"
        )

    @property
    def passed(self) -> int:
        return sum(
            1
            for current in self.results
            if current.status == "PASS"
        )

    @property
    def skipped(self) -> int:
        return sum(
            1
            for current in self.results
            if current.status == "SKIP"
        )


# ====================
# Utility definitions
# ====================
def color(
    value: str,
    code: str,
) -> str:
    if not sys.stdout.isatty():
        return value

    return f"\033[{code}m{value}\033[0m"


def short(
    value: Any,
    maximum: int = 500,
) -> str:
    try:
        result = json.dumps(
            value,
            ensure_ascii=False,
            default=str,
        )
    except Exception:
        result = repr(value)

    if len(result) > maximum:
        return result[:maximum] + "…"

    return result


def print_result(
    result: TestResult,
) -> None:
    status = {
        "PASS": color("PASS", "32;1"),
        "FAIL": color("FAIL", "31;1"),
        "SKIP": color("SKIP", "33;1"),
        "INFO": color("INFO", "36;1"),
    }.get(
        result.status,
        result.status,
    )

    duration = (
        f" [{result.duration:.3f}s]"
        if result.duration
        else ""
    )

    print(
        f"{status:>4}  {result.name}{duration}"
    )

    if result.detail:
        print(
            "      "
            + result.detail.replace(
                "\n",
                "\n      ",
            )
        )


async def run_case(
    report: TestReport,
    name: str,
    function: Callable[[], Any],
    *,
    skip: str | None = None,
) -> Any:
    if skip is not None:
        result = TestResult(
            name=name,
            status="SKIP",
            detail=skip,
        )
        report.results.append(
            result
        )
        print_result(
            result
        )
        return None

    started = time.monotonic()

    try:
        value = function()

        if inspect.isawaitable(
            value
        ):
            value = await value

        result = TestResult(
            name=name,
            status="PASS",
            detail=short(
                value
            ),
            duration=time.monotonic() - started,
        )

        report.results.append(
            result
        )
        print_result(
            result
        )

        return value

    except Exception as exc:
        result = TestResult(
            name=name,
            status="FAIL",
            detail=(
                f"{type(exc).__name__}: {exc}"
            ),
            duration=time.monotonic() - started,
        )

        report.results.append(
            result
        )
        print_result(
            result
        )

        if os.environ.get(
            "TERMUX_API_STC_TEST_TRACEBACK"
        ):
            traceback.print_exc()

        return None


def find_callable(
    module: Any,
    candidates: list[
        tuple[
            str,
            tuple,
            dict,
        ]
    ],
):
    for name, args, kwargs in candidates:
        function = getattr(
            module,
            name,
            None,
        )

        if callable(
            function
        ):
            return (
                name,
                function,
                args,
                kwargs,
            )

    return None


def public_callables(
    module: Any,
) -> dict[str, Callable]:
    result = {}

    for name, value in inspect.getmembers(
        module
    ):
        if name.startswith(
            "_"
        ):
            continue

        if inspect.isfunction(
            value
        ) and getattr(
            value,
            "__module__",
            None,
        ) == module.__name__:
            result[
                name
            ] = value

    return result


async def call_maybe_async(
    function: Callable,
    *args,
    **kwargs,
):
    value = function(
        *args,
        **kwargs,
    )

    if inspect.isawaitable(
        value
    ):
        return await value

    return value


def require_termux() -> bool:
    return (
        "com.termux"
        in os.environ.get(
            "PREFIX",
            ""
        )
        or "com.termux"
        in os.environ.get(
            "HOME",
            ""
        )
    )



# =============================
# Wrapper dry-run definitions
# =============================
def sample_argument(
    parameter: inspect.Parameter,
    temporary_directory: Path,
):
    """
    Generate conservative values for wrapper validation without executing
    Termux commands. Required arguments that cannot be inferred are reported
    as unresolved rather than silently guessed.
    """
    name = parameter.name.lower()

    exact = {
        "camera_id": "0",
        "provider": "network",
        "request": "last",
        "level": 128,
        "limit": 1,
        "offset": 0,
        "sim_slot": 0,
        "delay_ms": 250,
        "duration_ms": 200,
        "duration": 200,
        "bitrate": 64000,
        "sample_rate": 8000,
        "channels": 1,
        "frequency": 38000,
        "repeat": 1,
        "priority": "default",
        "visibility": "private",
    }

    if name in exact:
        return (
            True,
            exact[
                name
            ],
        )

    if name in {
        "number",
        "phone_number",
        "from_number",
    }:
        return (
            True,
            "+10000000000",
        )

    if name in {
        "numbers",
        "recipients",
    }:
        return (
            True,
            [
                "+10000000000"
            ],
        )

    if name in {
        "sensors",
    }:
        return (
            True,
            [
                "Accelerometer"
            ],
        )

    if name in {
        "text",
        "message",
        "title",
        "content",
        "label",
        "name",
        "tag",
    }:
        return (
            True,
            "termux-api-stc-test",
        )

    if name in {
        "url",
        "uri",
    }:
        return (
            True,
            "https://example.com/",
        )

    if (
        "output" in name
        or name in {
            "file",
            "filename",
            "path",
            "image",
            "image_file",
            "wallpaper",
        }
    ):
        return (
            True,
            str(
                temporary_directory
                / f"{name}.tmp"
            ),
        )

    if name in {
        "encoder",
    }:
        return (
            True,
            "aac",
        )

    if name in {
        "stream",
        "audio_stream",
    }:
        return (
            True,
            "music",
        )

    if name in {
        "mode",
    }:
        return (
            True,
            "normal",
        )

    if name in {
        "pattern",
    }:
        return (
            True,
            [
                100,
                100,
            ],
        )

    if name in {
        "key",
        "alias",
        "value",
        "password",
    }:
        return (
            True,
            "termux_api_stc_test",
        )

    annotation = str(
        parameter.annotation
    )

    if "bool" in annotation:
        return (
            True,
            False,
        )

    if "int" in annotation:
        return (
            True,
            1,
        )

    if "float" in annotation:
        return (
            True,
            1.0,
        )

    if "List" in annotation or "list" in annotation:
        return (
            True,
            [
                "test"
            ],
        )

    if "str" in annotation:
        return (
            True,
            "test",
        )

    return (
        False,
        None,
    )


async def test_wrapper_dry_run(
    report: TestReport,
    package: Any,
) -> None:
    """
    Exercise every public wrapper function without touching Android.

    Each module's imported core runners are temporarily replaced with local
    fakes. This validates:
    - Python-level wrapper execution;
    - argument validation;
    - references to module constants;
    - synchronous wrappers;
    - asynchronous wrappers;
    - async-generator wrappers.

    It intentionally does NOT validate the Android command itself; the later
    device suite does that.
    """
    print(
        "\n"
        + color(
            "Complete wrapper dry-run",
            "36;1",
        )
    )

    async def fake_async(
        *args,
        **kwargs,
    ):
        return {
            "dry_run": True,
            "args": args,
            "kwargs": kwargs,
        }

    async def fake_stream(
        *args,
        **kwargs,
    ):
        yield json.dumps(
            {
                "dry_run": True,
                "args": args,
                "kwargs": kwargs,
            }
        )

    def fake_sync(
        *args,
        **kwargs,
    ):
        return {
            "dry_run": True,
            "args": args,
            "kwargs": kwargs,
        }

    runner_names = {
        "run": fake_sync,
        "run_text": fake_sync,
        "run_json": fake_sync,
        "run_bytes": fake_sync,
        "run_async": fake_async,
        "run_text_async": fake_async,
        "run_json_async": fake_async,
        "run_bytes_async": fake_async,
        "stream_text_async": fake_stream,
        "stream_bytes_async": fake_stream,
    }

    with tempfile.TemporaryDirectory(
        prefix="termux-api-stc-dry-run-"
    ) as temporary:
        temporary_directory = Path(
            temporary
        )

        for module_name in EXPECTED_MODULES:
            module = getattr(
                package,
                module_name,
            )

            functions = public_callables(
                module
            )

            originals = {}

            for runner_name, replacement in runner_names.items():
                if hasattr(
                    module,
                    runner_name,
                ):
                    originals[
                        runner_name
                    ] = getattr(
                        module,
                        runner_name
                    )

                    setattr(
                        module,
                        runner_name,
                        replacement,
                    )

            try:
                for function_name, function in sorted(
                    functions.items()
                ):
                    signature = inspect.signature(
                        function
                    )

                    args = []
                    kwargs = {}
                    unresolved = []

                    for parameter in signature.parameters.values():
                        if parameter.kind in {
                            inspect.Parameter.VAR_POSITIONAL,
                            inspect.Parameter.VAR_KEYWORD,
                        }:
                            continue

                        if parameter.default is not inspect.Parameter.empty:
                            continue

                        known, value = sample_argument(
                            parameter,
                            temporary_directory,
                        )

                        if not known:
                            unresolved.append(
                                parameter.name
                            )
                            continue

                        if parameter.kind == inspect.Parameter.POSITIONAL_ONLY:
                            args.append(
                                value
                            )
                        else:
                            kwargs[
                                parameter.name
                            ] = value

                    name = (
                        f"dry-run {module_name}.{function_name}"
                    )

                    if unresolved:
                        await run_case(
                            report,
                            name,
                            lambda: None,
                            skip=(
                                "unresolved required sample arguments: "
                                + ", ".join(
                                    unresolved
                                )
                            ),
                        )
                        continue

                    async def invoke(
                        function=function,
                        args=tuple(
                            args
                        ),
                        kwargs=dict(
                            kwargs
                        ),
                    ):
                        if inspect.isasyncgenfunction(
                            function
                        ):
                            generator = function(
                                *args,
                                **kwargs,
                            )

                            first = None

                            try:
                                first = await generator.__anext__()
                            except StopAsyncIteration:
                                pass
                            finally:
                                with contextlib.suppress(
                                    Exception
                                ):
                                    await generator.aclose()

                            return {
                                "async_generator": True,
                                "first": first,
                            }

                        return await call_maybe_async(
                            function,
                            *args,
                            **kwargs,
                        )

                    await run_case(
                        report,
                        name,
                        invoke,
                    )

            finally:
                for runner_name, original in originals.items():
                    setattr(
                        module,
                        runner_name,
                        original,
                    )


# ========================
# Static test definitions
# ========================
async def test_package_structure(
    report: TestReport,
    package: Any,
) -> None:
    await run_case(
        report,
        "package version",
        lambda: (
            package.__version__
            if package.__version__ == EXPECTED_VERSION
            else (_ for _ in ()).throw(
                AssertionError(
                    f"expected {EXPECTED_VERSION}, got {package.__version__}"
                )
            )
        ),
    )

    for module_name in EXPECTED_MODULES:
        await run_case(
            report,
            f"import module: {module_name}",
            lambda module_name=module_name: (
                getattr(
                    package,
                    module_name
                )
            ),
        )

    expected = set(
        EXPECTED_MODULES
    )

    missing = [
        current
        for current in expected
        if not hasattr(
            package,
            current
        )
    ]

    await run_case(
        report,
        "all expected modules exported",
        lambda: (
            True
            if not missing
            else (_ for _ in ()).throw(
                AssertionError(
                    f"missing modules: {missing}"
                )
            )
        ),
    )


async def test_public_api_shape(
    report: TestReport,
    package: Any,
) -> None:
    print(
        "\n"
        + color(
            "Public API inventory",
            "36;1",
        )
    )

    total_functions = 0
    async_functions = 0

    for module_name in EXPECTED_MODULES:
        module = getattr(
            package,
            module_name,
        )

        functions = public_callables(
            module
        )

        total_functions += len(
            functions
        )

        async_count = sum(
            inspect.iscoroutinefunction(
                current
            )
            or inspect.isasyncgenfunction(
                current
            )
            for current in functions.values()
        )

        async_functions += async_count

        detail = ", ".join(
            sorted(
                functions
            )
        )

        report.add(
            f"API inventory: {module_name}",
            "INFO",
            detail or "no public functions",
        )

        print_result(
            report.results[
                -1
            ]
        )

    await run_case(
        report,
        "public function inventory non-empty",
        lambda: (
            {
                "total_public_functions": total_functions,
                "async_public_functions": async_functions,
            }
            if total_functions > 0
            else (_ for _ in ()).throw(
                AssertionError(
                    "no public functions discovered"
                )
            )
        ),
    )


async def test_core(
    report: TestReport,
    package: Any,
) -> None:
    await run_case(
        report,
        "core.is_command_available(python)",
        lambda: package.is_command_available(
            shutil.which(
                "python"
            )
            or shutil.which(
                "python3"
            )
            or "python"
        ),
    )

    python_binary = (
        shutil.which(
            "python"
        )
        or shutil.which(
            "python3"
        )
    )

    if python_binary:
        await run_case(
            report,
            "core.run_text",
            lambda: package.run_text(
                python_binary,
                [
                    "-c",
                    "print('termux-api-stc-core-ok')",
                ],
            ),
        )

        await run_case(
            report,
            "core.run_json",
            lambda: package.run_json(
                python_binary,
                [
                    "-c",
                    "import json; print(json.dumps({'ok': True, 'value': 7}))",
                ],
            ),
        )

        await run_case(
            report,
            "core.run_bytes",
            lambda: package.run_bytes(
                python_binary,
                [
                    "-c",
                    "import sys; sys.stdout.buffer.write(bytes([0,1,2,255]))",
                ],
            ),
        )

        await run_case(
            report,
            "core.run_text_async",
            lambda: package.run_text_async(
                python_binary,
                [
                    "-c",
                    "print('async-ok')",
                ],
            ),
        )

        await run_case(
            report,
            "core.run_json_async",
            lambda: package.run_json_async(
                python_binary,
                [
                    "-c",
                    "import json; print(json.dumps({'async': True}))",
                ],
            ),
        )


async def test_declared_binaries(
    report: TestReport,
    package: Any,
) -> dict[str, bool]:
    print(
        "\n"
        + color(
            "Termux API binary discovery",
            "36;1",
        )
    )

    available = await run_case(
        report,
        "available_apis()",
        package.available_apis,
    )

    tools = await run_case(
        report,
        "available_tools()",
        package.available_tools,
    )

    available = (
        available
        if isinstance(
            available,
            dict
        )
        else {}
    )

    tools = (
        tools
        if isinstance(
            tools,
            dict
        )
        else {}
    )

    for binary in package.TERMUX_API_BINARIES:
        exists = bool(
            available.get(
                binary
            )
        )

        report.add(
            f"binary: {binary}",
            "PASS"
            if exists
            else "SKIP",
            "available"
            if exists
            else "not present in PATH",
        )

        print_result(
            report.results[
                -1
            ]
        )

    for binary in package.TERMUX_TOOL_BINARIES:
        exists = bool(
            tools.get(
                binary
            )
        )

        report.add(
            f"tool: {binary}",
            "PASS"
            if exists
            else "SKIP",
            "available"
            if exists
            else "not present in PATH",
        )

        print_result(
            report.results[
                -1
            ]
        )

    return {
        **available,
        **tools,
    }


# ==========================
# Device test definitions
# ==========================
async def test_read_only_apis(
    report: TestReport,
    package: Any,
    binary_state: dict[str, bool],
) -> None:
    print(
        "\n"
        + color(
            "Read-only device API tests",
            "36;1",
        )
    )

    for module_name, candidates in READ_ONLY_CANDIDATES.items():
        module = getattr(
            package,
            module_name,
        )

        selected = find_callable(
            module,
            candidates,
        )

        if selected is None:
            await run_case(
                report,
                f"{module_name}: read-only operation",
                lambda: None,
                skip="no known read-only callable exported",
            )
            continue

        name, function, args, kwargs = selected

        await run_case(
            report,
            f"{module_name}.{name}",
            lambda function=function, args=args, kwargs=kwargs: call_maybe_async(
                function,
                *args,
                **kwargs,
            ),
        )


async def test_location_stream(
    report: TestReport,
    package: Any,
    enabled: bool,
) -> None:
    if not enabled:
        await run_case(
            report,
            "location.stream_updates",
            lambda: None,
            skip="requires --interactive",
        )
        return

    function = getattr(
        package.location,
        "stream_updates",
        None,
    )

    if not callable(
        function
    ):
        await run_case(
            report,
            "location.stream_updates",
            lambda: None,
            skip="stream_updates not exported",
        )
        return

    async def sample():
        values = []

        stream = function(
            "network"
        )

        try:
            async with asyncio.timeout(
                10.0
            ):
                async for current in stream:
                    values.append(
                        current
                    )

                    if len(
                        values
                    ) >= 2:
                        break
        except TimeoutError:
            pass

        return {
            "samples": values,
        }

    await run_case(
        report,
        "location.stream_updates(network)",
        sample,
    )


async def test_sensor_stream(
    report: TestReport,
    package: Any,
    enabled: bool,
) -> None:
    if not enabled:
        await run_case(
            report,
            "sensor stream",
            lambda: None,
            skip="requires --interactive",
        )
        return

    list_function = getattr(
        package.sensor,
        "list_sensors_async",
        None,
    ) or getattr(
        package.sensor,
        "list_sensors",
        None,
    )

    stream_function = getattr(
        package.sensor,
        "stream",
        None,
    )

    if not callable(
        list_function
    ) or not callable(
        stream_function
    ):
        await run_case(
            report,
            "sensor stream",
            lambda: None,
            skip="sensor list/stream API unavailable",
        )
        return

    async def sample():
        sensors = await call_maybe_async(
            list_function
        )

        if not sensors:
            return {
                "sensors": sensors,
                "samples": [],
            }

        sensor_name = None

        if isinstance(
            sensors,
            list
        ):
            first = sensors[
                0
            ]

            if isinstance(
                first,
                str
            ):
                sensor_name = first

            elif isinstance(
                first,
                dict
            ):
                sensor_name = (
                    first.get(
                        "name"
                    )
                    or first.get(
                        "sensor"
                    )
                )

        if not sensor_name:
            return {
                "sensors": sensors,
                "samples": [],
            }

        values = []

        try:
            async with asyncio.timeout(
                10.0
            ):
                async for current in stream_function(
                    [
                        sensor_name
                    ],
                    delay_ms=250,
                ):
                    values.append(
                        current
                    )

                    if len(
                        values
                    ) >= 3:
                        break
        except TimeoutError:
            pass

        return {
            "sensor": sensor_name,
            "samples": values,
        }

    await run_case(
        report,
        "sensor.stream",
        sample,
    )


async def test_camera(
    report: TestReport,
    package: Any,
    enabled: bool,
) -> None:
    if not enabled:
        await run_case(
            report,
            "camera photo",
            lambda: None,
            skip="requires --interactive or --all",
        )
        return

    function = getattr(
        package.camera,
        "photo_async",
        None,
    ) or getattr(
        package.camera,
        "photo",
        None,
    )

    if not callable(
        function
    ):
        await run_case(
            report,
            "camera photo",
            lambda: None,
            skip="camera photo API unavailable",
        )
        return

    output = Path(
        tempfile.gettempdir()
    ) / "termux-api-stc-test-camera.jpg"

    with contextlib.suppress(
        Exception
    ):
        output.unlink()

    await run_case(
        report,
        "camera.photo",
        lambda: call_maybe_async(
            function,
            str(
                output
            ),
            camera_id="0",
        ),
    )

    await run_case(
        report,
        "camera output exists",
        lambda: {
            "path": str(
                output
            ),
            "size": output.stat().st_size,
        }
        if output.exists()
        and output.stat().st_size > 0
        else (_ for _ in ()).throw(
            AssertionError(
                "camera output file was not created"
            )
        ),
    )


async def test_torch(
    report: TestReport,
    package: Any,
    enabled: bool,
) -> None:
    if not enabled:
        await run_case(
            report,
            "torch on/off",
            lambda: None,
            skip="requires --interactive or --all",
        )
        return

    on_function = getattr(
        package.torch,
        "on_async",
        None,
    ) or getattr(
        package.torch,
        "on",
        None,
    )

    off_function = getattr(
        package.torch,
        "off_async",
        None,
    ) or getattr(
        package.torch,
        "off",
        None,
    )

    if not callable(
        on_function
    ) or not callable(
        off_function
    ):
        await run_case(
            report,
            "torch on/off",
            lambda: None,
            skip="torch API unavailable",
        )
        return

    await run_case(
        report,
        "torch.on",
        lambda: call_maybe_async(
            on_function
        ),
    )

    await asyncio.sleep(
        1.0
    )

    await run_case(
        report,
        "torch.off",
        lambda: call_maybe_async(
            off_function
        ),
    )


async def test_vibrate(
    report: TestReport,
    package: Any,
    enabled: bool,
) -> None:
    if not enabled:
        await run_case(
            report,
            "vibrate",
            lambda: None,
            skip="requires --interactive or --all",
        )
        return

    functions = public_callables(
        package.vibrate
    )

    function = (
        functions.get(
            "vibrate_async"
        )
        or functions.get(
            "vibrate"
        )
    )

    if function is None:
        await run_case(
            report,
            "vibrate",
            lambda: None,
            skip="vibration API unavailable",
        )
        return

    signature = inspect.signature(
        function
    )

    kwargs = {}

    if "duration_ms" in signature.parameters:
        kwargs[
            "duration_ms"
        ] = 300

    elif "duration" in signature.parameters:
        kwargs[
            "duration"
        ] = 300

    await run_case(
        report,
        "vibrate",
        lambda: call_maybe_async(
            function,
            **kwargs,
        ),
    )


async def test_microphone(
    report: TestReport,
    package: Any,
    enabled: bool,
) -> None:
    if not enabled:
        await run_case(
            report,
            "microphone record/stop",
            lambda: None,
            skip="requires --interactive or --all",
        )
        return

    record = getattr(
        package.microphone,
        "record_async",
        None,
    ) or getattr(
        package.microphone,
        "record",
        None,
    )

    quit_function = getattr(
        package.microphone,
        "quit_async",
        None,
    ) or getattr(
        package.microphone,
        "quit",
        None,
    )

    if not callable(
        record
    ) or not callable(
        quit_function
    ):
        await run_case(
            report,
            "microphone record/stop",
            lambda: None,
            skip="microphone API unavailable",
        )
        return

    output = Path(
        tempfile.gettempdir()
    ) / "termux-api-stc-test-audio.m4a"

    with contextlib.suppress(
        Exception
    ):
        output.unlink()

    await run_case(
        report,
        "microphone.record",
        lambda: call_maybe_async(
            record,
            file=str(
                output
            ),
            limit_seconds=2,
            background=True,
        ),
    )

    await asyncio.sleep(
        3.0
    )

    await run_case(
        report,
        "microphone.quit",
        lambda: call_maybe_async(
            quit_function
        ),
    )


async def test_clipboard_set(
    report: TestReport,
    package: Any,
    enabled: bool,
) -> None:
    if not enabled:
        await run_case(
            report,
            "clipboard set",
            lambda: None,
            skip="requires --interactive or --all",
        )
        return

    function = getattr(
        package.clipboard,
        "set_async",
        None,
    ) or getattr(
        package.clipboard,
        "set",
        None,
    )

    if not callable(
        function
    ):
        await run_case(
            report,
            "clipboard set",
            lambda: None,
            skip="clipboard setter unavailable",
        )
        return

    await run_case(
        report,
        "clipboard.set",
        lambda: call_maybe_async(
            function,
            "termux-api-stc full_test.py",
        ),
    )


async def test_sms(
    report: TestReport,
    package: Any,
    enabled: bool,
    number: str | None,
    text: str,
) -> None:
    if not enabled or not number:
        await run_case(
            report,
            "sms.send",
            lambda: None,
            skip=(
                "requires --destructive/--all and --sms-number"
            ),
        )
        return

    function = getattr(
        package.sms,
        "send_async",
        None,
    ) or getattr(
        package.sms,
        "send",
        None,
    )

    await run_case(
        report,
        "sms.send",
        lambda: call_maybe_async(
            function,
            number,
            text,
        ),
    )


async def test_call(
    report: TestReport,
    package: Any,
    enabled: bool,
    number: str | None,
) -> None:
    if not enabled or not number:
        await run_case(
            report,
            "telephony.call",
            lambda: None,
            skip=(
                "requires --destructive/--all and --phone-number"
            ),
        )
        return

    function = getattr(
        package.telephony,
        "call_async",
        None,
    ) or getattr(
        package.telephony,
        "call",
        None,
    )

    await run_case(
        report,
        "telephony.call",
        lambda: call_maybe_async(
            function,
            number,
        ),
    )


# ============================
# Coverage/report definitions
# ============================
async def test_async_pairing(
    report: TestReport,
    package: Any,
) -> None:
    """
    Structural coverage rule:
    if a module exposes X and X_async, validate both are callable.
    Functions without an async pair are reported informationally, not failed,
    because stream async-generators intentionally have no synchronous twin.
    """
    print(
        "\n"
        + color(
            "Synchronous/asynchronous API pairing",
            "36;1",
        )
    )

    for module_name in EXPECTED_MODULES:
        module = getattr(
            package,
            module_name,
        )

        functions = public_callables(
            module
        )

        names = set(
            functions
        )

        for name in sorted(
            names
        ):
            if name.endswith(
                "_async"
            ):
                base = name[
                    :-6
                ]

                if base in names:
                    await run_case(
                        report,
                        f"pair {module_name}.{base}/{name}",
                        lambda module=module, base=base, name=name: {
                            "sync": str(
                                inspect.signature(
                                    getattr(
                                        module,
                                        base
                                    )
                                )
                            ),
                            "async": str(
                                inspect.signature(
                                    getattr(
                                        module,
                                        name
                                    )
                                )
                            ),
                        },
                    )


def print_summary(
    report: TestReport,
) -> None:
    print(
        "\n"
        + "=" * 72
    )
    print(
        color(
            "TERMUX-API-STC FULL TEST SUMMARY",
            "36;1",
        )
    )
    print(
        "=" * 72
    )
    print(
        f"PASS: {report.passed}"
    )
    print(
        f"FAIL: {report.failed}"
    )
    print(
        f"SKIP: {report.skipped}"
    )
    print(
        f"TOTAL: {len(report.results)}"
    )
    print(
        "=" * 72
    )

    if report.failed:
        print(
            color(
                "RESULT: FAILED",
                "31;1",
            )
        )

        print(
            "\nFailures:"
        )

        for current in report.results:
            if current.status == "FAIL":
                print(
                    f"- {current.name}: {current.detail}"
                )

    else:
        print(
            color(
                "RESULT: PASSED",
                "32;1",
            )
        )


# =========================
# Command-line definitions
# =========================
def parse_args():
    parser = argparse.ArgumentParser(
        description="Complete repository/device test for termux-api-stc"
    )

    mode = parser.add_mutually_exclusive_group()

    mode.add_argument(
        "--safe",
        action="store_true",
        help="Read-only/non-destructive suite (default)",
    )

    mode.add_argument(
        "--interactive",
        action="store_true",
        help="Also exercise camera, microphone, torch, streams, clipboard, vibration",
    )

    mode.add_argument(
        "--destructive",
        action="store_true",
        help="Also permit SMS/call tests when values are supplied",
    )

    mode.add_argument(
        "--all",
        action="store_true",
        help="Run safe + interactive + destructive tests",
    )

    parser.add_argument(
        "--phone-number",
        default=None,
        help="Number used only for the explicit telephony call test",
    )

    parser.add_argument(
        "--sms-number",
        default=None,
        help="Number used only for the explicit SMS send test",
    )

    parser.add_argument(
        "--sms-text",
        default="termux-api-stc full test",
    )

    parser.add_argument(
        "--json-report",
        default=None,
        help="Optional JSON report output path",
    )

    return parser.parse_args()


# ====================
# Runtime definition
# ====================
async def async_main(
    args,
) -> int:
    report = TestReport()

    print(
        "=" * 72
    )
    print(
        "termux-api-stc — complete repository/device test"
    )
    print(
        "=" * 72
    )
    print(
        f"Python:      {sys.version.split()[0]}"
    )
    print(
        f"Executable:  {sys.executable}"
    )
    print(
        f"Termux:      {require_termux()}"
    )
    print(
        f"PREFIX:      {os.environ.get('PREFIX')}"
    )
    print(
        f"HOME:        {os.environ.get('HOME')}"
    )
    print(
        "=" * 72
    )

    try:
        import termux_api_stc as package

    except Exception as exc:
        result = TestResult(
            name="import termux_api_stc",
            status="FAIL",
            detail=(
                f"{type(exc).__name__}: {exc}"
            ),
        )
        report.results.append(
            result
        )
        print_result(
            result
        )
        print_summary(
            report
        )
        return 1

    await run_case(
        report,
        "import termux_api_stc",
        lambda: package.__file__,
    )

    await test_package_structure(
        report,
        package,
    )

    await test_public_api_shape(
        report,
        package,
    )

    await test_async_pairing(
        report,
        package,
    )

    await test_wrapper_dry_run(
        report,
        package,
    )

    await test_core(
        report,
        package,
    )

    binary_state = await test_declared_binaries(
        report,
        package,
    )

    if not require_termux():
        report.add(
            "Termux runtime",
            "SKIP",
            (
                "Not running inside Termux. "
                "Repository/core tests were executed; Android API execution is skipped."
            ),
        )
        print_result(
            report.results[
                -1
            ]
        )

    else:
        await test_read_only_apis(
            report,
            package,
            binary_state,
        )

        interactive = (
            args.interactive
            or args.all
        )

        destructive = (
            args.destructive
            or args.all
        )

        await test_location_stream(
            report,
            package,
            interactive,
        )

        await test_sensor_stream(
            report,
            package,
            interactive,
        )

        await test_camera(
            report,
            package,
            interactive,
        )

        await test_torch(
            report,
            package,
            interactive,
        )

        await test_vibrate(
            report,
            package,
            interactive,
        )

        await test_microphone(
            report,
            package,
            interactive,
        )

        await test_clipboard_set(
            report,
            package,
            interactive,
        )

        await test_sms(
            report,
            package,
            destructive,
            args.sms_number,
            args.sms_text,
        )

        await test_call(
            report,
            package,
            destructive,
            args.phone_number,
        )

    if args.json_report:
        output = Path(
            args.json_report
        ).expanduser().resolve()

        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output.write_text(
            json.dumps(
                {
                    "generated_at": time.time(),
                    "version": getattr(
                        package,
                        "__version__",
                        None,
                    ),
                    "summary": {
                        "passed": report.passed,
                        "failed": report.failed,
                        "skipped": report.skipped,
                        "total": len(
                            report.results
                        ),
                    },
                    "results": [
                        {
                            "name": current.name,
                            "status": current.status,
                            "detail": current.detail,
                            "duration": current.duration,
                        }
                        for current in report.results
                    ],
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

        print(
            f"\nJSON report: {output}"
        )

    print_summary(
        report
    )

    return (
        1
        if report.failed
        else 0
    )


def main() -> int:
    args = parse_args()

    try:
        return asyncio.run(
            async_main(
                args
            )
        )

    except KeyboardInterrupt:
        print(
            "\nInterrupted."
        )
        return 130


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
