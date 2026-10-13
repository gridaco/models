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

MODELS_JSON = check.load(check.MODELS_JSON)
SCHEMA = check.load(check.MODELS_SCHEMA)


def mutated(mutate):
    facts = copy.deepcopy(MODELS_JSON)
    mutate(facts)
    return check.check(facts, SCHEMA)


def first(section: str, facts) -> dict:
    return next(iter(facts[section].values()))


def test_catalogue_is_valid():
    assert check.check(MODELS_JSON, SCHEMA) == []


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


# The authored cards in models/ and their projection to models.json.

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
    edited = check.MODELS_JSON.read_text(encoding="utf-8").replace('"GPT-5.5"', '"GPT 5.5"', 1)
    assert any("models.json is out of date" in e for e in check.source_errors({check.MODELS_JSON: edited.encode()}))


def test_hand_edited_labs_are_reported_out_of_date():
    edited = check.LABS.read_text(encoding="utf-8").replace('"OpenAI"', '"Open AI"', 1)
    assert any("labs.json is out of date" in e for e in check.source_errors({check.LABS: edited.encode()}))


def test_cards_round_trip_every_null():
    assembled = cards.assemble(CARDS, SECTIONS, check.build.schema_id(), check.build.required_sections())
    assert assembled == MODELS_JSON


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

    assert any("is not a models.json section" in e for e in layout(mutate))


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


# Labs: models/<lab>/lab.toml, projected to catalogue/labs.json.

LABS = cards.load_labs(check.build.MODELS)


def lab_check(labs, unregistered=check.KNOWN_UNREGISTERED_LABS):
    return list(cards.lab_errors(labs, CARDS, unregistered))


def test_labs_are_valid():
    assert lab_check(LABS) == []
    assert list(check.schema_errors(check.load(check.LABS), check.load(check.LABS_SCHEMA))) == []


def test_lab_directory_needs_a_lab_toml():
    labs = [lab for lab in LABS if lab.id != "openai"]
    assert any("models/openai/: lab directory has no lab.toml" in e for e in lab_check(labs))


def test_lab_toml_needs_cards():
    labs = LABS + [cards.Lab("nobody", {"name": "Nobody", "url": "https://example.com/"})]
    assert any("lab has no cards" in e for e in lab_check(labs))


def test_stale_unregistered_lab_is_reported():
    labs = LABS + [cards.Lab("nightmareai", {"name": "x", "url": "https://example.com/"})]
    assert any("stale unregistered lab 'nightmareai'" in e for e in lab_check(labs))


def test_unregistered_lab_without_cards_is_reported():
    unregistered = check.KNOWN_UNREGISTERED_LABS | {"nobody"}
    assert any("stale unregistered lab 'nobody'" in e for e in lab_check(LABS, unregistered))


def test_lab_schema_rejects_unknown_fields():
    labs = cards.assemble_labs(LABS)
    labs["openai"]["logo"] = "openai.svg"
    assert list(check.schema_errors(labs, check.load(check.LABS_SCHEMA)))


def test_lab_toml_is_not_a_card():
    assert not any(c.file == cards.LAB_FILE for c in CARDS)


# Logos: models/<lab>/logo.<ext>, copied to catalogue/logos/<lab>.<ext>.

SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M0 0h24v24H0z"/></svg>'
LOGO = {"file": "logo.svg", "kind": "symbol", "source_url": "https://example.com/logo.svg", "retrieved": "2026-10-12"}


def logo_check(svg=SVG, logo=LOGO, files=None):
    lab = cards.Lab("example", {"name": "Example", "url": "https://example.com/", "logo": logo})
    lab.files = {"logo.svg": svg} if files is None else files
    return list(cards.logo_errors(lab))


def test_clean_svg_logo_passes():
    assert logo_check() == []


