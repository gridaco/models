"""Build versioned snapshots of `catalogue/` for GitHub Releases.

A snapshot is everything in `catalogue/`, published under a version tag:

    v<schema major>.<YYYYMMDD>.<n>     e.g. v1.20261012.0

The major is the catalogue's schema version, so a semver range such as `^1` never crosses a
breaking change. The date is the UTC commit date of the snapshot, and `n` counts earlier
snapshots from the same day.

Usage:
    uv run scripts/release.py digest
    uv run scripts/release.py version
    uv run scripts/release.py build --version v1.20261012.0 --out dist
    uv run scripts/release.py notes --version v1.20261012.0 --previous previous/

`digest` prints a fingerprint of the catalogue's content; the release workflow publishes only
when it differs from the latest release's. `build` writes the release assets, and builds the
same bytes from the same commit. `notes` compares against the previous release's assets.
"""

from __future__ import annotations

import argparse
import datetime
import gzip
import hashlib
import io
import json
import re
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
CATALOGUE = ROOT / "catalogue"
REPOSITORY = "https://github.com/gridaco/models"
NAME = "grida-models"

# The catalogue's schema major version. Both schema `$id`s end in `-v<major>.json`;
# a breaking change to either bumps it.
SCHEMA_MAJOR = 1

# Files published individually, so `releases/latest/download/<name>` always resolves.
ASSETS = {
    "facts.json": "facts.json",
    "labs.json": "labs.json",
    "facts.schema.json": "schemas/facts.schema.json",
    "labs.schema.json": "schemas/labs.schema.json",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def catalogue_files(root: Path = CATALOGUE) -> dict[str, bytes]:
    """Every file in the catalogue, keyed by its path relative to it, in path order."""
    files = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file() and not path.name.startswith(".")
    }
    return dict(sorted(files.items()))


def digest(files: dict[str, bytes]) -> str:
    """A fingerprint of the catalogue's content: file paths and bytes, nothing else."""
    lines = "".join(f"{sha256(data)}  {name}\n" for name, data in sorted(files.items()))
    return "sha256:" + sha256(lines.encode())


def next_version(tags: list[str], day: datetime.date, major: int = SCHEMA_MAJOR) -> str:
    """The next tag for a snapshot from `day`, always greater than every existing tag.

    A commit can carry an older date than the latest release (for example after a rebase);
    its snapshot then takes the latest release's date, so versions only ever increase.
    """
    released = [
        (int(match.group(1)), int(match.group(2)))
        for tag in tags
        if (match := re.fullmatch(rf"v{major}\.(\d{{8}})\.(\d+)", tag))
    ]
    date = max([int(f"{day:%Y%m%d}")] + [d for d, _ in released])
    counter = max((n for d, n in released if d == date), default=-1) + 1
    return f"v{major}.{date}.{counter}"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()


def commit_info(rev: str = "HEAD") -> tuple[str, datetime.datetime]:
    sha, stamp = git("log", "-1", "--format=%H %ct", rev).split()
    return sha, datetime.datetime.fromtimestamp(int(stamp), datetime.UTC)


def schema_major(files: dict[str, bytes]) -> set[int]:
    """The major version each schema `$id` declares."""
    majors = set()
    for name in ("schemas/facts.schema.json", "schemas/labs.schema.json"):
        match = re.search(r"-v(\d+)\.json$", json.loads(files[name])["$id"])
        majors.add(int(match.group(1)) if match else -1)
    return majors


def manifest(version: str, commit: str, created: datetime.datetime, files: dict[str, bytes]) -> dict[str, Any]:
    facts = json.loads(files["facts.json"])
    cards = sum(len(table) for section, table in facts.items() if not section.endswith(".operation"))
    return {
        "name": NAME,
        "version": version,
        "schema_version": SCHEMA_MAJOR,
        "commit": commit,
        "created": created.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": f"{REPOSITORY}/tree/{commit}/catalogue",
        "digest": digest(files),
        "counts": {"cards": cards, "labs": len(json.loads(files["labs.json"]))},
        "files": {name: {"sha256": sha256(data), "bytes": len(data)} for name, data in files.items()},
    }


