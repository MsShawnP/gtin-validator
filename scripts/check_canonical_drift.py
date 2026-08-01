#!/usr/bin/env python3
"""Canonical drift gate.

Fails the build if any retired Cinderhaven figure/string appears in tracked
source or rendered output. The retired tokens are read from the vendored
reference/supersedes.txt (generated from the cinderhaven-data-platform canon by
verify_canonical.py, copied here by scripts/refresh_canonical.py).

Excluded from the scan:
  - the canon/supersedes files themselves,
  - history / audit / decision docs (they cite retired figures BY DESIGN),
  - per-repo legitimate uses listed in .canonical-allowlist.

A retired figure can never deploy again: if this exits non-zero, a superseded
value slipped into a live surface. Fix the value (reconcile to
reference/canonical_values.json) or, if the use is legitimately historical,
allowlist it.

Usage:  python scripts/check_canonical_drift.py
Exit:   0 = clean, 1 = drift found, 2 = misconfigured (no supersedes.txt).
"""
from __future__ import annotations

import fnmatch
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUPERSEDES = ROOT / "reference" / "supersedes.txt"
ALLOWLIST = ROOT / ".canonical-allowlist"

# Files that legitimately contain retired figures as history / provenance and
# are never a deployed surface. Matched by BASENAME anywhere in the tree
# (a project's history/decision/audit logs cite retired figures by design).
EXCLUDE_BASENAMES = {
    "supersedes.txt",
    "canonical_values.json",
    "canonical_values.yml",
    "CINDERHAVEN_CANONICAL.md",
    "DECISIONS.md",
    "HANDOFF.md",
    "FAILURES.md",
    "PLAN.md",
    "canonical_propagation.md",
    "data_generation_log.md",
    "check_canonical_drift.py",
    "refresh_canonical.py",
    ".canonical-allowlist",
}
EXCLUDE_BASENAME_GLOBS = [
    "AUDIT*.md", "*-AUDIT*.md", "TRIAGE*.md", "RE-AUDIT*.md", "FIX-LOG*.md",
    "*SUPERSEDE*", "*.min.js", "*.min.css", "*.map",
]

# Directory parts never scanned even if a stray file is tracked.
SKIP_DIR_PARTS = {
    ".git", "node_modules", ".venv", "venv", "env", "renv", "__pycache__",
    ".claude", ".pytest_cache", ".mypy_cache",
}

MAX_BYTES = 2_000_000  # skip anything larger (data dumps, binaries)


def load_tokens() -> list[str]:
    if not SUPERSEDES.exists():
        print(
            f"ERROR: {SUPERSEDES.relative_to(ROOT)} not found. The drift gate "
            f"cannot run without the retired-token list. Run "
            f"scripts/refresh_canonical.py to vendor it from the platform.",
            file=sys.stderr,
        )
        sys.exit(2)
    tokens = []
    for line in SUPERSEDES.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            tokens.append(line)
    if not tokens:
        print("ERROR: supersedes.txt has no tokens — refusing to pass a gate "
              "that checks nothing.", file=sys.stderr)
        sys.exit(2)
    return tokens


def load_allowlist() -> tuple[list[str], list[tuple[str, str]]]:
    """Return (file_globs_to_skip, [(token, path_glob), ...])."""
    file_globs: list[str] = []
    token_excepts: list[tuple[str, str]] = []
    if not ALLOWLIST.exists():
        return file_globs, token_excepts
    for raw in ALLOWLIST.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        # "TOKEN @ path/glob" excepts one token in matching files;
        # a bare "path/glob" skips the whole file.
        if " @ " in line:
            tok, glob = line.split(" @ ", 1)
            token_excepts.append((tok.strip(), glob.strip()))
        else:
            file_globs.append(line)
    return file_globs, token_excepts


def tracked_files() -> list[str]:
    out = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files"],
        capture_output=True, text=True, check=True,
    )
    return [p for p in out.stdout.splitlines() if p]


def _glob_match(path: str, glob: str) -> bool:
    """True if `glob` matches the full posix path or its basename. fnmatch's
    `*` spans `/`, so a path glob like 'a/research/*' also matches deeper files."""
    name = Path(path).name
    return fnmatch.fnmatch(path, glob) or fnmatch.fnmatch(name, glob)


def excluded(path: str, extra_globs: list[str]) -> bool:
    if set(Path(path).parts) & SKIP_DIR_PARTS:
        return True
    name = Path(path).name
    if name in EXCLUDE_BASENAMES:
        return True
    if any(fnmatch.fnmatch(name, g) for g in EXCLUDE_BASENAME_GLOBS):
        return True
    if any(_glob_match(path, g) for g in extra_globs):
        return True
    return False


def main() -> int:
    tokens = load_tokens()
    skip_globs, token_excepts = load_allowlist()
    hits: list[str] = []

    for rel in tracked_files():
        if excluded(rel, skip_globs):
            continue
        p = ROOT / rel
        try:
            if not p.is_file() or p.stat().st_size > MAX_BYTES:
                continue
            text = p.read_text(encoding="utf-8", errors="strict")
        except (UnicodeDecodeError, OSError):
            continue  # binary or unreadable — not a text surface
        for tok in tokens:
            if tok in text:
                if any(t == tok and _glob_match(rel, g)
                       for t, g in token_excepts):
                    continue
                for i, ln in enumerate(text.splitlines(), 1):
                    if tok in ln:
                        hits.append(f"  {rel}:{i}: [{tok}]  {ln.strip()[:100]}")

    if hits:
        print("CANONICAL DRIFT — retired figures found in live surfaces:\n")
        print("\n".join(hits))
        print(f"\n{len(hits)} hit(s). Reconcile to reference/canonical_values.json, "
              f"or allowlist a legitimate historical use in .canonical-allowlist.")
        return 1
    print(f"canonical drift gate: clean ({len(tokens)} retired tokens checked).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