@pytest.mark.parametrize(
    "svg, problem",
    [
        (SVG.replace(b"<path", b'<script>alert(1)</script><path'), "contains <script>"),
        (SVG.replace(b"<path", b"<foreignObject/><path"), "contains <foreignObject>"),
        (SVG.replace(b"<path", b'<path onclick="x()"'), "event attribute"),
        (SVG.replace(b"<path", b'<image href="https://example.com/a.png"/><path'), "references"),
        (SVG.replace(b"<path", b'<image href="data:image/png;base64,AAAA"/><path'), "references"),
        (SVG.replace(b"<path", b'<style>path{fill:url(https://example.com/a)}</style><path'), "external url()"),
        (SVG.replace(b' viewBox="0 0 24 24"', b""), "no viewBox"),
        (b"<svg", "well-formed"),
        (b'<!DOCTYPE svg [<!ENTITY a "b">]>' + SVG, "DOCTYPE"),
    ],
)
def test_svg_logo_is_plain_artwork(svg, problem):
    assert any(problem in e for e in logo_check(svg))


def test_internal_svg_references_are_allowed():
    svg = SVG.replace(b"<path", b'<defs><linearGradient id="g"/></defs><use href="#g"/><path fill="url(#g)"')
    assert logo_check(svg) == []


def test_raster_logo_must_match_its_extension():
    logo = {**LOGO, "file": "logo.png"}
    assert any("is not a PNG" in e for e in logo_check(logo=logo, files={"logo.png": SVG}))


def test_logo_file_must_be_named_logo():
    logo = {**LOGO, "file": "brand.svg"}
    assert any("logo.file must be one of" in e for e in logo_check(logo=logo, files={"brand.svg": SVG}))


def test_logo_file_must_exist():
    assert any("does not exist" in e for e in logo_check(files={}))


def test_lab_directory_holds_no_other_files():
    assert any("unexpected file" in e for e in logo_check(files={"logo.svg": SVG, "notes.txt": b""}))


def test_lab_schema_requires_logo_provenance():
    labs = cards.assemble_labs(LABS)
    labs["openai"]["logo"] = {"path": "logos/openai.svg", "media_type": "image/svg+xml", "kind": "symbol"}
    errors = list(check.schema_errors(labs, check.load(check.LABS_SCHEMA)))
    assert any("source_url" in e for e in errors) and any("retrieved" in e for e in errors)


def test_logo_not_generated_by_any_lab_is_reported(tmp_path, monkeypatch):
    monkeypatch.setattr(check.build, "LOGOS", tmp_path)
    (tmp_path / "gone.svg").write_bytes(SVG)
    assert check.build.orphans({}) == [tmp_path / "gone.svg"]


def test_models_json_names_its_schema():
    assert next(iter(MODELS_JSON)) == "$schema"
    assert MODELS_JSON["$schema"] == SCHEMA["$id"]


def test_models_json_schema_must_be_this_schema():
    def mutate(facts):
        facts["$schema"] = "https://example.com/other.json"

    assert any("$schema" in e for e in mutated(mutate))


def test_provider_endpoint_needs_source_and_input():
    def mutate(facts):
        first("image.models", facts)["providers"]["fal"]["endpoints"] = [{"id": "test/route"}]
    assert any("required property" in e for e in mutated(mutate))


def test_provider_endpoints_cannot_repeat():
    def mutate(facts):
        endpoint = {"id": "test/route", "input": "text", "source_url": "https://example.com/api"}
        first("image.models", facts)["providers"]["fal"]["endpoints"] = [endpoint, endpoint.copy()]
    assert any("duplicate endpoint" in e for e in mutated(mutate))


def test_existing_binding_without_endpoints_remains_valid():
    assert check.check(MODELS_JSON, SCHEMA) == []


def test_text_card_requires_vendor_lab():
    def mutate(facts):
        first("text.catalog", facts).pop("vendor", None)
    assert any("requires a vendor lab" in e for e in mutated(mutate))
# Additive published calculators, serving facts, and endpoint parameters.