def archive_members(prefix: str, files: dict[str, bytes], extra: dict[str, bytes]) -> list[tuple[str, bytes]]:
    members = {**{f"catalogue/{name}": data for name, data in files.items()}, **extra}
    return [(f"{prefix}/{name}", data) for name, data in sorted(members.items())]


def tar_gz(members: list[tuple[str, bytes]], mtime: int) -> bytes:
    """A gzipped tarball with fixed ownership, modes, order, and times."""
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.PAX_FORMAT) as tar:
        for name, data in members:
            info = tarfile.TarInfo(name)
            info.size, info.mtime, info.mode = len(data), mtime, 0o644
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            tar.addfile(info, io.BytesIO(data))
    out = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=out, mtime=mtime) as gz:
        gz.write(raw.getvalue())
    return out.getvalue()


def zip_bytes(members: list[tuple[str, bytes]], when: datetime.datetime) -> bytes:
    """A zip archive with fixed order, times, and permissions."""
    out = io.BytesIO()
    stamp = (max(when.year, 1980), when.month, when.day, when.hour, when.minute, when.second)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in members:
            info = zipfile.ZipInfo(name, date_time=stamp)
            info.external_attr = 0o644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    return out.getvalue()


def build(version: str, commit: str, created: datetime.datetime, files: dict[str, bytes]) -> dict[str, bytes]:
    """The release assets, keyed by asset name."""
    meta = (json.dumps(manifest(version, commit, created, files), indent=2) + "\n").encode()
    prefix = f"{NAME}-{version}"
    members = archive_members(prefix, files, {"LICENSE": (ROOT / "LICENSE").read_bytes(), "manifest.json": meta})
    assets = {name: files[path] for name, path in ASSETS.items()}
    assets["manifest.json"] = meta
    assets[f"{prefix}.tar.gz"] = tar_gz(members, int(created.timestamp()))
    assets[f"{prefix}.zip"] = zip_bytes(members, created)
    sums = "".join(f"{sha256(data)}  {name}\n" for name, data in sorted(assets.items()))
    assets["SHA256SUMS"] = sums.encode()
    return assets


def cards_by_key(facts: dict[str, Any]) -> dict[str, Any]:
    """Cards keyed by how release notes name them: `id` (section)."""
    keyed = {}
    for section, table in facts.items():
        if section.endswith(".operation"):
            keyed[f"`{section}`"] = table
        else:
            keyed.update({f"`{card_id}` ({section})": card for card_id, card in table.items()})
    return keyed


def diff(before: dict[str, Any], after: dict[str, Any]) -> tuple[list[str], list[str], list[str]]:
    added = sorted(after.keys() - before.keys())
    removed = sorted(before.keys() - after.keys())
    changed = sorted(k for k in before.keys() & after.keys() if before[k] != after[k])
    return added, removed, changed


