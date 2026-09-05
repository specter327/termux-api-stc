#!/usr/bin/env bash
set -uo pipefail

###############################################################################
# termux-api-stc
# Unified pytest unit-test campaign runner
#
# Expected structure:
#
# tests/
# ├── README.md
# ├── run-tests.sh
# ├── results/
# └── unit-test/
#     ├── conftest.py
#     ├── test_*.py
#     └── ...
#
# Usage:
#   ./tests/run-tests.sh
#
# Optional:
#   PYTHON_BIN=/path/to/python3 ./tests/run-tests.sh
#
###############################################################################

SCRIPT_VERSION="2"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
UNIT_TEST_DIR="${SCRIPT_DIR}/unit-test"
RESULTS_ROOT="${SCRIPT_DIR}/results"

TIMESTAMP="$(date -u +"%Y%m%dT%H%M%SZ")"
RESULT_DIR="${RESULTS_ROOT}/${TIMESTAMP}"

METADATA_FILE="${RESULT_DIR}/metadata.txt"
ENVIRONMENT_FILE="${RESULT_DIR}/environment.txt"
PACKAGES_FILE="${RESULT_DIR}/packages.txt"
DISCOVERY_FILE="${RESULT_DIR}/discovery.txt"
SUMMARY_FILE="${RESULT_DIR}/summary.txt"
OUTPUT_FILE="${RESULT_DIR}/test-output.txt"
EXIT_CODE_FILE="${RESULT_DIR}/exit-code.txt"
HASH_FILE="${RESULT_DIR}/SHA256SUMS"

###############################################################################
# Helpers
###############################################################################

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

section() {
    printf '\n'
    printf '===============================================================================\n'
    printf '%s\n' "$1"
    printf '===============================================================================\n'
}

utc_now() {
    date -u +"%Y-%m-%dT%H:%M:%SZ"
}

resolve_python() {
    if [[ -n "${PYTHON_BIN:-}" ]]; then
        if [[ -x "${PYTHON_BIN}" ]]; then
            printf '%s\n' "${PYTHON_BIN}"
            return 0
        fi

        if command_exists "${PYTHON_BIN}"; then
            command -v "${PYTHON_BIN}"
            return 0
        fi

        return 1
    fi

    if command_exists python3; then
        command -v python3
        return 0
    fi

    if command_exists python; then
        command -v python
        return 0
    fi

    return 1
}

###############################################################################
# Initial validation
###############################################################################

if [[ ! -d "${UNIT_TEST_DIR}" ]]; then
    echo "ERROR: unit-test directory not found:"
    echo "  ${UNIT_TEST_DIR}"
    exit 2
fi

mkdir -p "${RESULT_DIR}"

if ! PYTHON_EXECUTABLE="$(resolve_python)"; then
    {
        echo "ERROR: no Python interpreter found."
        echo
        echo "Expected one of:"
        echo "  python3"
        echo "  python"
        echo
        echo "Or specify explicitly:"
        echo "  PYTHON_BIN=/path/to/python3 ./tests/run-tests.sh"
    } | tee "${OUTPUT_FILE}"

    echo "127" > "${EXIT_CODE_FILE}"

    (
        cd "${RESULT_DIR}" || exit 1
        sha256sum test-output.txt exit-code.txt > SHA256SUMS
    )

    exit 127
fi

###############################################################################
# Pytest validation
###############################################################################

if ! "${PYTHON_EXECUTABLE}" -m pytest --version >/dev/null 2>&1; then
    {
        echo "ERROR: pytest is not installed for:"
        echo "  ${PYTHON_EXECUTABLE}"
        echo
        echo "Install test dependencies with:"
        echo "  ${PYTHON_EXECUTABLE} -m pip install -U pytest pytest-asyncio"
    } | tee "${OUTPUT_FILE}"

    echo "126" > "${EXIT_CODE_FILE}"

    (
        cd "${RESULT_DIR}" || exit 1
        sha256sum test-output.txt exit-code.txt > SHA256SUMS
    )

    exit 126
fi

###############################################################################
# Test environment preflight
###############################################################################

