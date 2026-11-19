"""Callable offerings and same-ID modes preserve canonical provider scopes."""

from copy import deepcopy

import pytest

import cards
import check


MODEL_ID = "openai/gpt-6.2-sol"
OTHER_MODEL_ID = "openai/gpt-6.2-astra"
FAST_ID = f"{MODEL_ID}-fast"
SOURCE = "https://provider.example/models"
CATALOGUE = check.load(check.MODELS_JSON)
SCHEMA = check.load(check.MODELS_SCHEMA)


def token_pricing():
    return {
        "source_url": SOURCE,
        "unit": "usd_per_token",
        "input": "0.000004",
        "output": "0.00002",
    }


def fast_offering():
    return {
        "id": FAST_ID,
        "canonical_model_id": MODEL_ID,
        "mode": "fast",
        "label": "GPT-6.2 Sol (Fast)",
        "source_url": SOURCE,
        "token_pricing": token_pricing(),
    }


def fast_mode():
    return {
        "source_url": SOURCE,
        "request": {"service_tier": "fast", "provider": {"only": ["openai/fast"]}},
        "token_pricing": token_pricing(),
    }


def add_fast_facts(card):
    providers = card["providers"]
    providers["vercel"]["offerings"] = {FAST_ID: fast_offering()}
    providers["openrouter"]["modes"] = {"fast": fast_mode()}


def without_fast_facts(catalogue):
    previous = deepcopy(catalogue)
    for card in previous["text.catalog"].values():
        for binding in card.get("providers", {}).values():
            binding.pop("offerings", None)
            binding.pop("modes", None)
    return previous


def test_mixed_catalogue_preserves_canonical_models_and_base_bindings():
    previous = without_fast_facts(CATALOGUE)
    candidate = deepcopy(previous)
    add_fast_facts(candidate["text.catalog"][MODEL_ID])

    assert not check.check(previous, SCHEMA)
    assert not check.check(candidate, SCHEMA)
    assert candidate["text.catalog"].keys() == previous["text.catalog"].keys()
    assert without_fast_facts(candidate) == previous


def test_authoring_projection_preserves_both_provider_fact_shapes():
    loaded = cards.load_cards(check.build.MODELS)
    parent = next(card for card in loaded if card.data.get("id") == MODEL_ID)
    add_fast_facts(parent.data)
    sections = check.build.sections()

    assert not list(cards.layout_errors(loaded, sections))
    generated = cards.assemble(loaded, sections, check.build.schema_id(), check.build.required_sections())
    projected = generated["text.catalog"][MODEL_ID]["providers"]
    assert not check.check(generated, SCHEMA)
    assert projected["vercel"]["offerings"][FAST_ID] == fast_offering()
    assert projected["openrouter"]["modes"]["fast"] == fast_mode()
    assert projected["openrouter"]["id"] == MODEL_ID
    assert FAST_ID not in generated["text.catalog"]


@pytest.fixture
def catalogue_with_fast():
    catalogue = without_fast_facts(CATALOGUE)
    add_fast_facts(catalogue["text.catalog"][MODEL_ID])
    return catalogue


def providers(catalogue, model_id=MODEL_ID):
    return catalogue["text.catalog"][model_id]["providers"]


def fast_record(catalogue, field):
    bindings = providers(catalogue)
    if field == "offerings":
        return bindings["vercel"]["offerings"][FAST_ID]
    return bindings["openrouter"]["modes"]["fast"]


def test_same_id_mode_requires_a_request(catalogue_with_fast):
    fast_record(catalogue_with_fast, "modes").pop("request")
    errors = check.check(catalogue_with_fast, SCHEMA)
    assert any("/modes/fast" in error and "request" in error for error in errors)


@pytest.mark.parametrize("field", ["offerings", "modes"])
@pytest.mark.parametrize("selector", [{}, [], None, {"model": FAST_ID}])
def test_request_selectors_are_nonempty_objects_without_model(catalogue_with_fast, field, selector):
    fast_record(catalogue_with_fast, field)["request"] = selector
    errors = check.check(catalogue_with_fast, SCHEMA)
    assert any(f"/{field}/" in error and "/request" in error for error in errors)


def test_dedicated_id_can_include_an_additional_native_selector(catalogue_with_fast):
    fast_record(catalogue_with_fast, "offerings")["request"] = {"service_tier": "fast"}
    assert not check.check(catalogue_with_fast, SCHEMA)


def test_fast_is_the_only_supported_mode(catalogue_with_fast):
    fast_record(catalogue_with_fast, "offerings")["mode"] = "ultrafast"
    providers(catalogue_with_fast)["openrouter"]["modes"]["turbo"] = fast_mode()
    errors = check.check(catalogue_with_fast, SCHEMA)
    assert any("/offerings/" in error and "/mode" in error for error in errors)
    assert any("/modes" in error and "turbo" in error for error in errors)


