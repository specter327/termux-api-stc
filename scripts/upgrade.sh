#!/usr/bin/env bash
set -Eeuo pipefail

# ==========
# Constants definition
# ==========

SCRIPT_DIRECTORY="$(
    cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &&
    pwd
)"

PROJECT_ROOT="$(
    cd -- "${SCRIPT_DIRECTORY}/.." &&
    pwd
)"

PYPI_PROJECT_NAME="termux-api-stc"
DEFAULT_TARGET="both"


# ==========
# Functions definition
# ==========

show_usage() {
    cat <<'EOF'
Usage:
    ./scripts/upgrade.sh
    ./scripts/upgrade.sh github
    ./scripts/upgrade.sh pypi
    ./scripts/upgrade.sh both

Targets:
    github  Update the local Git repository from its remote GitHub origin.
    pypi    Upgrade the locally installed termux-api-stc package from PyPI.
    both    Update both the Git repository and the installed PyPI package.

Default:
    both

Examples:
    ./scripts/upgrade.sh
    ./scripts/upgrade.sh github
    ./scripts/upgrade.sh pypi
    ./scripts/upgrade.sh both

This script DOES NOT publish releases and DOES NOT change the project version.
It only upgrades the local environment from the already published sources.
EOF
}


fail() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}


require_command() {
    local command_name="$1"

    command -v "${command_name}" >/dev/null 2>&1 || \
        fail "Required command not found: ${command_name}"
}


query_local_git_version() {
    git -C "${PROJECT_ROOT}" \
        describe \
        --tags \
        --always \
        --dirty 2>/dev/null || true
}


query_installed_pypi_version() {
    python3 - "${PYPI_PROJECT_NAME}" <<'PY'
from importlib.metadata import PackageNotFoundError, version
import sys

package_name = sys.argv[1]

try:
    print(version(package_name))
except PackageNotFoundError:
    print("not-installed")
PY
}


validate_git_repository() {
    require_command git

    git -C "${PROJECT_ROOT}" \
        rev-parse \
        --is-inside-work-tree >/dev/null 2>&1 || \
        fail "${PROJECT_ROOT} is not a Git repository."

    git -C "${PROJECT_ROOT}" \
        remote \
        get-url \
        origin >/dev/null 2>&1 || \
        fail "Git remote 'origin' is not configured."
}


validate_clean_worktree() {
    if [[ -n "$(
        git -C "${PROJECT_ROOT}" \
            status \
            --porcelain
    )" ]]; then
        fail \
            "The Git working tree contains local changes. " \
            "Commit, stash, or discard them before upgrading."
    fi
}


upgrade_github() {
    local branch
    local before_version
    local after_version

    validate_git_repository
    validate_clean_worktree

    branch="$(
        git -C "${PROJECT_ROOT}" \
            branch \
            --show-current
    )"

    [[ -n "${branch}" ]] || \
        fail "Detached HEAD is not supported."

    before_version="$(query_local_git_version)"

    printf '\n'
    printf 'GitHub repository upgrade\n'
    printf '  Root:   %s\n' "${PROJECT_ROOT}"
    printf '  Branch: %s\n' "${branch}"
    printf '  Before: %s\n' "${before_version:-unknown}"

    git -C "${PROJECT_ROOT}" \
        fetch \
        --prune \
        origin

    git -C "${PROJECT_ROOT}" \
        pull \
        --ff-only \
        origin \
        "${branch}"

    git -C "${PROJECT_ROOT}" \
        fetch \
        --tags \
        --force \
        origin

    after_version="$(query_local_git_version)"

    printf '  After:  %s\n' "${after_version:-unknown}"
}


upgrade_pypi() {
    local before_version
    local after_version

    require_command python3

    before_version="$(query_installed_pypi_version)"

    printf '\n'
    printf 'PyPI package upgrade\n'
    printf '  Package: %s\n' "${PYPI_PROJECT_NAME}"
    printf '  Before:  %s\n' "${before_version}"

    python3 -m pip install \
        --upgrade \
        "${PYPI_PROJECT_NAME}"

    after_version="$(query_installed_pypi_version)"

    printf '  After:   %s\n' "${after_version}"
}


# ==========
# Entry point
# ==========

if [[ $# -gt 1 ]]; then
    show_usage
    exit 2
fi

TARGET="${1:-${DEFAULT_TARGET}}"

case "${TARGET}" in
    github|pypi|both)
        ;;
    -h|--help|help)
        show_usage
        exit 0
        ;;
    *)
        show_usage
        fail "Unknown target: ${TARGET}"
        ;;
esac

printf 'termux-api-stc local upgrade\n'
printf 'Target: %s\n' "${TARGET}"

case "${TARGET}" in
    github)
        upgrade_github
        ;;

    pypi)
        upgrade_pypi
        ;;

    both)
        upgrade_github
        upgrade_pypi
        ;;
esac

printf '\nUpgrade completed successfully.\n'