SOURCE = "https://provider.example/models/example/api"
CALCULATOR = {
    "source_url": SOURCE,
    "area_offset": 2000000,
    "area_divisor": 4000000,
    "short_axis_rounding": "nearest_ties_even",
    "token_rounding": "ceil",
    "quality_axes": {"low": 16, "medium": 48, "high": 96},
    "examples": [{"width": 1024, "height": 1024, "quality": "low", "output_tokens": 196, "source_url": SOURCE}],
}
TOKEN_PRICING = {
    "source_url": SOURCE,
    "unit": "usd_per_token",
    "input": "0.000005",
    "output": "0.00003",
    "tiers": [
        {"meter": "input", "minimum_input_tokens": 0, "maximum_input_tokens": 272000, "usd_per_token": "0.000005"},
        {"meter": "input", "minimum_input_tokens": 272000, "usd_per_token": "0.00001"},
    ],
}
ENDPOINT = {
    "id": "provider/example/edit", "input": "image", "source_url": SOURCE,
    "parameters": {
        "image_size.width": {"type": "integer", "minimum": 16, "maximum": 3840, "multiple_of": 16},
        "quality": {"type": "string", "enum": ["low", "medium", "high"]},
        "image_urls": {"type": "array", "min_items": 1, "max_items": 16},
    },
    "image_constraints": {"step": 16, "min_pixels": 655360, "max_pixels": 8294400, "aspect_ratio": {"max": 3}},
}


def enriched(mutate=lambda card: None):
    facts = copy.deepcopy(MODELS_JSON)
    card = first("image.models", facts)
    card.update({
        "output_token_calculator": copy.deepcopy(CALCULATOR),
        "vision_tokenization": {"source_url": SOURCE, "patch_size_px": 32, "token_multiplier": 1.2,
                                "detail_patch_budgets": {"high": 25088}, "detail_maximum_edges": {"low": 512},
                                "maximum_tokens_per_image": 4784, "token_rounding": "ceil"},
        "capabilities": {"source_url": SOURCE, "reasoning": True, "structured_output": False},
    })
    binding = card["providers"]["fal"]
    binding.update({"token_pricing": copy.deepcopy(TOKEN_PRICING),
                    "limits": {"source_url": SOURCE, "context_tokens": 272000, "max_output_tokens": 32000},
                    "endpoints": [copy.deepcopy(ENDPOINT)]})
    mutate(card)
    return check.check(facts, SCHEMA)


def test_additive_sourced_facts_validate_together():
    assert enriched() == []


@pytest.mark.parametrize("field", ["output_token_calculator", "vision_tokenization", "capabilities"])
def test_new_card_facts_require_sources(field):
    assert any("source_url" in error for error in enriched(lambda card: card[field].pop("source_url")))


def test_new_binding_facts_require_sources():
    assert any("source_url" in error for error in enriched(lambda card: card["providers"]["fal"]["token_pricing"].pop("source_url")))


@pytest.mark.parametrize("url", ["https://", "https://operator:secret@provider.example/api", "http://provider.example/api"])
def test_new_fact_urls_are_absolute_https_without_credentials(url):
    assert any("source_url" in error for error in enriched(lambda card: card["capabilities"].update(source_url=url)))


def test_calculator_cannot_carry_arbitrary_consumer_fields():
    assert any("additional" in error.lower() for error in enriched(lambda card: card["output_token_calculator"].update(preference_order=["fast", "quality"])))


def test_calculator_axes_must_be_positive():
    assert any("quality_axes" in error for error in enriched(lambda card: card["output_token_calculator"]["quality_axes"].update(low=0)))


def test_calculator_divisor_cannot_be_zero():
    assert any("area_divisor" in error for error in enriched(lambda card: card["output_token_calculator"].update(area_divisor=0)))


def test_calculator_example_quality_must_have_an_axis():
    assert any("quality has no" in error for error in enriched(lambda card: card["output_token_calculator"]["examples"][0].update(quality="unknown")))


def test_calculator_examples_are_unique_per_size_and_quality():
    def mutate(card):
        calc = card["output_token_calculator"]
        calc["examples"].append(copy.deepcopy(calc["examples"][0]))
    assert any("duplicate size/quality" in error for error in enriched(mutate))


def test_verified_output_token_example_must_match_calculator():
    assert any("does not match calculator" in error for error in enriched(lambda card: card["output_token_calculator"]["examples"][0].update(output_tokens=197)))


def test_rounded_price_example_never_requires_inferred_tokens():
    def mutate(card):
        example = card["output_token_calculator"]["examples"][0]
        example.pop("output_tokens")
        example.update(usd=0.006, usd_precision=3)
    assert enriched(mutate) == []


