#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIRECTORY="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIRECTORY}/.." && pwd)"

PYPROJECT_FILE="${PROJECT_ROOT}/pyproject.toml"
PACKAGE_INIT_FILE="${PROJECT_ROOT}/termux_api/__init__.py"
PUBLISH_SCRIPT="${SCRIPT_DIRECTORY}/publish.sh"
PYPI_PROJECT_NAME="termux-api-stc"

show_usage() {
    cat <<'USAGE'
Usage:
    ./scripts/upgrade.sh VERSION github [commit-message]
    ./scripts/upgrade.sh VERSION pypi
    ./scripts/upgrade.sh VERSION both [commit-message]

Examples:
    ./scripts/upgrade.sh 2.1.0 github
    ./scripts/upgrade.sh 2.1.0 pypi
    ./scripts/upgrade.sh 2.1.0 both
    ./scripts/upgrade.sh 2.1.0 both "Release termux-api-stc 2.1.0"

Behavior:
    1. Validates VERSION.
    2. Updates [project].version in pyproject.toml.
    3. Updates __version__ in termux_api/__init__.py.
    4. Validates the Python package.
    5. Delegates publication to scripts/publish.sh.
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

validate_version() {
    local version="$1"
    python3 - "$version" <<'PY'
import re
import sys

version = sys.argv[1]
pattern = re.compile(r'^[0-9]+(?:\.[0-9]+){2}(?:(?:a|b|rc)[0-9]+|\.post[0-9]+|\.dev[0-9]+)?$')
if pattern.fullmatch(version) is None:
    raise SystemExit(
        "Invalid version. Examples: 2.1.0, 2.1.0a1, 2.1.0b1, "
        "2.1.0rc1, 2.1.0.post1, 2.1.0.dev1"
    )
PY
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

write_version() {
    local version="$1"
    python3 - "$PYPROJECT_FILE" "$PACKAGE_INIT_FILE" "$version" <<'PY'
from pathlib import Path
import re
import sys

pyproject_path = Path(sys.argv[1])
init_path = Path(sys.argv[2])
version = sys.argv[3]

pyproject_text = pyproject_path.read_text(encoding="utf-8")
updated_pyproject, count = re.subn(
    r'(?ms)(^\[project\].*?^version\s*=\s*")[^"]+(")',
    rf'\g<1>{version}\g<2>',
    pyproject_text,
    count=1,
)
if count != 1:
    raise SystemExit("Unable to update [project].version in pyproject.toml")

init_text = init_path.read_text(encoding="utf-8")
updated_init, count = re.subn(
    r'^__version__\s*=\s*["\'][^"\']+["\']',
    f'__version__ = "{version}"',
    init_text,
    count=1,
    flags=re.MULTILINE,
)
if count != 1:
    raise SystemExit("Unable to update __version__ in termux_api/__init__.py")

pyproject_path.write_text(updated_pyproject, encoding="utf-8")
init_path.write_text(updated_init, encoding="utf-8")
PY
}

if [[ $# -lt 2 || $# -gt 3 ]]; then
    show_usage
    exit 2
fi

require_command python3

VERSION="$1"
TARGET="$2"
COMMIT_MESSAGE="${3:-Release termux-api-stc $VERSION}"

case "$TARGET" in
    github|pypi|both) ;;
    *) show_usage; fail "Unknown destination: $TARGET" ;;
esac

validate_version "$VERSION"

[[ -f "$PYPROJECT_FILE" ]] || fail "Missing $PYPROJECT_FILE"
[[ -f "$PACKAGE_INIT_FILE" ]] || fail "Missing $PACKAGE_INIT_FILE"
[[ -x "$PUBLISH_SCRIPT" ]] || fail "$PUBLISH_SCRIPT does not exist or is not executable."

PROJECT_NAME="$(read_project_field name)"
[[ "$PROJECT_NAME" == "$PYPI_PROJECT_NAME" ]] || \
    fail "pyproject.toml must contain [project].name = \"$PYPI_PROJECT_NAME\". Current value: \"$PROJECT_NAME\""

CURRENT_VERSION="$(read_project_field version)"
[[ "$CURRENT_VERSION" != "$VERSION" ]] || fail "Project is already at version $VERSION."

BACKUP_DIRECTORY="$(mktemp -d)"
cp -- "$PYPROJECT_FILE" "$BACKUP_DIRECTORY/pyproject.toml"
cp -- "$PACKAGE_INIT_FILE" "$BACKUP_DIRECTORY/__init__.py"

cleanup_backup() {
    rm -rf "$BACKUP_DIRECTORY"
}

restore_versions() {
    cp -- "$BACKUP_DIRECTORY/pyproject.toml" "$PYPROJECT_FILE"
    cp -- "$BACKUP_DIRECTORY/__init__.py" "$PACKAGE_INIT_FILE"
}

handle_error() {
    local exit_code=$?
    printf 'Upgrade failed. Restoring version files.\n' >&2
    restore_versions
    cleanup_backup
    exit "$exit_code"
}

trap handle_error ERR
trap cleanup_backup EXIT

write_version "$VERSION"
python3 -m compileall -q "${PROJECT_ROOT}/termux_api"

"$PUBLISH_SCRIPT" "$TARGET" "$COMMIT_MESSAGE"

trap - ERR
printf 'Upgrade completed successfully: %s -> %s\n' "$CURRENT_VERSION" "$VERSION"