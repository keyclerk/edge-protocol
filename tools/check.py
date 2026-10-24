# SPDX-License-Identifier: EUPL-1.2
"""Checks this repository holds together: the conformance set parses, every file RELEASE.txt lists has the hash it
lists, and every relative link in the Markdown files points at a file that exists. Standard library only.

    python3 tools/check.py
"""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINK = re.compile(r"\]\(([^)\s]+)\)|(?:src|srcset|href)=\"([^\"]+)\"")


def main() -> int:
    errors = []
    try:
        json.loads((ROOT / "conformance" / "edge.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        errors.append(f"conformance/edge.json does not parse: {e}")
    listed = re.findall(r"^  (\S+)  sha256 ([0-9a-f]{64})$", (ROOT / "RELEASE.txt").read_text(encoding="utf-8"), re.M)
    if not listed:
        errors.append("RELEASE.txt lists no files")
    for name, digest in listed:
        f = ROOT / name
        if not f.is_file():
            errors.append(f"{name}: listed in RELEASE.txt, missing")
        elif hashlib.sha256(f.read_bytes()).hexdigest() != digest:
            errors.append(f"{name}: differs from the hash in RELEASE.txt")
    for md in sorted(ROOT.rglob("*.md")):
        for m in LINK.finditer(md.read_text(encoding="utf-8")):
            target = (m.group(1) or m.group(2)).split("#", 1)[0]
            if not target or re.match(r"^[a-z]+:", target):
                continue
            if not (md.parent / target).exists():
                errors.append(f"{md.relative_to(ROOT).as_posix()}: link to {target}, which does not exist")
    for e in errors:
        print(e)
    print(f"{len(listed)} files checked against RELEASE.txt; {'no' if not errors else len(errors)} problems")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
