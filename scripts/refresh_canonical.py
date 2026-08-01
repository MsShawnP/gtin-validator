#!/usr/bin/env python3
"""Refresh this repo's vendored canon from the cinderhaven-data-platform.

Copies the platform's generated artifacts into reference/:
  - canonical_values.json  (the machine-readable canon; tests read it)
  - supersedes.txt         (retired-figure list; the drift gate reads it)

The platform generates both on every `verify_canonical.py` run. This is a
DEV-TIME tool: run it after the canon changes, review the diff, commit the
vendored copies. It is NOT part of CI (the vendored files are committed).

Platform location resolution, in order:
  1. $CINDERHAVEN_PLATFORM (path to the platform repo root)
  2. common relative layouts from this repo
Fails loudly if it can't find the platform — never silently vendors nothing.
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEST = REPO / "reference"
ARTIFACTS = ("canonical_values.json", "supersedes.txt")

CANDIDATES = [
    os.environ.get("CINDERHAVEN_PLATFORM", ""),
    REPO / ".." / ".." / "active datasources" / "cinderhaven-data-platform",
    REPO / ".." / "cinderhaven-data-platform",
    REPO / ".." / ".." / "cinderhaven-data-platform",
]


def find_platform() -> Path:
    for c in CANDIDATES:
        if not c:
            continue
        p = Path(c).expanduser()
        if (p / "reference" / "canonical_values.yml").exists():
            return p.resolve()
    print(
        "ERROR: could not locate cinderhaven-data-platform. Set "
        "CINDERHAVEN_PLATFORM to its repo root and retry.",
        file=sys.stderr,
    )
    sys.exit(1)


def main() -> int:
    platform = find_platform()
    src = platform / "reference"
    missing = [a for a in ARTIFACTS if not (src / a).exists()]
    if missing:
        print(
            f"ERROR: {platform.name} has not generated {missing}. Run its "
            f"scripts/verify_canonical.py first (it emits both artifacts).",
            file=sys.stderr,
        )
        return 1
    DEST.mkdir(parents=True, exist_ok=True)
    for a in ARTIFACTS:
        shutil.copyfile(src / a, DEST / a)
        print(f"  vendored {a}  <-  {platform.name}")
    print("done. Review `git diff reference/` and commit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
