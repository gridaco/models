"""scripts/release.py builds versioned, reproducible snapshots of catalogue/."""

from __future__ import annotations

import copy
import datetime
import hashlib
import io
import json
import tarfile
import zipfile

import pytest

import release

FILES = release.catalogue_files()
WHEN = datetime.datetime(2026, 10, 12, 8, 30, tzinfo=datetime.UTC)
DAY = WHEN.date()
COMMIT = "0" * 40


def test_schemas_declare_the_release_major():
    assert release.schema_major(FILES) == {release.SCHEMA_MAJOR}


@pytest.mark.parametrize(
    "tags, expected",
    [
        ([], "v1.20261012.0"),
        (["v1.20261012.0"], "v1.20261012.1"),
        (["v1.20261012.0", "v1.20261012.3"], "v1.20261012.4"),
        (["v1.20261011.5", "v2.20261012.0", "v1.20261012.x"], "v1.20261012.0"),
        (["v1.20261013.0"], "v1.20261013.1"),  # an older commit never lowers the version
    ],
)
def test_next_version_counts_releases_of_the_same_day(tags, expected):
    assert release.next_version(tags, DAY) == expected


def test_digest_ignores_order_but_not_content_or_names():
    files = {"b.json": b"1", "a.json": b"2"}
    assert release.digest(files) == release.digest(dict(reversed(list(files.items()))))
    assert release.digest(files) != release.digest({**files, "a.json": b"3"})
    assert release.digest(files) != release.digest({"c.json": b"1", "a.json": b"2"})


def test_build_is_reproducible():
    first = release.build("v1.20261012.0", COMMIT, WHEN, FILES)
    second = release.build("v1.20261012.0", COMMIT, WHEN, copy.deepcopy(FILES))
    assert first == second


def test_build_publishes_the_contract_files_and_checksums():
    assets = release.build("v1.20261012.0", COMMIT, WHEN, FILES)
    for name, path in release.ASSETS.items():
        assert assets[name] == FILES[path]
    sums = dict(line.split("  ")[::-1] for line in assets["SHA256SUMS"].decode().splitlines())
    assert set(sums) == set(assets) - {"SHA256SUMS"}
    for name, digest in sums.items():
        assert hashlib.sha256(assets[name]).hexdigest() == digest


def test_manifest_describes_the_snapshot():
    meta = json.loads(release.build("v1.20261012.0", COMMIT, WHEN, FILES)["manifest.json"])
    assert meta["version"] == "v1.20261012.0"
    assert meta["schema_version"] == release.SCHEMA_MAJOR
    assert meta["commit"] == COMMIT
    assert meta["created"] == "2026-10-12T08:30:00Z"
    assert meta["digest"] == release.digest(FILES)
    assert meta["counts"]["labs"] == len(json.loads(FILES["labs.json"]))
    assert set(meta["files"]) == set(FILES)


def test_archives_hold_the_whole_catalogue_with_fixed_metadata():
    assets = release.build("v1.20261012.0", COMMIT, WHEN, FILES)
    prefix = "grida-models-v1.20261012.0/"
    expected = {prefix + "catalogue/" + name for name in FILES} | {prefix + "LICENSE", prefix + "manifest.json"}

    with tarfile.open(fileobj=io.BytesIO(assets["grida-models-v1.20261012.0.tar.gz"])) as tar:
        members = tar.getmembers()
        assert {m.name for m in members} == expected
        assert {(m.uid, m.gid, m.mtime, m.mode) for m in members} == {(0, 0, int(WHEN.timestamp()), 0o644)}
        assert tar.extractfile(prefix + "catalogue/models.json").read() == FILES["models.json"]

    with zipfile.ZipFile(io.BytesIO(assets["grida-models-v1.20261012.0.zip"])) as archive:
        assert set(archive.namelist()) == expected
        assert archive.read(prefix + "catalogue/labs.json") == FILES["labs.json"]


def current_snapshot(files=FILES):
    snapshot = release.manifest("v1.20261012.0", COMMIT, WHEN, files)
    snapshot["models"], snapshot["labs"] = json.loads(files["models.json"]), json.loads(files["labs.json"])
    return snapshot


def previous_snapshot(mutate):
    previous = {
        "manifest": release.manifest("v1.20261011.0", COMMIT, WHEN, FILES),
        "models": json.loads(FILES["models.json"]),
        "labs": json.loads(FILES["labs.json"]),
    }
    mutate(previous)
    return previous


def test_first_release_notes():
    assert "First release." in release.notes("v1.20261012.0", current_snapshot(), None)


def test_notes_without_content_changes():
    text = release.notes("v1.20261012.0", current_snapshot(), previous_snapshot(lambda p: None))
    assert "Changes since `v1.20261011.0`" in text
    assert "No content changes." in text


def test_notes_list_added_removed_and_changed_entries():
    def mutate(previous):
        text = previous["models"]["text.catalog"]
        text.pop("openai/gpt-5.5")
        text["anthropic/claude-opus-5"]["label"] = "Old label"
        text["example/retired"] = {"id": "example/retired"}
        previous["labs"]["xai"]["name"] = "Old name"
        previous["manifest"]["files"]["PROVENANCE.md"]["sha256"] = "0"
        previous["manifest"]["files"]["schemas/labs.schema.json"]["sha256"] = "0"

    text = release.notes("v1.20261012.0", current_snapshot(), previous_snapshot(mutate))
    assert "- Added models (1): `openai/gpt-5.5` (text.catalog)" in text
    assert "- Removed models (1): `example/retired` (text.catalog)" in text
    assert "- Changed models (1): `anthropic/claude-opus-5` (text.catalog)" in text
    assert "- Changed labs (1): `xai`" in text
    assert "- Schema changed: `schemas/labs.schema.json`" in text
    assert "- Other files changed: `PROVENANCE.md`" in text
    assert "No content changes." not in text


def test_asset_names_carry_the_schema_major():
    major = f".v{release.SCHEMA_MAJOR}."
    assert all(major in name for name in release.ASSETS)
    assert set(release.ASSETS.values()) <= set(FILES)


def test_previous_release_under_legacy_names_is_read(tmp_path):
    meta = release.manifest("v1.20261011.0", COMMIT, WHEN, FILES)
    (tmp_path / "manifest.json").write_text(json.dumps(meta))
    (tmp_path / "facts.json").write_bytes(FILES["models.json"])
    (tmp_path / "labs.json").write_bytes(FILES["labs.json"])
    previous = release.load_previous(tmp_path)
    assert previous["models"] == json.loads(FILES["models.json"])


def test_previous_release_needs_models_labs_and_manifest(tmp_path):
    (tmp_path / "manifest.json").write_text("{}")
    assert release.load_previous(tmp_path) is None


def test_renamed_files_compare_with_their_old_selves():
    def mutate(previous):
        files = previous["manifest"]["files"]
        for old, new in release.RENAMED.items():
            files[old] = files.pop(new)

    text = release.notes("v1.20261012.0", current_snapshot(), previous_snapshot(mutate))
    assert "- Renamed: `facts.json` → `models.json`, `schemas/facts.schema.json` → `schemas/models.schema.json`" in text
    assert "Schema changed" not in text and "Other files changed" not in text
