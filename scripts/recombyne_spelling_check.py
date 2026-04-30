#!/usr/bin/env python3
"""Pre-commit hook that blocks misspellings of the project name.

The correct spelling is always "Recombyne". This hook runs over every staged
file and refuses the commit if it finds a violation. Files may opt out by
including the literal token ``recombyne-spelling-allow`` somewhere in their
contents (for example, this hook itself does so).

# recombyne-spelling-allow
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PATTERN = re.compile(r"recombine", re.IGNORECASE)
ALLOWLIST_TOKEN = "recombyne-spelling-allow"
ALLOWED_SUFFIXES = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".md",
    ".yml",
    ".yaml",
    ".json",
    ".html",
    ".css",
    ".sh",
    ".txt",
    ".env",
    ".env.example",
    "",
}


def file_should_be_checked(path: Path) -> bool:
    """Return True for text files we want to lint for the spelling rule."""

    if path.is_dir():
        return False
    if not path.exists():
        return False
    if path.suffix in ALLOWED_SUFFIXES:
        return True
    return False


def main(argv: list[str]) -> int:
    """Exit non-zero when any staged file contains the disallowed spelling."""

    failures: list[str] = []
    for raw in argv[1:]:
        path = Path(raw)
        if not file_should_be_checked(path):
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if ALLOWLIST_TOKEN in content:
            continue
        if PATTERN.search(content):
            failures.append(str(path))

    if failures:
        print(
            "Error: Found 'recombine' in staged files. The correct spelling is "
            "'Recombyne'. Please fix before committing."
        )
        for failure in failures:
            print(f"  - {failure}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