def test_offering_id_matches_its_key(catalogue_with_fast):
    fast_record(catalogue_with_fast, "offerings")["id"] = "different-call-id"
    errors = check.check(catalogue_with_fast, SCHEMA)
    assert any("offering id does not match its key" in error for error in errors)


def test_offering_names_its_actual_canonical_parent(catalogue_with_fast):
    fast_record(catalogue_with_fast, "offerings")["canonical_model_id"] = OTHER_MODEL_ID
    errors = check.check(catalogue_with_fast, SCHEMA)
    assert any("canonical_model_id does not match its containing model" in error for error in errors)


@pytest.mark.parametrize("base_model_id", [MODEL_ID, OTHER_MODEL_ID])
def test_offering_id_must_not_reuse_a_base_binding_id(catalogue_with_fast, base_model_id):
    base_id = providers(catalogue_with_fast, base_model_id)["vercel"]["id"]
    offerings = providers(catalogue_with_fast)["vercel"]["offerings"]
    offerings[base_id] = offerings.pop(FAST_ID)
    offerings[base_id]["id"] = base_id
    errors = check.check(catalogue_with_fast, SCHEMA)
    assert any("offering reuses an existing base binding id" in error for error in errors)


def test_offering_id_is_unique_per_provider(catalogue_with_fast):
    duplicate = fast_offering()
    duplicate["canonical_model_id"] = OTHER_MODEL_ID
    bindings = providers(catalogue_with_fast, OTHER_MODEL_ID)
    bindings["openrouter"]["offerings"] = {FAST_ID: duplicate}
    assert not check.check(catalogue_with_fast, SCHEMA)

    bindings["vercel"]["offerings"] = bindings["openrouter"].pop("offerings")
    errors = check.check(catalogue_with_fast, SCHEMA)
    assert any("duplicate offering id for provider" in error for error in errors)


@pytest.mark.parametrize("scope", ["text_card", "image_binding"])
def test_offerings_and_modes_are_only_allowed_on_text_provider_bindings(catalogue_with_fast, scope):
    if scope == "text_card":
        target = catalogue_with_fast["text.catalog"][MODEL_ID]
    else:
        image_card = next(iter(catalogue_with_fast["image.models"].values()))
        target = next(iter(image_card["providers"].values()))
    target["offerings"] = {FAST_ID: fast_offering()}
    target["modes"] = {"fast": fast_mode()}
    errors = check.check(catalogue_with_fast, SCHEMA)
    assert any("offerings and modes are only supported on text provider bindings" in error for error in errors)


@pytest.mark.parametrize("field", ["offerings", "modes"])
def test_fast_pricing_validates_provider_sources_and_rate_bands(catalogue_with_fast, field):
    price = fast_record(catalogue_with_fast, field)["token_pricing"]
    price["source_url"] = "https://user:secret@provider.example/models"
    price["input"] = "4e-6"
    price["tiers"] = [
        {"meter": "input", "minimum_input_tokens": 0, "maximum_input_tokens": 100, "usd_per_token": "0.000004"},
        {"meter": "input", "minimum_input_tokens": 99, "usd_per_token": "0.000008"},
    ]
    errors = check.check(catalogue_with_fast, SCHEMA)
    assert any("/token_pricing/input" in error for error in errors)
    assert any("source_url must be an absolute HTTPS URL without credentials" in error for error in errors)
    assert any("overlapping input-token tiers for input" in error for error in errors)


@pytest.mark.parametrize("field", ["offerings", "modes"])
@pytest.mark.parametrize("number", ["nan", "inf", "-inf"])
def test_build_rejects_nonfinite_numbers_in_authored_fast_requests(tmp_path, monkeypatch, field, number):
    models = tmp_path / "models"
    model_dir = models / MODEL_ID
    model_dir.mkdir(parents=True)
    source = f'''\
id = "{MODEL_ID}"
section = "text.catalog"
vendor = "openai"
label = "Example model"

[release]
date = "2026-01-01"
basis = "model"
source_url = "{SOURCE}"

[providers.vercel]
provider = "vercel"
id = "{MODEL_ID}"
'''
    if field == "offerings":
        source += f'''\
[providers.vercel.offerings."{FAST_ID}"]
id = "{FAST_ID}"
canonical_model_id = "{MODEL_ID}"
mode = "fast"
label = "Example model (Fast)"
'''
    else:
        source += "[providers.vercel.modes.fast]\n"
    source += f'''\
source_url = "{SOURCE}"
request = {{ service_tier = "fast", options = {{ levels = [{{ threshold = {number} }}] }} }}
'''
    (model_dir / cards.CARD_FILE).write_text(source, encoding="utf-8")
    monkeypatch.setattr(check.build, "MODELS", models)

    outputs, errors = check.build.build()

    assert not outputs
    assert any("cannot generate valid JSON" in error for error in errors)
