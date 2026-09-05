from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def summarize(path: Path) -> str:
    if not path.exists():
        return "tests=UNKNOWN failures=UNKNOWN errors=UNKNOWN skipped=UNKNOWN"
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))

    def total(name: str) -> int:
        return sum(int(suite.attrib.get(name, 0)) for suite in suites)

    return (
        f"tests={total('tests')} failures={total('failures')} "
        f"errors={total('errors')} skipped={total('skipped')}"
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: junit_summary.py JUNIT_XML")
    print(summarize(Path(sys.argv[1])))
