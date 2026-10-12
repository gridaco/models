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
    assembled = cards.assemble(CARDS, SECTIONS, check.build.schema_id())
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
