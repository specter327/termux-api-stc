#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIRECTORY="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIRECTORY}/.." && pwd)"

PYPROJECT_FILE="${PROJECT_ROOT}/pyproject.toml"
PACKAGE_DIRECTORY="${PROJECT_ROOT}/termux_api_stc"
PACKAGE_INIT_FILE="${PACKAGE_DIRECTORY}/__init__.py"
DIST_DIRECTORY="${PROJECT_ROOT}/dist"
BUILD_DIRECTORY="${PROJECT_ROOT}/build"
PYPI_PROJECT_NAME="termux-api-stc"

show_usage() {
    cat <<'USAGE'
Usage:
    ./scripts/publish.sh github [commit-message]
    ./scripts/publish.sh pypi
    ./scripts/publish.sh both [commit-message]

Destinations:
    github  Commit, tag and push the current version to GitHub.
    pypi    Build and upload the current version to PyPI.
    both    Publish the current version to GitHub and PyPI.

Important:
    - This script does NOT change the project version.
    - PyPI does not allow replacing an already published version.
      Increment the project version before publishing a replacement release.
USAGE
}

fail() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

require_command() {
    local command_name="$1"
    command -v "$command_name" >/dev/null 2>&1 || fail "Required command not found: $command_name"
}

read_project_field() {
    local field="$1"
    python3 - "$PYPROJECT_FILE" "$field" <<'PY'
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
field = sys.argv[2]
text = path.read_text(encoding="utf-8")
match = re.search(rf'(?ms)^\[project\].*?^{re.escape(field)}\s*=\s*"([^"]+)"', text)
if match is None:
    raise SystemExit(f"Unable to read [project].{field} from pyproject.toml")
print(match.group(1))
PY
}

validate_project() {
    require_command python3
    [[ -f "$PYPROJECT_FILE" ]] || fail "Missing $PYPROJECT_FILE"
    [[ -d "$PACKAGE_DIRECTORY" ]] || fail "Missing $PACKAGE_DIRECTORY"
    [[ -f "$PACKAGE_INIT_FILE" ]] || fail "Missing $PACKAGE_INIT_FILE"

    local project_name
    project_name="$(read_project_field name)"
    [[ "$project_name" == "$PYPI_PROJECT_NAME" ]] || \
        fail "pyproject.toml must contain [project].name = \"$PYPI_PROJECT_NAME\". Current value: \"$project_name\""
}

validate_python_sources() {
    python3 -m compileall -q "$PACKAGE_DIRECTORY" || fail "Python source validation failed."
}

validate_build_dependencies() {
    python3 -c "import build" >/dev/null 2>&1 || \
        fail "Missing Python package 'build'. Install with: python3 -m pip install --upgrade build"
    python3 -c "import twine" >/dev/null 2>&1 || \
        fail "Missing Python package 'twine'. Install with: python3 -m pip install --upgrade twine"
}

clean_build_artifacts() {
    rm -rf "$DIST_DIRECTORY" "$BUILD_DIRECTORY"
    find "$PROJECT_ROOT" -maxdepth 1 -type d -name '*.egg-info' -exec rm -rf {} +
}

build_distribution() {
    validate_build_dependencies
    validate_python_sources
    clean_build_artifacts
    (cd "$PROJECT_ROOT" && python3 -m build)
    python3 -m twine check "$DIST_DIRECTORY"/*
}

validate_git_repository() {
    require_command git
    git -C "$PROJECT_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1 || fail "$PROJECT_ROOT is not a Git repository."
    git -C "$PROJECT_ROOT" remote get-url origin >/dev/null 2>&1 || fail "Git remote 'origin' is not configured."
}

publish_github() {
    local version="$1"
    local commit_message="$2"
    local branch

    validate_git_repository
    branch="$(git -C "$PROJECT_ROOT" branch --show-current)"
    [[ -n "$branch" ]] || fail "Detached HEAD is not supported."

    git -C "$PROJECT_ROOT" add -A
    if ! git -C "$PROJECT_ROOT" diff --cached --quiet; then
        git -C "$PROJECT_ROOT" commit -m "$commit_message"
    else
        printf 'Git: no changes to commit.\n'
    fi

    git -C "$PROJECT_ROOT" push origin "$branch"

    if git -C "$PROJECT_ROOT" rev-parse "refs/tags/v$version" >/dev/null 2>&1; then
        printf 'Git: tag v%s already exists locally.\n' "$version"
    else
        git -C "$PROJECT_ROOT" tag -a "v$version" -m "Release v$version"
    fi

    if git -C "$PROJECT_ROOT" ls-remote --exit-code --tags origin "refs/tags/v$version" >/dev/null 2>&1; then
        printf 'GitHub: tag v%s already exists remotely.\n' "$version"
    else
        git -C "$PROJECT_ROOT" push origin "v$version"
    fi
}

publish_pypi() {
    python3 -m twine upload "$DIST_DIRECTORY"/*
}

if [[ $# -lt 1 || $# -gt 2 ]]; then
    show_usage
    exit 2
fi

TARGET="$1"
COMMIT_MESSAGE="${2:-Publish termux-api-stc}"

case "$TARGET" in
    github|pypi|both) ;;
    *) show_usage; fail "Unknown destination: $TARGET" ;;
esac

validate_project
VERSION="$(read_project_field version)"

printf 'Project root: %s\n' "$PROJECT_ROOT"
printf 'Distribution: %s\n' "$PYPI_PROJECT_NAME"
printf 'Version:      %s\n' "$VERSION"
printf 'Target:       %s\n' "$TARGET"

case "$TARGET" in
    github)
        validate_python_sources
        publish_github "$VERSION" "$COMMIT_MESSAGE"
        ;;
    pypi)
        build_distribution
        publish_pypi
        ;;
    both)
        build_distribution
        publish_github "$VERSION" "$COMMIT_MESSAGE"
        publish_pypi
        ;;
esac

printf 'Publication completed successfully.\n'