def notes(version: str, current: dict[str, Any], previous: dict[str, Any] | None) -> str:
    """Release notes: what this snapshot changes since the previous release."""
    download = f"{REPOSITORY}/releases/download/{version}"
    counts = current["counts"]
    lines = [
        f"Catalogue snapshot `{version}` from [`{current['commit'][:12]}`]({REPOSITORY}/commit/{current['commit']}): "
        f"{counts['cards']} model cards, {counts['labs']} labs. Schema version {current['schema_version']}.",
        "",
    ]
    if previous is None:
        lines += ["First release.", ""]
    else:
        lines += [f"## Changes since `{previous['manifest']['version']}`", ""]
        sections = [
            ("models", cards_by_key(previous["facts"]), cards_by_key(current["facts"])),
            ("labs", *({f"`{k}`": v for k, v in labs.items()} for labs in (previous["labs"], current["labs"]))),
        ]
        any_change = False
        for label, before, after in sections:
            for verb, keys in zip(("Added", "Removed", "Changed"), diff(before, after)):
                if keys:
                    any_change = True
                    lines.append(f"- {verb} {label} ({len(keys)}): " + ", ".join(keys))
        old_files, new_files = previous["manifest"]["files"], current["files"]
        for name in ("schemas/facts.schema.json", "schemas/labs.schema.json"):
            if old_files.get(name, {}).get("sha256") != new_files[name]["sha256"]:
                any_change = True
                lines.append(f"- Schema changed: `{name}`")
        covered = {"facts.json", "labs.json", "schemas/facts.schema.json", "schemas/labs.schema.json"}
        others = [
            name
            for name in sorted(old_files.keys() | new_files.keys())
            if name not in covered and old_files.get(name) != new_files.get(name)
        ]
        if others:
            any_change = True
            lines.append("- Other files changed: " + ", ".join(f"`{name}`" for name in others))
        if not any_change:
            lines.append("- No content changes.")
        lines.append("")
    lines += [
        "## Download",
        "",
        f"- Model facts: [`facts.json`]({download}/facts.json), labs: [`labs.json`]({download}/labs.json), "
        f"schemas: [`facts.schema.json`]({download}/facts.schema.json), [`labs.schema.json`]({download}/labs.schema.json)",
        f"- Everything, logos included: [`{NAME}-{version}.tar.gz`]({download}/{NAME}-{version}.tar.gz) or "
        f"[`.zip`]({download}/{NAME}-{version}.zip)",
        f"- Always the newest snapshot: `{REPOSITORY}/releases/latest/download/facts.json`",
        "- Verify: download `SHA256SUMS` with the assets and run `sha256sum -c SHA256SUMS --ignore-missing`",
        "",
        "Catalogue data is MIT licensed. Lab logos are trademarks of their owners and are not covered by "
        "that license; each lab's entry in `labs.json` links its source and brand guidelines.",
    ]
    return "\n".join(lines) + "\n"


def load_previous(directory: Path) -> dict[str, Any] | None:
    paths = {name: directory / name for name in ("manifest.json", "facts.json", "labs.json")}
    if not all(path.exists() for path in paths.values()):
        return None
    return {name.removesuffix(".json"): json.loads(path.read_text()) for name, path in paths.items()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("digest", help="print the catalogue's content fingerprint")
    commands.add_parser("version", help="print the next version tag for HEAD")
    build_cmd = commands.add_parser("build", help="write the release assets")
    build_cmd.add_argument("--version", required=True)
    build_cmd.add_argument("--out", type=Path, required=True)
    notes_cmd = commands.add_parser("notes", help="print release notes")
    notes_cmd.add_argument("--version", required=True)
    notes_cmd.add_argument("--previous", type=Path, help="directory with the previous release's assets")
    args = parser.parse_args(argv)

    files = catalogue_files()
    if schema_major(files) != {SCHEMA_MAJOR}:
        print(f"schema $ids do not all declare v{SCHEMA_MAJOR}; update SCHEMA_MAJOR", file=sys.stderr)
        return 1
    if args.command == "digest":
        print(digest(files))
    elif args.command == "version":
        tags = git("tag", "--list", f"v{SCHEMA_MAJOR}.*").split()
        print(next_version(tags, commit_info()[1].date()))
    elif args.command == "build":
        commit, created = commit_info()
        args.out.mkdir(parents=True, exist_ok=True)
        for name, data in build(args.version, commit, created, files).items():
            (args.out / name).write_bytes(data)
            print(f"{args.out / name}")
    elif args.command == "notes":
        commit, created = commit_info()
        current = manifest(args.version, commit, created, files)
        current["facts"], current["labs"] = json.loads(files["facts.json"]), json.loads(files["labs.json"])
        previous = load_previous(args.previous) if args.previous else None
        sys.stdout.write(notes(args.version, current, previous))
    return 0


if __name__ == "__main__":
    sys.exit(main())
