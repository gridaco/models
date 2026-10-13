"""Provider facts apply uniformly to model families and preserve public price meaning."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("coverage_check", ROOT / "scripts" / "check.py")
check = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(check)
CATALOGUE = check.load(check.MODELS_JSON)
SCHEMA = check.load(check.MODELS_SCHEMA)
SECTIONS = tuple(section for section in CATALOGUE if section != "$schema")
SOURCE = "https://provider.example/models"
BINDING = {"id": "test-model", "provider": "example", "source_url": SOURCE}
PRICE = {
    "source_url": SOURCE,
    "currency": "USD",
    "components": [{
        "id": "input-band", "meter": "input_tokens", "unit": "token",
        "usd_per_unit": "0.0000015", "per_quantity": "1",
        "when": {"properties": {"quality": {"enum": ["standard", "high"]}}},
        "quantity_rounding": {"mode": "none", "increment": None},
        "quantity_range": {"meter": "input_tokens", "min": "0", "max": "1000"},
    }],
}


def mutate(callback, section="image.models"):
    facts = copy.deepcopy(CATALOGUE)
    card = facts[section] if section in check.NON_TABLE_SECTIONS else next(iter(facts[section].values()))
    callback(card)
    return check.check(facts, SCHEMA)


def add_binding(card):
    card.setdefault("providers", {})["example"] = copy.deepcopy(BINDING)
    card["reference_provider"] = "example"
    card.setdefault("provider_coverage", {})["example"] = {
        "disposition": "listed", "source_url": SOURCE,
    }


@pytest.mark.parametrize("section", SECTIONS)
def test_reference_and_coverage_are_valid_in_every_family_and_operation(section):
    assert mutate(add_binding, section) == []


@pytest.mark.parametrize("section", SECTIONS)
def test_provider_key_must_match_even_outside_image_and_video(section):
    def edit(card):
        add_binding(card)
        card["providers"]["example"]["provider"] = "different"
    assert any("binding.provider" in error for error in mutate(edit, section))


def test_reference_resolves_existing_native_direct_provider_without_duplicate_binding():
    def edit(card):
        card["reference_provider"] = card["provider"]
    assert mutate(edit, "three_d.rig_check.operation") == []


def test_reference_does_not_create_an_invented_provider():
    assert any("reference_provider" in error for error in mutate(lambda card: card.update(reference_provider="invented")))


@pytest.mark.parametrize("disposition", ["not_listed", "excluded"])
def test_absence_requires_a_public_reason_and_cannot_coexist_with_binding(disposition):
    def no_reason(card):
        card["provider_coverage"] = {"unlisted": {"disposition": disposition, "source_url": SOURCE}}
    assert mutate(no_reason)
    def contradictory(card):
        add_binding(card)
        card["provider_coverage"]["example"].update(disposition=disposition, reason="Documented incompatible contract")
    assert any("still has a binding" in error for error in mutate(contradictory))
    def valid(card):
        card["provider_coverage"] = {"unlisted": {
            "disposition": disposition, "source_url": SOURCE, "reason": "Published endpoint uses a different model identity",
        }}
    assert mutate(valid) == []


def test_listed_coverage_cannot_replace_a_missing_binding():
    def edit(card):
        card["provider_coverage"] = {"invented": {"disposition": "listed", "source_url": SOURCE}}
    assert any("no binding" in error for error in mutate(edit))


@pytest.mark.parametrize("url", ["http://example.com", "https://user:password@example.com", "/models"])
def test_coverage_and_binding_sources_reject_unsafe_or_relative_links(url):
    def edit(card):
        add_binding(card)
        card["provider_coverage"]["example"]["source_url"] = url
    assert mutate(edit)
    def binding(card):
        add_binding(card)
        card["providers"]["example"]["source_url"] = url
    assert mutate(binding)


def price_mutation(callback=lambda price: None, *, endpoint=False):
    def edit(card):
        add_binding(card)
        target = card["providers"]["example"]
        if endpoint:
            target["endpoints"] = [{"id": "generate", "operation": "image.generate", "interface": "openai.images", "input": "multi_image", "source_url": SOURCE}]
            target = target["endpoints"][0]
        target["published_pricing"] = copy.deepcopy(PRICE)
        callback(target["published_pricing"])
    return mutate(edit)


@pytest.mark.parametrize("endpoint", [False, True])
def test_public_usd_components_are_exact_and_provider_neutral(endpoint):
    assert price_mutation(endpoint=endpoint) == []


@pytest.mark.parametrize("value", [1.5, "-1", "NaN", "1e-5", "0.0.1"])
def test_published_rates_use_nonnegative_decimal_strings(value):
    assert price_mutation(lambda price: price["components"][0].update(usd_per_unit=value))


@pytest.mark.parametrize("value", ["0", "0.0", "-1", 1])
def test_price_denominator_must_be_a_positive_decimal(value):
    assert price_mutation(lambda price: price["components"][0].update(per_quantity=value))


@pytest.mark.parametrize("band", [{"min": "1000", "max": "1000"}, {"min": "1001", "max": "1000"}])
def test_half_open_price_bands_must_have_positive_width(band):
    assert price_mutation(lambda price: price["components"][0]["quantity_range"].update(band))


def test_unbounded_price_band_remains_valid():
    assert price_mutation(lambda price: price["components"][0]["quantity_range"].update(max=None)) == []


@pytest.mark.parametrize("rounding", [{"mode": "none", "increment": "1"}, {"mode": "ceil", "increment": None}])
def test_rounding_mode_and_increment_must_agree(rounding):
    assert price_mutation(lambda price: price["components"][0].update(quantity_rounding=rounding))


def test_ceil_quantity_rounding_preserves_its_positive_increment():
    assert price_mutation(lambda price: price["components"][0].update(quantity_rounding={"mode": "ceil", "increment": "1"})) == []


def test_duplicate_component_identity_rejected():
    assert price_mutation(lambda price: price["components"].append(copy.deepcopy(price["components"][0])))


@pytest.mark.parametrize("extra", ["margin", "credits_per_dollar", "promotion_end", "account_price"])
def test_published_pricing_does_not_accept_business_or_promotion_fields(extra):
    assert price_mutation(lambda price: price.update({extra: "example"}))


def test_public_price_requires_currency_source_and_components():
    for field in ["source_url", "currency", "components"]:
        assert price_mutation(lambda price: price.pop(field))


def test_price_conditions_are_valid_json_schema_predicates():
    assert price_mutation(lambda price: price["components"][0].update(when={"properties": {"quality": {"const": "high"}}})) == []
    assert price_mutation(lambda price: price["components"][0].update(when={"type": "not-a-json-type"}))


@pytest.mark.parametrize("field", ["request_schema_url", "result_schema_url"])
def test_public_contract_links_are_https_without_credentials(field):
    def edit(card):
        add_binding(card)
        card["providers"]["example"]["endpoints"] = [{
            "id": "generate", "input": "image", "source_url": SOURCE,
            field: "https://user:password@example.com/schema",
        }]
    assert mutate(edit)


def test_cache_write_ttls_remain_separate_prices():
    def edit(card):
        add_binding(card)
        card["providers"]["example"]["token_pricing"] = {
            "source_url": SOURCE, "unit": "usd_per_token", "scope": "Standard service; cache writes 5 minutes and 1 hour",
            "input_cache_write": "0.00000125", "input_cache_write_1h": "0.000002",
        }
    assert mutate(edit) == []


def test_toml_omission_preserves_unbounded_range_and_no_rounding():
    """Arrays need no synthetic nulls: TOML omits only semantically optional fields."""
    import tomllib
    pricing = tomllib.loads('''
source_url = "https://provider.example/models"
currency = "USD"
[[components]]
meter = "input_tokens"
unit = "token"
usd_per_unit = "0.000005"
[components.quantity_rounding]
mode = "none"
[components.quantity_range]
meter = "input_tokens"
min = "1000"
''')
    def replace(price):
        price.clear()
        price.update(pricing)
    assert price_mutation(replace, endpoint=True) == []
    assert "max" not in pricing["components"][0]["quantity_range"]
    assert "increment" not in pricing["components"][0]["quantity_rounding"]


def test_missing_component_rate_is_unknown_not_zero():
    assert price_mutation(lambda price: price["components"][0].pop("usd_per_unit"))
    assert mutate(add_binding) == []  # known provider can omit the entire unknown price


def test_ceil_cannot_omit_increment():
    assert price_mutation(lambda price: price["components"][0].update(quantity_rounding={"mode": "ceil"}))


@pytest.mark.parametrize("disposition", [[], {}, 1, None])
def test_malformed_coverage_disposition_reports_errors_without_crashing(disposition):
    def edit(card):
        add_binding(card)
        card["provider_coverage"]["example"]["disposition"] = disposition
    assert mutate(edit)


@pytest.mark.parametrize("number", [float("nan"), float("inf"), -float("inf")])
def test_price_conditions_are_finite_json(number):
    assert price_mutation(lambda price: price["components"][0].update(when={"properties": {"quantity": {"maximum": number}}}))


@pytest.mark.parametrize("qualification", [
    {"notes": "Regular rate is not established"},
    {"source_url": SOURCE},
    {"source_url": "https://token:secret@example.com", "notes": "Unknown rate"},
    {"source_url": SOURCE, "notes": "Unknown rate", "guessed_price": 1},
])
def test_unknown_provider_fact_qualifications_need_a_public_source(qualification):
    def edit(card):
        add_binding(card)
        card["providers"]["example"]["qualifications"] = [qualification]
    assert mutate(edit)


def test_verified_provider_can_qualify_missing_regular_price():
    def edit(card):
        add_binding(card)
        card["providers"]["example"]["qualifications"] = [{"source_url": SOURCE, "notes": "The public endpoint is documented but no regular rate is published."}]
    assert mutate(edit) == []
