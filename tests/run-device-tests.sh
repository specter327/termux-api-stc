#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
RESULTS_ROOT="${SCRIPT_DIR}/results"
MODE="${1:-readonly}"
TIMESTAMP="$(date -u +'%Y%m%dT%H%M%SZ')"
RESULT_DIR="${RESULTS_ROOT}/${TIMESTAMP}-device-${MODE}"

resolve_python() {
    if [[ -n "${PYTHON_BIN:-}" ]]; then
        command -v "${PYTHON_BIN}" 2>/dev/null || printf '%s\n' "${PYTHON_BIN}"
    elif command -v python3 >/dev/null 2>&1; then
        command -v python3
    elif command -v python >/dev/null 2>&1; then
        command -v python
    else
        return 1
    fi
}

PYTHON="$(resolve_python)" || { echo "ERROR: python3/python not found"; exit 127; }

if [[ "${MODE}" != "readonly" && "${MODE}" != "side-effects" && "${MODE}" != "all" ]]; then
    echo "Usage: $0 [readonly|side-effects|all]"
    exit 2
fi

if [[ -z "${PREFIX:-}" || "${PREFIX}" != *com.termux* ]]; then
    echo "ERROR: this campaign must run inside Termux."
    exit 3
fi

mkdir -p "${RESULT_DIR}"

{
    echo "timestamp_utc=${TIMESTAMP}"
    echo "mode=${MODE}"
    echo "python=${PYTHON}"
    echo "python_version=$(${PYTHON} --version 2>&1)"
    echo "PREFIX=${PREFIX:-UNKNOWN}"
    echo "TERMUX_VERSION=${TERMUX_VERSION:-UNKNOWN}"
    echo "android_release=$(getprop ro.build.version.release 2>/dev/null || true)"
    echo "android_sdk=$(getprop ro.build.version.sdk 2>/dev/null || true)"
    echo "manufacturer=$(getprop ro.product.manufacturer 2>/dev/null || true)"
    echo "model=$(getprop ro.product.model 2>/dev/null || true)"
    echo
    echo "[termux-info]"
    command -v termux-info >/dev/null 2>&1 && termux-info 2>&1 || true
    echo
    echo "[termux-api package]"
    dpkg-query -W -f='${Package} ${Version} ${Status}\n' termux-api 2>&1 || true
    echo
    echo "[commands]"
    for c in "${PREFIX}"/bin/termux-*; do
        [[ -e "$c" ]] && basename "$c"
    done | sort
} > "${RESULT_DIR}/environment.txt"

case "${MODE}" in
    readonly)
        PYTEST_ARGS=(tests/device/test_readonly_conformance.py tests/device/test_native_parity.py)
        ;;
    side-effects)
        export TERMUX_API_STC_ENABLE_SIDE_EFFECTS=1
        PYTEST_ARGS=(tests/device/test_side_effects.py tests/device/test_guarded_actions.py)
        ;;
    all)
        export TERMUX_API_STC_ENABLE_SIDE_EFFECTS=1
        PYTEST_ARGS=(tests/device)
        ;;
esac

cd "${PROJECT_ROOT}" || exit 1
set +e
PYTHONPATH="${PROJECT_ROOT}${PYTHONPATH:+:${PYTHONPATH}}" \
    "${PYTHON}" -m pytest -vv "${PYTEST_ARGS[@]}" 2>&1 | tee "${RESULT_DIR}/test-output.txt"
RC=${PIPESTATUS[0]}
set -e

printf '%s\n' "${RC}" > "${RESULT_DIR}/exit-code.txt"
{
    echo "mode=${MODE}"
    echo "exit_code=${RC}"
    if [[ "${RC}" -eq 0 ]]; then echo "status=PASS"; else echo "status=FAIL"; fi
} > "${RESULT_DIR}/summary.txt"

(
    cd "${RESULT_DIR}" || exit 1
    sha256sum environment.txt test-output.txt exit-code.txt summary.txt > SHA256SUMS
)

echo
cat "${RESULT_DIR}/summary.txt"
echo "evidence=${RESULT_DIR}"
exit "${RC}"
