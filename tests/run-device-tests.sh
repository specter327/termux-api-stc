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
        if [[ -x "${PYTHON_BIN}" ]]; then printf '%s\n' "${PYTHON_BIN}"; return 0; fi
        command -v "${PYTHON_BIN}" 2>/dev/null && return 0
        return 1
    elif command -v python3 >/dev/null 2>&1; then
        command -v python3
    elif command -v python >/dev/null 2>&1; then
        command -v python
    else
        return 1
    fi
}

PYTHON="$(resolve_python)" || { echo "ERROR: python3/python not found"; exit 127; }

case "${MODE}" in
    readonly|safe-effects|side-effects|interactive|sensitive|qualification|all) ;;
    *)
        echo "Usage: $0 [readonly|safe-effects|side-effects|interactive|sensitive|qualification|all]"
        exit 2
        ;;
esac

if [[ -z "${PREFIX:-}" || "${PREFIX}" != *com.termux* ]]; then
    echo "ERROR: this campaign must run inside Termux."
    exit 3
fi

if ! "${PYTHON}" -m pytest --version >/dev/null 2>&1; then
    echo "ERROR: pytest not installed for ${PYTHON}"
    exit 126
fi
if ! "${PYTHON}" -c 'import pytest_asyncio' >/dev/null 2>&1; then
    echo "ERROR: pytest-asyncio not installed for ${PYTHON}"
    echo "Install with: ${PYTHON} -m pip install -e '.[test]'"
    exit 125
fi

VERSION_PREFLIGHT="$(
PYTHONPATH="${PROJECT_ROOT}${PYTHONPATH:+:${PYTHONPATH}}" "${PYTHON}" - <<'PY'
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
if [[ -z "${INSTALLED_VERSION}" ]]; then
    echo "ERROR: termux-api-stc distribution is not installed for ${PYTHON}."
    echo "Install with: ${PYTHON} -m pip install -e '.[test]'"
    exit 123
fi
if [[ "${INSTALLED_VERSION}" != "${RUNTIME_VERSION}" ]]; then
    echo "ERROR: runtime/distribution version mismatch."
    echo "runtime=${RUNTIME_VERSION}"
    echo "distribution=${INSTALLED_VERSION}"
    exit 124
fi

mkdir -p "${RESULT_DIR}"

GIT_COMMIT="$(git -C "${PROJECT_ROOT}" rev-parse HEAD 2>/dev/null || true)"
GIT_BRANCH="$(git -C "${PROJECT_ROOT}" branch --show-current 2>/dev/null || true)"
GIT_STATUS="$(git -C "${PROJECT_ROOT}" status --porcelain=v1 --untracked-files=all 2>/dev/null || true)"

{
    echo "timestamp_utc=${TIMESTAMP}"
    echo "mode=${MODE}"
    echo "project_root=${PROJECT_ROOT}"
    echo "python=${PYTHON}"
    echo "python_version=$(${PYTHON} --version 2>&1)"
    echo "pytest=$(${PYTHON} -m pytest --version 2>&1 | head -1)"
    echo "runtime_version=${RUNTIME_VERSION}"
    echo "distribution_version=${INSTALLED_VERSION}"
    echo "git_commit=${GIT_COMMIT:-UNKNOWN}"
    echo "git_branch=${GIT_BRANCH:-UNKNOWN}"
    if [[ -z "${GIT_STATUS}" ]]; then echo "git_tree=clean"; else echo "git_tree=dirty"; fi
    echo "PREFIX=${PREFIX:-UNKNOWN}"
    echo "TERMUX_VERSION=${TERMUX_VERSION:-UNKNOWN}"
    echo "android_release=$(getprop ro.build.version.release 2>/dev/null || true)"
    echo "android_sdk=$(getprop ro.build.version.sdk 2>/dev/null || true)"
    echo "manufacturer=$(getprop ro.product.manufacturer 2>/dev/null || true)"
    echo "model=$(getprop ro.product.model 2>/dev/null || true)"
    echo "device=$(getprop ro.product.device 2>/dev/null || true)"
    echo "abi=$(getprop ro.product.cpu.abi 2>/dev/null || true)"
    echo
    echo "[git status]"
    printf '%s\n' "${GIT_STATUS:-CLEAN}"
    echo
    echo "[termux-info]"
    command -v termux-info >/dev/null 2>&1 && termux-info 2>&1 || true
    echo
    echo "[termux-api package]"
    dpkg-query -W -f='${Package} ${Version} ${Status}\n' termux-api 2>&1 || true
    echo
    echo "[python packages]"
    "${PYTHON}" -m pip freeze 2>&1 || true
    echo
    echo "[commands]"
    for c in "${PREFIX}"/bin/termux-*; do
        [[ -e "$c" ]] && basename "$c"
    done | sort
} > "${RESULT_DIR}/environment.txt"

case "${MODE}" in
    readonly)
        PYTEST_ARGS=(
            tests/device/test_readonly_conformance.py
            tests/device/test_native_parity.py
            tests/device/test_async_readonly_conformance.py
        )
        ;;
    safe-effects|side-effects)
        export TERMUX_API_STC_ENABLE_SAFE_EFFECTS=1
        PYTEST_ARGS=(tests/device/test_safe_effects.py)
        ;;
    interactive)
        export TERMUX_API_STC_ENABLE_INTERACTIVE=1
        PYTEST_ARGS=(tests/device/test_interactive_actions.py)
        ;;
    sensitive)
        export TERMUX_API_STC_ENABLE_SENSITIVE=1
        PYTEST_ARGS=(tests/device/test_sensitive_actions.py)
        ;;
    qualification)
        export TERMUX_API_STC_ENABLE_SAFE_EFFECTS=1
        PYTEST_ARGS=(
            tests/device/test_readonly_conformance.py
            tests/device/test_native_parity.py
            tests/device/test_async_readonly_conformance.py
            tests/device/test_safe_effects.py
        )
        ;;
    all)
        export TERMUX_API_STC_ENABLE_SAFE_EFFECTS=1
        export TERMUX_API_STC_ENABLE_INTERACTIVE=1
        export TERMUX_API_STC_ENABLE_SENSITIVE=1
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
    echo "runtime_version=${RUNTIME_VERSION}"
    echo "distribution_version=${INSTALLED_VERSION}"
    echo "git_commit=${GIT_COMMIT:-UNKNOWN}"
    echo "git_tree=$([[ -z "${GIT_STATUS}" ]] && echo clean || echo dirty)"
    echo "exit_code=${RC}"
    [[ "${RC}" -eq 0 ]] && echo "status=PASS" || echo "status=FAIL"
} > "${RESULT_DIR}/summary.txt"

(
    cd "${RESULT_DIR}" || exit 1
    sha256sum environment.txt test-output.txt exit-code.txt summary.txt > SHA256SUMS
)

echo
cat "${RESULT_DIR}/summary.txt"
echo "evidence=${RESULT_DIR}"
exit "${RC}"
