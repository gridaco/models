"""Illustrative scenarios have explicit manual provenance, separate from tariffs."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("illustrative_check", ROOT / "scripts" / "check.py")
check = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(check)
CATALOGUE = check.load(check.MODELS_JSON)
SCHEMA = check.load(check.MODELS_SCHEMA)
SOURCE = "https://provider.example/models/pricing"
EXAMPLE = {
    "amount": "0.0969",
    "currency": "USD",
    "scenario": "One 2048x2048 medium-quality image edit.",
    "coverage": "Includes output, reference and prompt tokens; excludes further reasoning.",
    "provenance": {
        "maintenance": "manual",
        "description": "Manually calculated from the provider's published worked example.",
        "reviewed_on": "2026-11-13",
    },
}


def fixture(scope="binding"):
    facts = copy.deepcopy(CATALOGUE)
    if scope.startswith("binding"):
        card = next(iter(facts["image.models"].values()))
        target = {"provider": "example", "id": "example/image-model"}
        card["providers"]["example"] = target
    elif scope.startswith("operation"):
        target = facts["three_d.rig_check.operation"]
    else:
        target = next(iter(facts["three_d.models"].values()))
    if scope.endswith("endpoint"):
        target["endpoints"] = [{"id": "example/edit", "input": "image", "source_url": SOURCE}]
        target = target["endpoints"][0]
    target["illustrative_costs"] = [copy.deepcopy(EXAMPLE)]
    return facts, target


def errors(callback=lambda example: None, *, scope="binding"):
    facts, target = fixture(scope)
    callback(target["illustrative_costs"][0])
    return check.check(facts, SCHEMA)


@pytest.mark.parametrize("scope", [
    "binding", "binding_endpoint", "direct", "direct_endpoint", "operation", "operation_endpoint",
])
def test_manual_examples_without_urls_are_valid_at_their_provider_scope(scope):
    facts, target = fixture(scope)
    assert "source_urls" not in target["illustrative_costs"][0]["provenance"]
    assert check.check(facts, SCHEMA) == []


def test_legacy_catalogue_without_illustrative_costs_remains_valid():
    assert check.check(CATALOGUE, SCHEMA) == []


@pytest.mark.parametrize("currency", ["USD", "CNY"])
def test_currency_is_preserved_without_conversion(currency):
    assert errors(lambda example: example.update(amount="0.247309", currency=currency)) == []


@pytest.mark.parametrize("amount", ["0", "0.0", "0.000000001", "1000.2500"])
def test_exact_nonnegative_decimal_strings_preserve_small_and_rounded_amounts(amount):
    assert errors(lambda example: example.update(amount=amount)) == []


@pytest.mark.parametrize("amount", [
    0, 0.0969, True, None, float("nan"), float("inf"),
    "", " ", "-1", "-0", "+1", ".1", "1.", "01", "0.1.2",
    "1e-4", "1E4", "NaN", "Infinity", "0,01", " 0.1", "0.1 ", "0.1\n", "0.1\t",
])
def test_invalid_or_inexact_amount_representations_are_rejected(amount):
    assert errors(lambda example: example.update(amount=amount))


@pytest.mark.parametrize("currency", ["usd", "EUR", "US", "USDD", "ZZZ", "", None, 1])
def test_unreviewed_or_malformed_currencies_are_rejected(currency):
    assert errors(lambda example: example.update(currency=currency))


@pytest.mark.parametrize("field", ["amount", "currency", "scenario", "coverage", "provenance"])
def test_every_illustrative_cost_field_is_required(field):
    assert errors(lambda example: example.pop(field))


@pytest.mark.parametrize("field", ["scenario", "coverage"])
@pytest.mark.parametrize("value", ["", " ", "\t\n", None, [], 1])
def test_scenario_and_coverage_must_be_nonblank_text(field, value):
    assert errors(lambda example: example.update({field: value}))


@pytest.mark.parametrize("provenance", [{}, "", None, [], True])
def test_provenance_cannot_be_missing_or_an_empty_unstructured_value(provenance):
    assert errors(lambda example: example.update(provenance=provenance))


@pytest.mark.parametrize("field", ["maintenance", "description", "reviewed_on"])
def test_manual_provenance_requires_its_description_and_review_date(field):
    assert errors(lambda example: example["provenance"].pop(field))


@pytest.mark.parametrize("maintenance", ["", "automatic", "published", "Manual", True, None])
def test_maintenance_is_explicitly_manual(maintenance):
    assert errors(lambda example: example["provenance"].update(maintenance=maintenance))


@pytest.mark.parametrize("description", ["", " ", "\t\n", None, [], 1])
def test_provenance_description_cannot_be_blank_or_unstructured(description):
    assert errors(lambda example: example["provenance"].update(description=description))


@pytest.mark.parametrize("reviewed_on", [
    "2026-02-30", "2025-02-29", "2026-13-01", "2026-00-10",
    "2026-1-01", "20261113", "2026-W46-5", "2026-11-13T00:00:00Z",
    "2026-11-13 ", "", None, 20261113,
])
def test_review_date_is_a_real_canonical_calendar_day(reviewed_on):
    assert errors(lambda example: example["provenance"].update(reviewed_on=reviewed_on))


def test_leap_day_is_valid_without_a_runtime_freshness_policy():
    assert errors(lambda example: example["provenance"].update(reviewed_on="2024-02-29")) == []


def test_optional_genuine_https_sources_are_valid():
    assert errors(lambda example: example["provenance"].update(source_urls=[
        SOURCE, "https://provider.example/docs/calculator#costs",
    ])) == []


@pytest.mark.parametrize("source", [
    "http://provider.example/pricing", "/pricing", "//provider.example/pricing",
    "https://user:password@provider.example/pricing", "https://user@provider.example/pricing",
    "https:///pricing", "https://provider.example:invalid/pricing",
    "https://provider.example:99999/pricing", "https://[broken/pricing",
    "https://provider.example/pricing\n", "https://provider.example/pricing\t",
    "https://provider.example/pricing page", "https://bad host.example/pricing", "", None, 1,
])
def test_optional_sources_are_absolute_safe_https_urls(source):
    assert errors(lambda example: example["provenance"].update(source_urls=[source]))


@pytest.mark.parametrize("sources", [[], [SOURCE, SOURCE], SOURCE, None, {}])
def test_present_source_list_is_nonempty_unique_and_structured(sources):
    assert errors(lambda example: example["provenance"].update(source_urls=sources))


@pytest.mark.parametrize("field", ["unit", "id", "basis", "parameters", "unknown"])
def test_examples_do_not_accept_extra_meters_or_an_execution_dsl(field):
    assert errors(lambda example: example.update({field: "example"}))


@pytest.mark.parametrize("field", ["source_url", "basis", "manual", "unknown"])
def test_provenance_rejects_unknown_fields(field):
    assert errors(lambda example: example["provenance"].update({field: "example"}))


@pytest.mark.parametrize("examples", [None, {}, "example", [], [None], [False], [{}]])
def test_illustrative_costs_is_a_nonempty_array_of_records(examples):
    facts, target = fixture()
    target["illustrative_costs"] = examples
    assert check.check(facts, SCHEMA)


def test_identical_examples_are_not_repeated():
    facts, target = fixture()
    target["illustrative_costs"].append(copy.deepcopy(EXAMPLE))
    assert check.check(facts, SCHEMA)


def test_multi_provider_model_cannot_publish_global_cost_examples():
    facts = copy.deepcopy(CATALOGUE)
    card = next(iter(facts["image.models"].values()))
    card["illustrative_costs"] = [copy.deepcopy(EXAMPLE)]
    assert any("direct provider" in error for error in check.check(facts, SCHEMA))


def test_canonical_card_endpoint_cannot_publish_cost_examples_without_a_direct_provider():
    facts = copy.deepcopy(CATALOGUE)
    card = next(iter(facts["image.models"].values()))
    card["endpoints"] = [{
        "id": "example/edit", "input": "image", "source_url": SOURCE,
        "illustrative_costs": [copy.deepcopy(EXAMPLE)],
    }]
    assert any("direct provider" in error for error in check.check(facts, SCHEMA))


@pytest.mark.parametrize("scope", ["direct", "direct_endpoint", "operation", "operation_endpoint"])
@pytest.mark.parametrize("provider", [None, "", " \t", False])
def test_card_scope_requires_a_nonempty_direct_provider_including_singletons(scope, provider):
    facts, target = fixture(scope)
    if scope.startswith("operation"):
        target = facts["three_d.rig_check.operation"]
    elif scope.endswith("endpoint"):
        target = next(iter(facts["three_d.models"].values()))
    if provider is None:
        target.pop("provider", None)
    else:
        target["provider"] = provider
    assert any("direct provider" in error for error in check.check(facts, SCHEMA))


@pytest.mark.parametrize("scope", ["binding", "binding_endpoint"])
@pytest.mark.parametrize("provider", [None, "", " \t", False])
def test_binding_and_its_endpoints_require_a_nonempty_binding_provider(scope, provider):
    facts, _ = fixture(scope)
    card = next(iter(facts["image.models"].values()))
    binding = card["providers"].pop("example")
    if provider is None:
        binding.pop("provider")
        key = "example"
    else:
        binding["provider"] = provider
        # Matching blank keys ensure this is not merely the existing key-mismatch check.
        key = provider if isinstance(provider, str) else "example"
    card["providers"][key] = binding
    assert any("nonempty binding provider" in error for error in check.check(facts, SCHEMA))


@pytest.mark.parametrize("invalid_price", [
    {"currency": "USD", "components": [{"meter": "output", "unit": "token", "usd_per_unit": "0.00003"}]},
    {"source_url": SOURCE, "currency": "USD", "components": [{"meter": "output", "unit": "token", "usd_per_unit": "NaN"}]},
    {"source_url": "https://user:password@provider.example/pricing", "currency": "USD", "components": [{"meter": "output", "unit": "token", "usd_per_unit": "0.00003"}]},
])
def test_manual_examples_do_not_relax_published_price_sources_or_amounts(invalid_price):
    facts, target = fixture()
    target["published_pricing"] = invalid_price
    assert check.check(facts, SCHEMA)