if ! "${PYTHON_EXECUTABLE}" -c 'import pytest_asyncio' >/dev/null 2>&1; then
    echo "ERROR: pytest-asyncio is required for the async test suite."
    echo "Install with: ${PYTHON_EXECUTABLE} -m pip install -e '.[test]'"
    exit 125
fi

VERSION_PREFLIGHT="$(
PYTHONPATH="${PROJECT_ROOT}${PYTHONPATH:+:${PYTHONPATH}}" "${PYTHON_EXECUTABLE}" - <<'PY'
import importlib.metadata as md
import termux_api_stc
try:
    installed = md.version("termux-api-stc")
except md.PackageNotFoundError:
    installed = None
print(termux_api_stc.__version__)
print(installed or "")
PY
)"
RUNTIME_VERSION="$(printf '%s\n' "${VERSION_PREFLIGHT}" | sed -n '1p')"
INSTALLED_VERSION="$(printf '%s\n' "${VERSION_PREFLIGHT}" | sed -n '2p')"

if [[ -n "${INSTALLED_VERSION}" && "${INSTALLED_VERSION}" != "${RUNTIME_VERSION}" ]]; then
    echo "ERROR: runtime/distribution version mismatch."
    echo "runtime=${RUNTIME_VERSION}"
    echo "distribution=${INSTALLED_VERSION}"
    echo "Reinstall with: ${PYTHON_EXECUTABLE} -m pip install -e '.[test]'"
    exit 124
fi

###############################################################################
# Discovery
###############################################################################

mapfile -t TEST_FILES < <(
    find "${UNIT_TEST_DIR}" \
        -maxdepth 1 \
        -type f \
        -name 'test_*.py' \
        -print \
        | sort
)

TEST_FILE_COUNT="${#TEST_FILES[@]}"

{
    section "PYTEST DISCOVERY"

    echo "directory=${UNIT_TEST_DIR}"
    echo "test_file_count=${TEST_FILE_COUNT}"
    echo

    for test_file in "${TEST_FILES[@]}"; do
        echo "$(basename "${test_file}")"
    done

    echo
    echo "[pytest --collect-only]"
    PYTHONPATH="${PROJECT_ROOT}${PYTHONPATH:+:${PYTHONPATH}}" \
        "${PYTHON_EXECUTABLE}" -m pytest \
        --collect-only -q "${UNIT_TEST_DIR}" 2>&1 || true

} > "${DISCOVERY_FILE}"

if [[ "${TEST_FILE_COUNT}" -eq 0 ]]; then
    {
        echo "ERROR: no pytest test files found in:"
        echo "  ${UNIT_TEST_DIR}"
        echo
        echo "Expected filenames matching:"
        echo "  test_*.py"
    } | tee "${OUTPUT_FILE}"

    echo "2" > "${EXIT_CODE_FILE}"

    (
        cd "${RESULT_DIR}" || exit 1
        sha256sum discovery.txt test-output.txt exit-code.txt > SHA256SUMS
    )

    exit 2
fi

###############################################################################
# Metadata
###############################################################################

{
    section "TERMUX-API-STC UNIT-TEST CAMPAIGN"

    echo "runner_version=${SCRIPT_VERSION}"
    echo "timestamp_utc=${TIMESTAMP}"
    echo "started_utc=$(utc_now)"
    echo "project_root=${PROJECT_ROOT}"
    echo "tests_directory=${SCRIPT_DIR}"
    echo "unit_test_directory=${UNIT_TEST_DIR}"
    echo "results_directory=${RESULT_DIR}"
    echo "test_file_count=${TEST_FILE_COUNT}"
    echo "python_executable=${PYTHON_EXECUTABLE}"

    echo
    section "GIT"

    if command_exists git && \
       git -C "${PROJECT_ROOT}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then

        echo "git_commit=$(git -C "${PROJECT_ROOT}" rev-parse HEAD 2>/dev/null || echo UNKNOWN)"
        echo "git_branch=$(git -C "${PROJECT_ROOT}" branch --show-current 2>/dev/null || echo UNKNOWN)"

        if [[ -z "$(git -C "${PROJECT_ROOT}" status --porcelain 2>/dev/null)" ]]; then
            echo "git_tree=clean"
        else
            echo "git_tree=dirty"
        fi

        echo
        echo "[git status --short]"
        git -C "${PROJECT_ROOT}" status --short 2>&1 || true
    else
        echo "git_commit=UNKNOWN"
        echo "git_branch=UNKNOWN"
        echo "git_tree=UNKNOWN"
    fi

} > "${METADATA_FILE}"

