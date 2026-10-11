"""Validate the authored cards in `models/` and the catalogue contract in `catalogue/`.

Three layers:

1. Source: every card in `models/` sits at the path its lab and ID give it, names a
   known section, every lab directory has a `lab.toml`, and the generated
   `catalogue/models.json` and `catalogue/labs.json` are exactly what the source
   generates (`scripts/build.py`).
2. Structure: `catalogue/models.json` and `catalogue/labs.json` against their schemas in
   `catalogue/schemas/` (JSON Schema 2020-12, with format assertions on).
3. Invariants the schema cannot express: table keys equal card IDs, release
   dates are real calendar dates, facts carry no product policy, and provider
   bindings are keyed by their own provider.

Usage:
    uv run scripts/check.py

Exits 1 and prints one line per problem when the catalogue is invalid.
"""

from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path
from typing import Any, Iterator

from jsonschema import Draft202012Validator

import build
import cards

ROOT = Path(__file__).resolve().parent.parent
MODELS_JSON = ROOT / "catalogue" / "models.json"
MODELS_SCHEMA = ROOT / "catalogue" / "schemas" / "models.schema.json"
LABS = ROOT / "catalogue" / "labs.json"
LABS_SCHEMA = ROOT / "catalogue" / "schemas" / "labs.schema.json"

# Top-level sections that are not tables of cards keyed by ID.
NON_TABLE_SECTIONS = {"three_d.rig_check.operation"}

# Listing and lifecycle decisions belong to the products that consume the
# catalogue, not to model facts.
POLICY_KEYS = ("listed", "listed_reason", "status", "legacy", "deprecated", "default")

# Families whose cards hold intrinsic facts plus per-provider bindings.
# A primary-provider choice on such a card is product policy.
MULTI_PROVIDER_SECTIONS = ("image.models", "video.models")

# Known violations carried over unchanged from the source data. Each entry is
# (section, card id, key). An exception that no longer matches the data is
# itself reported, so this list can only shrink.
KNOWN_EXCEPTIONS = {
    # Carried with the embedding card's storage contract; see catalogue/README.md.
    ("embedding.models", "google/gemini-embedding-2", "deprecated"),
}

# Lab directories without a lab.toml. Each is the ID namespace of a card that has no
# sourced `vendor` yet: its publisher on a provider, not the lab that made the model.
# An entry that no longer applies is reported, so this set can only shrink.
KNOWN_UNREGISTERED_LABS = {
    "851-labs",  # publisher of 851-labs/background-remover on Replicate
    "nightmareai",  # publisher of nightmareai/real-esrgan on Replicate
}


def load(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def schema_errors(facts: Any, schema: Any) -> Iterator[str]:
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(
        schema, format_checker=Draft202012Validator.FORMAT_CHECKER
    )
    for error in sorted(validator.iter_errors(facts), key=lambda e: list(e.absolute_path)):
        path = "/".join(str(p) for p in error.absolute_path) or "(root)"
        yield f"schema: {path}: {error.message}"


def is_calendar_date(value: str) -> bool:
    try:
        return datetime.date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def invariant_errors(facts: dict[str, Any]) -> Iterator[str]:
    used_exceptions: set[tuple[str, str, str]] = set()

    for section, table in facts.items():
        if section in NON_TABLE_SECTIONS or not isinstance(table, dict):
            continue
        for key, card in table.items():
            where = f"{section}/{key}"
            if not isinstance(card, dict):
                yield f"{where}: card is not an object"
                continue

            if card.get("id") != key:
                yield f"{where}: id {card.get('id')!r} does not match its table key"

            release = card.get("release")
            if isinstance(release, dict):
                date = release.get("date")
                if date is None:
                    if release.get("basis") != "provider_endpoint":
                        yield f"{where}: release.date is null but basis is not provider_endpoint"
                elif not (isinstance(date, str) and is_calendar_date(date)):
                    yield f"{where}: release.date {date!r} is not a YYYY-MM-DD calendar date"
                if not str(release.get("source_url", "")).startswith("https://"):
                    yield f"{where}: release.source_url is not https"
            else:
                yield f"{where}: missing release"

            for policy_key in POLICY_KEYS:
                if policy_key in card:
                    exception = (section, key, policy_key)
                    if exception in KNOWN_EXCEPTIONS:
                        used_exceptions.add(exception)
                    else:
                        yield f"{where}: carries product policy key {policy_key!r}"

            if section in MULTI_PROVIDER_SECTIONS:
                if "provider" in card:
                    yield f"{where}: selects a primary 'provider'; bindings carry no preference"
                providers = card.get("providers")
                if not isinstance(providers, dict) or not providers:
                    yield f"{where}: has no provider bindings"
                    continue
                for name, binding in providers.items():
                    if binding.get("provider") != name:
                        yield f"{where}/providers/{name}: binding.provider is {binding.get('provider')!r}"
                    if not binding.get("id"):
                        yield f"{where}/providers/{name}: binding has no id"

    for exception in sorted(KNOWN_EXCEPTIONS - used_exceptions):
        yield f"stale known exception {exception}: remove it from KNOWN_EXCEPTIONS"


def check(facts: Any, schema: Any) -> list[str]:
    errors = list(schema_errors(facts, schema))
    if isinstance(facts, dict):
        errors.extend(invariant_errors(facts))
    return errors


def source_errors(committed: dict[Path, bytes] | None = None) -> list[str]:
    outputs, errors = build.build()
    errors += cards.lab_errors(
        cards.load_labs(build.MODELS), cards.load_cards(build.MODELS), KNOWN_UNREGISTERED_LABS
    )
    if not errors:
        for path in build.stale(outputs, committed):
            errors.append(f"{path.relative_to(ROOT)} is out of date: run uv run scripts/build.py")
        for path in build.orphans(outputs):
            errors.append(f"{path.relative_to(ROOT)} is not generated by any lab: run uv run scripts/build.py")
    return errors


def main() -> int:
    facts = load(MODELS_JSON)
    errors = source_errors() + check(facts, load(MODELS_SCHEMA))
    errors += [f"labs.json {error}" for error in schema_errors(load(LABS), load(LABS_SCHEMA))]
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        print(f"{len(errors)} problem(s)", file=sys.stderr)
        return 1
    count = sum(
        len(table)
        for section, table in facts.items()
        if section not in NON_TABLE_SECTIONS and isinstance(table, dict)
    )
    print(f"ok: {MODELS_JSON.relative_to(ROOT)} ({count} cards), {LABS.relative_to(ROOT)} ({len(load(LABS))} labs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
