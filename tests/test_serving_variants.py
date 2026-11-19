"""Serving variants retain canonical identity and preserve provider-scoped facts."""

from copy import deepcopy

import pytest

import cards
import check


MODEL_ID = "openai/gpt-6.2-sol"
SOURCE = "https://provider.example/models"
CATALOGUE = check.load(check.MODELS_JSON)
SCHEMA = check.load(check.MODELS_SCHEMA)


def fast_variant():
    return {
        "label": "Fast",
        "source_url": SOURCE,
        "providers": {
            "vercel": {
                "id": f"{MODEL_ID}-fast",
                "source_url": SOURCE,
                "token_pricing": {
                    "source_url": SOURCE,
                    "unit": "usd_per_token",
                    "input": "0.000004",
                    "output": "0.00002",
                },
            },
            "openrouter": {
                "id": MODEL_ID,
                "source_url": SOURCE,
                "request": {
                    "service_tier": "fast",
                    "provider": {"only": ["openai/fast"]},
                },
            },
        },
    }


def test_mixed_catalogue_accepts_fast_variants_and_preserves_existing_cards():
    previous = deepcopy(CATALOGUE)
    for card in previous["text.catalog"].values():
        card.pop("variants", None)
    candidate = deepcopy(previous)
    parent = candidate["text.catalog"][MODEL_ID]
    parent["variants"] = {"fast": fast_variant()}

    assert not check.check(previous, SCHEMA)
    assert not check.check(candidate, SCHEMA)
    assert parent.pop("variants")["fast"] == fast_variant()
    assert candidate == previous


def test_authoring_projection_keeps_variant_under_its_parent():
    loaded = cards.load_cards(check.build.MODELS)
    parent = next(card for card in loaded if card.data.get("id") == MODEL_ID)
    parent.data["variants"] = {"fast": fast_variant()}
    sections = check.build.sections()

    assert not list(cards.layout_errors(loaded, sections))
    generated = cards.assemble(loaded, sections, check.build.schema_id(), check.build.required_sections())
    projected = generated["text.catalog"][MODEL_ID]
    assert not check.check(generated, SCHEMA)
    assert projected["variants"] == {"fast": fast_variant()}
    assert projected["providers"] == CATALOGUE["text.catalog"][MODEL_ID]["providers"]
    assert f"{MODEL_ID}-fast" not in generated["text.catalog"]


@pytest.fixture
def catalogue_with_variant():
    catalogue = deepcopy(CATALOGUE)
    catalogue["text.catalog"][MODEL_ID]["variants"] = {"fast": fast_variant()}
    return catalogue


def variant_bindings(catalogue):
    return catalogue["text.catalog"][MODEL_ID]["variants"]["fast"]["providers"]


def test_variant_binding_requires_a_parent_provider(catalogue_with_variant):
    providers = variant_bindings(catalogue_with_variant)
    providers["unlisted"] = providers.pop("vercel")
    errors = check.check(catalogue_with_variant, SCHEMA)
    assert any("variant provider has no provider binding" in error for error in errors)


def test_same_model_id_requires_a_request_selector(catalogue_with_variant):
    variant_bindings(catalogue_with_variant)["openrouter"].pop("request")
    errors = check.check(catalogue_with_variant, SCHEMA)
    assert any("without a request selector" in error for error in errors)


@pytest.mark.parametrize("request_fields", [{}, [], None, {"model": f"{MODEL_ID}-fast"}])
def test_native_request_selector_must_be_a_nonempty_object_without_model(catalogue_with_variant, request_fields):
    variant_bindings(catalogue_with_variant)["openrouter"]["request"] = request_fields
    errors = check.check(catalogue_with_variant, SCHEMA)
    assert any("/request" in error for error in errors)


def test_variant_key_is_lower_snake_case(catalogue_with_variant):
    catalogue_with_variant["text.catalog"][MODEL_ID]["variants"] = {"Fast-mode": fast_variant()}
    errors = check.check(catalogue_with_variant, SCHEMA)
    assert any("/variants" in error for error in errors)


def test_serving_variants_are_text_only(catalogue_with_variant):
    image_card = next(iter(catalogue_with_variant["image.models"].values()))
    image_card["variants"] = {"fast": fast_variant()}
    errors = check.check(catalogue_with_variant, SCHEMA)
    assert any("variants are only supported on text cards" in error for error in errors)


def test_provider_can_use_the_same_id_for_distinct_variant_selectors(catalogue_with_variant):
    variants = catalogue_with_variant["text.catalog"][MODEL_ID]["variants"]
    ultrafast = fast_variant()
    router = ultrafast["providers"]["openrouter"]
    ultrafast["label"] = "Ultrafast"
    ultrafast["providers"] = {"openrouter": router}
    router["request"] = {"service_tier": "ultrafast"}
    variants["ultrafast"] = ultrafast

    assert not check.check(catalogue_with_variant, SCHEMA)


def test_exact_duplicate_provider_call_and_selector_is_rejected(catalogue_with_variant):
    variants = catalogue_with_variant["text.catalog"][MODEL_ID]["variants"]
    duplicate = fast_variant()
    router = duplicate["providers"]["openrouter"]
    duplicate["providers"] = {"openrouter": router}
    router["request"] = dict(reversed(list(router["request"].items())))
    variants["fast_again"] = duplicate

    errors = check.check(catalogue_with_variant, SCHEMA)
    assert any("duplicate variant call ID and request selector" in error for error in errors)


def test_variant_prices_validate_provider_sources_and_rate_bands(catalogue_with_variant):
    price = variant_bindings(catalogue_with_variant)["vercel"]["token_pricing"]
    price["source_url"] = "https://user:secret@provider.example/models"
    price["input"] = "4e-6"
    price["tiers"] = [
        {"meter": "input", "minimum_input_tokens": 0, "maximum_input_tokens": 100, "usd_per_token": "0.000004"},
        {"meter": "input", "minimum_input_tokens": 99, "usd_per_token": "0.000008"},
    ]
    errors = check.check(catalogue_with_variant, SCHEMA)
    assert any("/token_pricing/input" in error for error in errors)
    assert any("source_url must be an absolute HTTPS URL without credentials" in error for error in errors)
    assert any("overlapping input-token tiers for input" in error for error in errors)