###############################################################################
# Environment
###############################################################################

{
    section "SYSTEM"

    echo "date_utc=$(utc_now)"
    echo "pwd=$(pwd)"
    echo "user=$(id -un 2>/dev/null || echo UNKNOWN)"
    echo "uid=$(id -u 2>/dev/null || echo UNKNOWN)"
    echo "shell=${SHELL:-UNKNOWN}"

    if command_exists uname; then
        echo "uname=$(uname -a 2>/dev/null || echo UNKNOWN)"
        echo "machine=$(uname -m 2>/dev/null || echo UNKNOWN)"
        echo "kernel=$(uname -r 2>/dev/null || echo UNKNOWN)"
    else
        echo "uname=UNKNOWN"
        echo "machine=UNKNOWN"
        echo "kernel=UNKNOWN"
    fi

    echo
    section "PYTHON"

    echo "python_executable=${PYTHON_EXECUTABLE}"
    echo "python_version=$("${PYTHON_EXECUTABLE}" --version 2>&1)"

    echo "python_prefix=$("${PYTHON_EXECUTABLE}" - <<'PY'
import sys
print(sys.prefix)
PY
)"

    echo "python_base_prefix=$("${PYTHON_EXECUTABLE}" - <<'PY'
import sys
print(sys.base_prefix)
PY
)"

    echo "python_implementation=$("${PYTHON_EXECUTABLE}" - <<'PY'
import platform
print(platform.python_implementation())
PY
)"

    echo "pytest_version=$("${PYTHON_EXECUTABLE}" -m pytest --version 2>&1)"

    echo
    section "TERMUX / ANDROID"

    echo "PREFIX=${PREFIX:-UNKNOWN}"
    echo "TERMUX_VERSION=${TERMUX_VERSION:-UNKNOWN}"

    if command_exists getprop; then
        echo "android_release=$(getprop ro.build.version.release 2>/dev/null || echo UNKNOWN)"
        echo "android_sdk=$(getprop ro.build.version.sdk 2>/dev/null || echo UNKNOWN)"
        echo "device_manufacturer=$(getprop ro.product.manufacturer 2>/dev/null || echo UNKNOWN)"
        echo "device_model=$(getprop ro.product.model 2>/dev/null || echo UNKNOWN)"
        echo "device_name=$(getprop ro.product.device 2>/dev/null || echo UNKNOWN)"
        echo "device_abi=$(getprop ro.product.cpu.abi 2>/dev/null || echo UNKNOWN)"
    else
        echo "android_release=UNKNOWN"
        echo "android_sdk=UNKNOWN"
        echo "device_manufacturer=UNKNOWN"
        echo "device_model=UNKNOWN"
        echo "device_name=UNKNOWN"
        echo "device_abi=UNKNOWN"
    fi

    echo
    section "TERMUX-API PACKAGE"

    if command_exists dpkg-query; then
        dpkg-query -W \
            -f='package=${Package}\nversion=${Version}\nstatus=${Status}\n' \
            termux-api 2>/dev/null \
            || echo "termux_api_package=UNKNOWN"
    elif command_exists pkg; then
        pkg list-installed termux-api 2>&1 || true
    else
        echo "termux_api_package=UNKNOWN"
    fi

    echo
    section "AVAILABLE TERMUX COMMANDS"

    if [[ -n "${PREFIX:-}" && -d "${PREFIX}/bin" ]]; then
        find "${PREFIX}/bin" \
            -maxdepth 1 \
            -type f \
            -name 'termux-*' \
            -printf '%f\n' 2>/dev/null \
            | sort || true
    else
        echo "Termux PREFIX unavailable."
    fi

} > "${ENVIRONMENT_FILE}"

###############################################################################
# Python package snapshot
###############################################################################

{
    section "PYTHON PACKAGES"

    "${PYTHON_EXECUTABLE}" -m pip freeze 2>&1 || true

} > "${PACKAGES_FILE}"

###############################################################################
# Campaign execution
###############################################################################

cd "${PROJECT_ROOT}" || exit 1