def test_example_requires_a_documented_token_or_price_value():
    assert any("examples" in error for error in enriched(lambda card: card["output_token_calculator"]["examples"][0].pop("output_tokens")))


def test_example_precision_requires_price():
    assert any("usd" in error for error in enriched(lambda card: card["output_token_calculator"]["examples"][0].update(usd_precision=3)))


def test_vision_rules_cannot_be_empty_source_only():
    assert any("vision_tokenization" in error for error in enriched(lambda card: card.update(vision_tokenization={"source_url": SOURCE})))


def test_vision_quantities_must_be_positive():
    assert any("maximum_tokens_per_image" in error for error in enriched(lambda card: card["vision_tokenization"].update(maximum_tokens_per_image=0)))


def test_serving_capabilities_must_be_boolean():
    assert any("capabilities" in error for error in enriched(lambda card: card["capabilities"].update(reasoning="yes")))


def test_provider_limits_must_be_positive():
    assert any("context_tokens" in error for error in enriched(lambda card: card["providers"]["fal"]["limits"].update(context_tokens=0)))


def test_token_rates_preserve_exact_decimal_strings():
    assert any("token_pricing" in error for error in enriched(lambda card: card["providers"]["fal"]["token_pricing"].update(input=0.000005)))


def test_token_price_unit_is_explicit_and_fixed():
    assert any("token_pricing" in error for error in enriched(lambda card: card["providers"]["fal"]["token_pricing"].update(unit="usd_per_million_tokens")))


def test_tiers_use_half_open_bounds_and_allow_unbounded_last_band():
    assert enriched() == []


def test_token_tiers_cannot_overlap_for_the_same_meter():
    assert any("overlapping" in error for error in enriched(lambda card: card["providers"]["fal"]["token_pricing"]["tiers"][1].update(minimum_input_tokens=271999)))


def test_token_tier_cannot_be_empty_or_reversed():
    assert any("exclusive maximum" in error for error in enriched(lambda card: card["providers"]["fal"]["token_pricing"]["tiers"][0].update(maximum_input_tokens=0)))


def test_token_tiers_may_overlap_between_distinct_meters():
    def mutate(card):
        pricing = card["providers"]["fal"]["token_pricing"]
        pricing["tiers"].append({"meter": "output", "minimum_input_tokens": 0, "usd_per_token": "0.00003"})
    assert enriched(mutate) == []


def test_endpoint_dotted_native_parameter_names_are_preserved():
    assert enriched() == []


def test_endpoint_parameters_must_have_ordered_ranges():
    assert any("minimum exceeds maximum" in error for error in enriched(lambda card: card["providers"]["fal"]["endpoints"][0]["parameters"]["image_size.width"].update(minimum=4000)))


def test_endpoint_reference_count_range_cannot_be_reversed():
    assert any("min_items exceeds max_items" in error for error in enriched(lambda card: card["providers"]["fal"]["endpoints"][0]["parameters"]["image_urls"].update(min_items=17)))


def test_endpoint_image_constraint_range_cannot_be_reversed():
    assert any("min_pixels exceeds max_pixels" in error for error in enriched(lambda card: card["providers"]["fal"]["endpoints"][0]["image_constraints"].update(min_pixels=9000000)))


def test_parameter_enum_must_not_repeat_values():
    assert any("non-unique" in error for error in enriched(lambda card: card["providers"]["fal"]["endpoints"][0]["parameters"]["quality"].update(enum=["low", "low"])))


def test_nonfinite_published_numbers_are_rejected():
    assert any("finite" in error for error in enriched(lambda card: card["providers"]["fal"]["endpoints"][0]["parameters"]["image_size.width"].update(maximum=float("inf"))))


def test_endpoint_fact_fields_cannot_hold_arbitrary_consumer_settings():
    assert any("additional" in error.lower() for error in enriched(lambda card: card["providers"]["fal"]["endpoints"][0]["parameters"]["quality"].update(default="high")))


def test_single_provider_card_can_record_sourced_endpoint_variants():
    facts = copy.deepcopy(MODELS_JSON)
    first("three_d.models", facts)["endpoints"] = [copy.deepcopy(ENDPOINT)]
    assert check.check(facts, SCHEMA) == []


