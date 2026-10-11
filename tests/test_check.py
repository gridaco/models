"""Each invariant in scripts/check.py must reject the case it exists for."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("check", ROOT / "scripts" / "check.py")
check = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(check)

FACTS = check.load(check.FACTS)
SCHEMA = check.load(check.FACTS_SCHEMA)


def mutated(mutate):
    facts = copy.deepcopy(FACTS)
    mutate(facts)
    return check.check(facts, SCHEMA)


def first(section: str, facts) -> dict:
    return next(iter(facts[section].values()))


def test_catalogue_is_valid():
    assert check.check(FACTS, SCHEMA) == []


def test_id_must_match_table_key():
    def mutate(facts):
        first("text.catalog", facts)["id"] = "vendor/renamed"

    assert any("does not match its table key" in e for e in mutated(mutate))


def test_release_date_must_be_a_real_day():
    def mutate(facts):
        first("image.models", facts)["release"]["date"] = "2026-02-30"

    assert any("calendar date" in e for e in mutated(mutate))


def test_null_release_date_requires_provider_endpoint_basis():
    def mutate(facts):
        release = first("video.models", facts)["release"]
        release["date"] = None
        release["basis"] = "model"

    assert any("provider_endpoint" in e for e in mutated(mutate))


def test_release_source_must_be_https():
    def mutate(facts):
        first("text.catalog", facts)["release"]["source_url"] = "http://example.com"

    assert any("source_url" in e for e in mutated(mutate))


@pytest.mark.parametrize("key", check.POLICY_KEYS)
def test_facts_carry_no_product_policy(key):
    def mutate(facts):
        first("image.models", facts)[key] = True

    assert any(f"policy key {key!r}" in e for e in mutated(mutate))


def test_multi_provider_cards_select_no_primary_provider():
    def mutate(facts):
        first("image.models", facts)["provider"] = "vercel"

    assert any("primary 'provider'" in e for e in mutated(mutate))


def test_binding_is_keyed_by_its_own_provider():
    def mutate(facts):
        card = first("video.models", facts)
        name = next(iter(card["providers"]))
        card["providers"][name]["provider"] = "someone-else"

    assert any("binding.provider" in e for e in mutated(mutate))


def test_multi_provider_cards_need_a_binding():
    def mutate(facts):
        first("video.models", facts)["providers"] = {}

    assert any("no provider bindings" in e for e in mutated(mutate))


def test_stale_known_exception_is_reported():
    def mutate(facts):
        for section, card_id, key in check.KNOWN_EXCEPTIONS:
            facts[section][card_id].pop(key, None)

    assert any("stale known exception" in e for e in mutated(mutate))
