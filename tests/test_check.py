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


# The authored cards in models/ and their projection to facts.json.

import cards  # noqa: E402

SECTIONS = check.build.sections()
CARDS = cards.load_cards(check.build.MODELS)


def layout(mutate):
    loaded = copy.deepcopy(CARDS)
    mutate(loaded)
    return list(cards.layout_errors(loaded, SECTIONS))


def card(loaded, card_id):
    return next(c for c in loaded if c.data.get("id") == card_id)


def test_cards_generate_the_committed_facts():
    assert check.source_errors() == []


def test_hand_edited_facts_are_reported_out_of_date():
    edited = check.FACTS.read_text(encoding="utf-8").replace('"GPT-5.5"', '"GPT 5.5"', 1)
    assert any("out of date" in e for e in check.source_errors(edited))


def test_cards_round_trip_every_null():
    assembled = cards.assemble(CARDS, SECTIONS)
    assert assembled == FACTS


def test_card_must_sit_under_its_vendor():
    def mutate(loaded):
        card(loaded, "bfl/flux-2-pro").path = "bfl/flux-2-pro"

    assert any("belongs in models/black-forest-labs/flux-2-pro/" in e for e in layout(mutate))


def test_card_without_vendor_sits_under_its_id_namespace():
    def mutate(loaded):
        card(loaded, "openai/gpt-5.5").path = "gpt-5.5"

    assert any("belongs in models/openai/gpt-5.5/" in e for e in layout(mutate))


def test_card_must_name_a_known_section():
    def mutate(loaded):
        card(loaded, "openai/gpt-5.5").data["section"] = "text.models"

    assert any("is not a facts.json section" in e for e in layout(mutate))


def test_card_file_must_be_named_card_toml():
    def mutate(loaded):
        card(loaded, "openai/gpt-5.5").file = "gpt-5.5.toml"

    assert any("unexpected file" in e for e in layout(mutate))


def test_card_id_must_be_unique_within_its_section():
    def mutate(loaded):
        loaded.append(copy.deepcopy(card(loaded, "openai/gpt-5.5")))

    assert any("duplicates" in e for e in layout(mutate))


def test_card_directory_cannot_contain_another_card():
    def mutate(loaded):
        nested = copy.deepcopy(card(loaded, "openai/gpt-5.5"))
        nested.data["id"] = "openai/gpt-5.5/mini"
        nested.path = "openai/gpt-5.5/mini"
        loaded.append(nested)

    assert any("cannot contain another card" in e for e in layout(mutate))


def test_operation_must_be_authored_as_operation_toml():
    def mutate(loaded):
        op = next(c for c in loaded if c.file == cards.OPERATION_FILE)
        op.file = cards.CARD_FILE

    assert any("authored as operation.toml" in e for e in layout(mutate))


def test_null_keys_must_be_dotted_paths():
    def mutate(loaded):
        card(loaded, "openai/gpt-image-2").data["null_keys"] = "styles"

    assert any("null_keys" in e for e in layout(mutate))
