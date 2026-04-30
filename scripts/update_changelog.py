"""Generate or extend CHANGELOG.md from conventional commit messages."""

from __future__ import annotations

import re
import subprocess
from datetime import date
from pathlib import Path

CHANGELOG_PATH = Path(__file__).resolve().parent.parent / "CHANGELOG.md"

CONVENTIONAL_RE = re.compile(
    r"^(feat|fix|docs|refactor|test|chore|perf)(\([^)]+\))?:\s+(.*)$"
)
SECTION_TITLES = {
    "feat": "Features",
    "fix": "Fixes",
    "docs": "Docs",
    "refactor": "Refactors",
    "test": "Tests",
    "chore": "Chore",
    "perf": "Performance",
}


def _last_release_tag() -> str | None:
    """Return the most recent annotated tag, or None when no tags exist."""

    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return None
        return result.stdout.strip()
    except Exception:
        return None


def _commits_since(reference: str | None) -> list[str]:
    """Return one-line commit messages since the given reference (or all)."""

    range_spec = f"{reference}..HEAD" if reference else "HEAD"
    result = subprocess.run(
        ["git", "log", range_spec, "--pretty=format:%s"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def _bucketize(messages: list[str]) -> dict[str, list[str]]:
    """Group commit messages by conventional commit type."""

    buckets: dict[str, list[str]] = {key: [] for key in SECTION_TITLES}
    for message in messages:
        match = CONVENTIONAL_RE.match(message)
        if not match:
            continue
        commit_type, scope, description = match.groups()
        scope_text = f" ({scope.strip('()')})" if scope else ""
        buckets[commit_type].append(f"- {description}{scope_text}")
    return buckets


def _format_entry(buckets: dict[str, list[str]]) -> str:
    """Render the changelog markdown entry for the current run."""

    today = date.today().isoformat()
    body = [f"## [{today}]"]
    has_content = False
    for commit_type, items in buckets.items():
        if not items:
            continue
        has_content = True
        body.append("")
        body.append(f"### {SECTION_TITLES[commit_type]}")
        body.extend(items)
    if not has_content:
        return ""
    body.append("")
    return "\n".join(body)


def main() -> None:
    """Append the latest changelog entry to CHANGELOG.md."""

    last = _last_release_tag()
    messages = _commits_since(last)
    if not messages:
        print("No new commits to add.")
        return
    buckets = _bucketize(messages)
    entry = _format_entry(buckets)
    if not entry:
        print("No conventional commits to record.")
        return

    if CHANGELOG_PATH.exists():
        existing = CHANGELOG_PATH.read_text(encoding="utf-8")
    else:
        existing = (
            "# Changelog\n\nGenerated automatically from conventional commits.\n\n"
        )
    CHANGELOG_PATH.write_text(existing + entry + "\n", encoding="utf-8")
    print("CHANGELOG.md updated.")


if __name__ == "__main__":
    main()