def test_single_provider_endpoint_ids_cannot_repeat():
    facts = copy.deepcopy(MODELS_JSON)
    first("three_d.models", facts)["endpoints"] = [copy.deepcopy(ENDPOINT), copy.deepcopy(ENDPOINT)]
    assert any("duplicate endpoint" in error for error in check.check(facts, SCHEMA))


def test_singleton_operation_can_record_sourced_endpoint_parameters():
    facts = copy.deepcopy(MODELS_JSON)
    facts["three_d.rig_check.operation"]["endpoints"] = [copy.deepcopy(ENDPOINT)]
    assert check.check(facts, SCHEMA) == []


# Optional decision offerings use their own interface and do not inherit chat facts.

def decision_fixture():
    return {
        "id": "openai/decision-example", "label": "Decision example", "vendor": "openai",
        "underlying_model": "openai/gpt-6-luna",
        "release": {"date": None, "basis": "provider_endpoint", "source_url": "https://example.com/decisions"},
        "reference_provider": "openai",
        "providers": {
            "openai": {
                "id": "native-model", "provider": "openai", "source_url": "https://example.com/decisions",
                "decision_contract": {
                    "source_url": "https://example.com/decisions", "question_types": ["predicate", "choice", "score"],
                    "minimum_choices": 2, "maximum_choices": 255, "typed_choice_values": True,
                },
            },
        },
    }


def decision_facts():
    facts = copy.deepcopy(MODELS_JSON)
    facts["decision.models"] = {"openai/decision-example": decision_fixture()}
    return facts


def test_optional_decision_family_preserves_prior_snapshots():
    facts = copy.deepcopy(MODELS_JSON)
    facts.pop("decision.models", None)
    assert check.check(facts, SCHEMA) == []
    assert "decision.models" not in check.build.required_sections()


def test_decision_card_has_independent_identity_and_provider_contract():
    assert check.check(decision_facts(), SCHEMA) == []


@pytest.mark.parametrize("field", ["context_window", "output_limit", "cost", "tool_call", "multimodal"])
def test_decision_card_rejects_inherited_chat_fields(field):
    facts = decision_facts()
    facts["decision.models"]["openai/decision-example"][field] = 1
    assert any(field in e for e in check.check(facts, SCHEMA))


def test_decision_card_requires_a_vendor_underlying_model_and_binding():
    for field in ("vendor", "underlying_model", "providers"):
        facts = decision_facts()
        facts["decision.models"]["openai/decision-example"].pop(field)
        assert check.check(facts, SCHEMA)
    facts = decision_facts()
    facts["decision.models"]["openai/decision-example"]["providers"] = {}
    assert any("no provider bindings" in e for e in check.check(facts, SCHEMA))


def test_decision_contract_bounds_and_source_are_checked():
    facts = decision_facts()
    contract = facts["decision.models"]["openai/decision-example"]["providers"]["openai"]["decision_contract"]
    contract["minimum_choices"] = 256
    assert any("minimum_choices exceeds maximum_choices" in e for e in check.check(facts, SCHEMA))
    contract["minimum_choices"] = 2
    contract["source_url"] = "https://user:password@example.com/decisions"
    assert any("without credentials" in e for e in check.check(facts, SCHEMA))


def test_decision_contract_rejects_unknown_vocabulary():
    facts = decision_facts()
    contract = facts["decision.models"]["openai/decision-example"]["providers"]["openai"]["decision_contract"]
    contract["question_types"] = ["chat"]
    assert any("question_types" in e for e in check.check(facts, SCHEMA))


def test_optional_family_is_generated_only_when_authored():
    required = check.build.required_sections()
    old = [c for c in CARDS if c.data.get("section") != "decision.models"]
    assert "decision.models" not in cards.assemble(old, SECTIONS, check.build.schema_id(), required)
    example = cards.Card("openai/decision-example", "card.toml", {"section": "decision.models", **decision_fixture()})
    assert list(cards.layout_errors(old + [example], SECTIONS)) == []
    assembled = cards.assemble(old + [example], SECTIONS, check.build.schema_id(), required)
    assert assembled["decision.models"]["openai/decision-example"] == decision_fixture()
