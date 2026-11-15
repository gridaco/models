"""Schema PRs need authored history; ordinary catalogue changes do not."""

from __future__ import annotations

import subprocess

import pytest

import check_changelog


def commit(repo, files):
    for name, value in files.items():
        path = repo / name
        if value is None:
            path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(value)
    subprocess.run(["git", "-C", str(repo), "add", "--all"], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=Schema test", "-c", "user.email=schema@example.com",
         "commit", "-m", "fixture"], check=True, capture_output=True,
    )
    return check_changelog.git(repo, "rev-parse", "HEAD").decode().strip()


@pytest.fixture
def history(tmp_path):
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    base = commit(tmp_path, {
        "catalogue/schemas/models.schema.json": '{"type":"object"}\n',
        check_changelog.CHANGELOG: "# Schema history\n\nExisting contract.\n",
    })
    return tmp_path, base


@pytest.mark.parametrize("name", ["catalogue/models.json", "models/example/card.toml", "README.md"])
def test_catalogue_and_docs_changes_need_no_schema_entry(history, name):
    repo, base = history
    head = commit(repo, {name: "Changed data or documentation.\n"})
    assert check_changelog.check(repo, base, head) is None


@pytest.mark.parametrize("change", ["edit", "add", "delete", "rename_out"])
def test_schema_changes_require_changelog_coverage(history, change):
    repo, base = history
    path = "catalogue/schemas/models.schema.json"
    changes = {
        "edit": {path: '{"type":"array"}\n'},
        "add": {"catalogue/schemas/new.schema.json": "{}\n"},
        "delete": {path: None},
        "rename_out": {path: None, "archived/models.schema.json": '{"type":"object"}\n'},
    }[change]
    head = commit(repo, changes)
    assert check_changelog.CHANGELOG in check_changelog.check(repo, base, head)


@pytest.mark.parametrize("entry", [None, "", " \n\t", "# Schema history\n\n Existing contract. \n"])
def test_missing_empty_or_whitespace_only_changelog_does_not_cover_schema(history, entry):
    repo, base = history
    head = commit(repo, {
        "catalogue/schemas/models.schema.json": '{"type":"array"}\n',
        check_changelog.CHANGELOG: entry,
    })
    assert check_changelog.check(repo, base, head)


def test_different_changelog_filename_does_not_cover_schema(history):
    repo, base = history
    head = commit(repo, {
        "catalogue/schemas/models.schema.json": '{"type":"array"}\n',
        "CHANGELOG.md": "Schema change explained here.\n",
    })
    assert check_changelog.check(repo, base, head)


def test_schema_change_with_authored_entry_is_covered(history):
    repo, base = history
    head = commit(repo, {
        "catalogue/schemas/models.schema.json": '{"type":"array"}\n',
        check_changelog.CHANGELOG: "# Schema history\n\nAccept arrays; readers must migrate.\n",
    })
    assert check_changelog.check(repo, base, head) is None


def test_schema_formatting_and_key_order_need_no_entry(history):
    repo, base = history
    before = commit(repo, {"catalogue/schemas/models.schema.json": '{"type":"object","description":"Meaning."}\n'})
    head = commit(repo, {
        "catalogue/schemas/models.schema.json": '{\n  "description": "Meaning.",\n  "type": "object"\n}\n',
    })
    assert check_changelog.check(repo, before, head) is None


def test_schema_description_change_requires_entry(history):
    repo, base = history
    head = commit(repo, {"catalogue/schemas/models.schema.json": '{"type":"object","description":"New meaning."}\n'})
    assert check_changelog.check(repo, base, head)


@pytest.mark.parametrize("before, after", [
    ('{"const":true}\n', '{"const":1}\n'),
    ('{"maximum":0.123456789123456789}\n', '{"maximum":0.123456789123456788}\n'),
])
def test_schema_comparison_preserves_json_types_and_decimal_precision(history, before, after):
    repo, _ = history
    base = commit(repo, {"catalogue/schemas/models.schema.json": before})
    head = commit(repo, {"catalogue/schemas/models.schema.json": after})
    assert check_changelog.check(repo, base, head)


def test_malformed_schema_comparison_fails_closed(history):
    repo, base = history
    head = commit(repo, {"catalogue/schemas/models.schema.json": "not JSON\n"})
    with pytest.raises(ValueError):
        check_changelog.check(repo, base, head)


def test_first_changelog_can_cover_a_schema_change(history):
    repo, base = history
    without = commit(repo, {check_changelog.CHANGELOG: None})
    head = commit(repo, {
        "catalogue/schemas/models.schema.json": '{"type":"array"}\n',
        check_changelog.CHANGELOG: "# Schema history\n\nAccept arrays; readers must migrate.\n",
    })
    assert check_changelog.check(repo, without, head) is None


def test_unknown_or_inexact_revisions_fail_closed(history):
    repo, base = history
    with pytest.raises(ValueError):
        check_changelog.check(repo, "main", base)
    with pytest.raises(subprocess.CalledProcessError):
        check_changelog.check(repo, "0" * 40, base)


def test_base_branch_schema_changes_do_not_require_an_entry_in_docs_only_pr(history):
    repo, common = history
    head = commit(repo, {"README.md": "Documentation update.\n"})
    check_changelog.git(repo, "checkout", "--detach", common)
    base = commit(repo, {"catalogue/schemas/models.schema.json": '{"type":"array"}\n'})
    assert check_changelog.check(repo, base, head) is None


def test_base_branch_changelog_changes_cannot_cover_pr_schema_changes(history):
    repo, common = history
    head = commit(repo, {"catalogue/schemas/models.schema.json": '{"type":"array"}\n'})
    check_changelog.git(repo, "checkout", "--detach", common)
    base = commit(repo, {check_changelog.CHANGELOG: "# Schema history\n\nUnrelated base-branch entry.\n"})
    assert check_changelog.check(repo, base, head)
