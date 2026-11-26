#!/usr/bin/env python3
"""Static QML checks that qmllint's warnings are too quiet about.

Two failure modes shipped in 1.9.0/1.9.1 and neither booted the app visibly:

* a dialog used component names that do not exist (`TButton` instead of
  `DialogButton`) — fatal at load, caught by ``scripts/bootcheck.sh``;
* a dialog used theme tokens that do not exist (`Theme.size()`,
  ``Theme.radiusLg``) — not fatal, but every binding reads ``undefined`` and
  draws nothing.

This script makes the second one loud and deterministic by comparing every
``Theme.<name>`` reference against the properties/functions the singleton
actually declares. It also runs qmllint and treats an unresolved type name as
an error instead of a warning.
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEME = ROOT / "theme" / "Theme.qml"
QMLDIRS = ["surface", "components", "data", "config"]


def theme_tokens():
    source = THEME.read_text()
    names = set(re.findall(r"(?:readonly\s+)?property\s+(?:[\w<>.]+\s+)?(\w+)", source))
    names |= set(re.findall(r"function\s+(\w+)", source))
    return names


def theme_references():
    refs = {}
    for directory in QMLDIRS:
        for path in sorted((ROOT / directory).glob("*.qml")):
            for match in re.finditer(r"Theme\.(\w+)", path.read_text()):
                refs.setdefault(match.group(1), set()).add(path.name)
    return refs


def check_theme():
    tokens = theme_tokens()
    missing = {name: files for name, files in theme_references().items()
               if name not in tokens}
    for name in sorted(missing):
        print(f"theme: Theme.{name} is not declared in theme/Theme.qml "
              f"(used by {', '.join(sorted(missing[name]))})", file=sys.stderr)
    return not missing


def check_qmllint():
    binary = "/usr/lib/qt6/bin/qmllint"
    if not Path(binary).exists():
        print("qmllint: /usr/lib/qt6/bin/qmllint not found", file=sys.stderr)
        return False
    files = []
    for directory in QMLDIRS:
        files += [str(p) for p in sorted((ROOT / directory).glob("*.qml"))]
    result = subprocess.run([binary, *files], capture_output=True, text=True)
    output = result.stdout + result.stderr
    bad = [line for line in output.splitlines()
           if "was not found" in line or "Expected token" in line
           or "is not a type" in line or "syntax error" in line]
    for line in bad:
        print(f"qmllint: {line}", file=sys.stderr)
    return not bad


def main():
    ok = check_theme() & check_qmllint()
    print("qmlcheck OK" if ok else "qmlcheck FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