CAMPAIGN_START_EPOCH="$(date +%s)"

{
    section "TERMUX-API-STC UNIT-TEST EXECUTION"

    echo "started_utc=$(utc_now)"
    echo "python=${PYTHON_EXECUTABLE}"
    echo "pytest=$("${PYTHON_EXECUTABLE}" -m pytest --version 2>&1)"
    echo "test_file_count=${TEST_FILE_COUNT}"
    echo
    echo "command:"
    echo "  ${PYTHON_EXECUTABLE} -m pytest -vv ${UNIT_TEST_DIR}"
    echo

} | tee "${OUTPUT_FILE}"

set +e

PYTHONPATH="${PROJECT_ROOT}${PYTHONPATH:+:${PYTHONPATH}}" \
    "${PYTHON_EXECUTABLE}" -m pytest \
    -vv \
    "${UNIT_TEST_DIR}" \
    2>&1 | tee -a "${OUTPUT_FILE}"

PYTEST_EXIT=${PIPESTATUS[0]}

set -e

CAMPAIGN_END_EPOCH="$(date +%s)"
CAMPAIGN_DURATION="$((CAMPAIGN_END_EPOCH - CAMPAIGN_START_EPOCH))"

###############################################################################
# Summary
###############################################################################

case "${PYTEST_EXIT}" in
    0)
        FINAL_STATUS="PASS"
        ;;
    1)
        FINAL_STATUS="FAIL"
        ;;
    2)
        FINAL_STATUS="INTERRUPTED_OR_USAGE_ERROR"
        ;;
    3)
        FINAL_STATUS="INTERNAL_ERROR"
        ;;
    4)
        FINAL_STATUS="USAGE_ERROR"
        ;;
    5)
        FINAL_STATUS="NO_TESTS_COLLECTED"
        ;;
    *)
        FINAL_STATUS="ERROR"
        ;;
esac

{
    section "CAMPAIGN SUMMARY"

    echo "started_utc=${TIMESTAMP}"
    echo "completed_utc=$(utc_now)"
    echo "duration_seconds=${CAMPAIGN_DURATION}"
    echo "test_file_count=${TEST_FILE_COUNT}"
    echo "pytest_exit_code=${PYTEST_EXIT}"
    echo "status=${FINAL_STATUS}"

    echo
    echo "[pytest summary]"
    grep -E \
        '([0-9]+ passed|[0-9]+ failed|[0-9]+ skipped|[0-9]+ xfailed|[0-9]+ xpassed|[0-9]+ error|[0-9]+ errors)' \
        "${OUTPUT_FILE}" \
        | tail -n 5 \
        || true

} > "${SUMMARY_FILE}"

cat "${SUMMARY_FILE}" | tee -a "${OUTPUT_FILE}"

printf '%s\n' "${PYTEST_EXIT}" > "${EXIT_CODE_FILE}"

###############################################################################
# Completion metadata
###############################################################################

{
    echo
    section "CAMPAIGN COMPLETION"
    echo "completed_utc=$(utc_now)"
    echo "duration_seconds=${CAMPAIGN_DURATION}"
    echo "status=${FINAL_STATUS}"
    echo "pytest_exit_code=${PYTEST_EXIT}"
} >> "${METADATA_FILE}"

###############################################################################
# Integrity
###############################################################################

(
    cd "${RESULT_DIR}" || exit 1

    sha256sum \
        metadata.txt \
        environment.txt \
        packages.txt \
        discovery.txt \
        summary.txt \
        test-output.txt \
        exit-code.txt \
        > SHA256SUMS
)

###############################################################################
# Final output
###############################################################################

echo
section "EVIDENCE"

echo "Campaign:"
echo "  ${RESULT_DIR}"
echo

echo "Files:"
echo "  metadata.txt"
echo "  environment.txt"
echo "  packages.txt"
echo "  discovery.txt"
echo "  summary.txt"
echo "  test-output.txt"
echo "  exit-code.txt"
echo "  SHA256SUMS"
echo

echo "Verify evidence:"
echo "  cd \"${RESULT_DIR}\" && sha256sum -c SHA256SUMS"
echo

echo "STATUS: ${FINAL_STATUS}"

exit "${PYTEST_EXIT}"
