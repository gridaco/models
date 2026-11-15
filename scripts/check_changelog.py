"""Require a schema changelog update alongside a pull request's schema changes.

This checks file coverage, not whether the prose fully explains a contract change.
Consumer-visible validator or generator changes still need contributor review.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHANGELOG = "catalogue/SCHEMA_CHANGELOG.md"


def git(repo: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(repo), *args], stderr=subprocess.PIPE)


def contents(repo: Path, revision: str, path: str) -> bytes | None:
    if path not in git(repo, "ls-tree", "-r", "--name-only", "-z", revision, "--", path).decode().split("\0"):
        return None
    return git(repo, "show", f"{revision}:{path}")


def equivalent(before, after) -> bool:
    # JSON booleans differ from numbers, even though Python's True equals 1.
    if isinstance(before, bool) != isinstance(after, bool):
        return False
    if isinstance(before, dict) and isinstance(after, dict):
        return before.keys() == after.keys() and all(equivalent(before[key], after[key]) for key in before)
    if isinstance(before, list) and isinstance(after, list):
        return len(before) == len(after) and all(equivalent(a, b) for a, b in zip(before, after))
    return before == after


def check(repo: Path, base: str, head: str) -> str | None:
    for revision in (base, head):
        if not re.fullmatch(r"[0-9a-f]{40}", revision):
            raise ValueError("base and head must be exact 40-character commit SHAs")
        git(repo, "rev-parse", "--verify", f"{revision}^{{commit}}")

    # Match the PR's own changes, not unrelated commits added to the base branch
    # since the PR diverged. Main-only changelog edits cannot cover this PR.
    base = git(repo, "merge-base", base, head).decode().strip()

    # Treat a rename as a deletion and addition so moving a schema out of this
    # directory cannot hide the contract change.
    changed = git(repo, "diff", "--no-renames", "--name-only", "-z", base, head, "--").decode().split("\0")
    schema_changed = False
    for path in changed:
        if not (path.startswith("catalogue/schemas/") and path.endswith(".json")):
            continue
        before, after = contents(repo, base, path), contents(repo, head, path)
        # Formatting and object-key order do not change the JSON contract.
        # Descriptions remain part of the comparison because they can define
        # field meanings even when structural validation stays the same.
        try:
            previous = json.loads(before, parse_float=Decimal) if before is not None else None
            current = json.loads(after, parse_float=Decimal) if after is not None else None
        except ValueError as exc:
            raise ValueError(f"Cannot read schema {path}: {exc}") from exc
        if before is None or after is None or not equivalent(previous, current):
            schema_changed = True
    if not schema_changed:
        return None

    before, after = contents(repo, base, CHANGELOG), contents(repo, head, CHANGELOG)
    normalized = b"".join((after or b"").split())
    if not normalized or normalized == b"".join((before or b"").split()):
        return f"Schema files changed: update {CHANGELOG} with the contract change, compatibility and migration impact."
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    args = parser.parse_args()
    try:
        error = check(ROOT, args.base, args.head)
    except (ValueError, subprocess.CalledProcessError) as exc:
        print(f"Cannot compare schema changelog coverage: {exc}", file=sys.stderr)
        return 1
    if error:
        print(error, file=sys.stderr)
        return 1
    print("ok: schema changelog coverage")
    return 0


if __name__ == "__main__":
    sys.exit(main())
