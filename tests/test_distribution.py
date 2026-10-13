"""Source and weight distribution facts belong to models, not hosted endpoints."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("distribution_check", ROOT / "scripts" / "check.py")
check = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(check)

CATALOGUE = check.load(check.MODELS_JSON)
SCHEMA = check.load(check.MODELS_SCHEMA)
MODEL_SECTIONS = tuple(
    section for section in CATALOGUE if section not in {"$schema", "three_d.rig_check.operation"}
)
SOURCE = "https://model.example/releases/example"
CODE_URL = "https://github.com/example/model"
WEIGHTS_URL = "https://huggingface.co/example/model"
DISTRIBUTION = {
    "source_url": SOURCE,
    "code": {
        "repository_url": CODE_URL,
        "license": {"name": "MIT", "url": f"{CODE_URL}/blob/main/LICENSE"},
    },
    "weights": [
        {
            "id": "example-4b",
            "url": WEIGHTS_URL,
            "license": {"name": "Example Weights License", "url": f"{WEIGHTS_URL}/blob/main/LICENSE"},
            "access": "gated",
        }
    ],
}
ENDPOINT = {
    "id": "provider/example",
    "input": "text",
    "source_url": "https://provider.example/models/example/api",
}


def first(facts, section="image.models"):
    return next(iter(facts[section].values()))


def validate(distribution=DISTRIBUTION, section="image.models"):
    facts = copy.deepcopy(CATALOGUE)
    first(facts, section)["distribution"] = copy.deepcopy(distribution)
    return check.check(facts, SCHEMA)


def test_omitted_distribution_preserves_existing_cards():
    facts = copy.deepcopy(CATALOGUE)
    for section in MODEL_SECTIONS:
        for card in facts[section].values():
            card.pop("distribution", None)
    assert check.check(facts, SCHEMA) == []


@pytest.mark.parametrize("section", MODEL_SECTIONS)
def test_distribution_is_intrinsic_to_every_model_family(section):
    assert validate(section=section) == []


@pytest.mark.parametrize(
    "distribution",
    [
        {"source_url": SOURCE, "code": {"repository_url": CODE_URL}},
        {"source_url": SOURCE, "weights": [{"url": WEIGHTS_URL}]},
        {
            "source_url": SOURCE,
            "code": {"repository_url": CODE_URL},
            "weights": [{"url": WEIGHTS_URL}],
        },
    ],
)
def test_code_weights_licenses_and_access_are_independent_optional_facts(distribution):
    assert validate(distribution) == []


@pytest.mark.parametrize("access", ["public", "gated"])
def test_weight_access_records_published_access_conditions(access):
    distribution = copy.deepcopy(DISTRIBUTION)
    distribution["weights"][0]["access"] = access
    assert validate(distribution) == []


@pytest.mark.parametrize(
    "distribution",
    [
        {},
        {"source_url": SOURCE},
        {"code": {"repository_url": CODE_URL}},
        {"source_url": SOURCE, "code": {}},
        {"source_url": SOURCE, "weights": []},
        {"source_url": SOURCE, "weights": [{}]},
        {"source_url": SOURCE, "code": None},
        {"source_url": SOURCE, "weights": None},
    ],
)
def test_distribution_requires_provenance_and_at_least_one_usable_distribution(distribution):
    assert validate(distribution)


@pytest.mark.parametrize("kind", ["code", "weights"])
@pytest.mark.parametrize("missing", ["name", "url"])
def test_present_license_requires_its_name_and_source_link(kind, missing):
    distribution = copy.deepcopy(DISTRIBUTION)
    target = distribution["code"] if kind == "code" else distribution["weights"][0]
    target["license"].pop(missing)
    assert validate(distribution)


@pytest.mark.parametrize(
    "path",
    [
        ("source_url",),
        ("code", "repository_url"),
        ("code", "license", "name"),
        ("code", "license", "url"),
        ("weights", 0, "id"),
        ("weights", 0, "url"),
        ("weights", 0, "license", "name"),
        ("weights", 0, "license", "url"),
    ],
)
def test_present_distribution_identifiers_and_links_cannot_be_empty(path):
    distribution = copy.deepcopy(DISTRIBUTION)
    target = distribution
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = ""
    assert validate(distribution)


@pytest.mark.parametrize(
    "path",
    [
        ("source_url",),
        ("code", "repository_url"),
        ("code", "license", "url"),
        ("weights", 0, "url"),
        ("weights", 0, "license", "url"),
    ],
)
@pytest.mark.parametrize(
    "url",
    [
        "http://model.example/artifact",
        "/artifacts/model",
        "https://",
        "https://user:password@model.example/artifact",
        "https://user@model.example/artifact",
    ],
)
def test_every_distribution_link_is_absolute_https_without_credentials(path, url):
    distribution = copy.deepcopy(DISTRIBUTION)
    target = distribution
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = url
    assert validate(distribution)


@pytest.mark.parametrize("access", ["open", "private", "unknown", "", True])
def test_weight_access_does_not_infer_other_permissions(access):
    distribution = copy.deepcopy(DISTRIBUTION)
    distribution["weights"][0]["access"] = access
    assert validate(distribution)


@pytest.mark.parametrize(
    "path, key",
    [
        ((), "open_source"),
        ((), "commercial_use"),
        (("code",), "commercial_use"),
        (("code", "license"), "approved"),
        (("weights", 0), "commercial_use"),
        (("weights", 0, "license"), "approved"),
    ],
)
def test_distribution_objects_do_not_accept_inferred_rights_or_arbitrary_fields(path, key):
    distribution = copy.deepcopy(DISTRIBUTION)
    target = distribution
    for part in path:
        target = target[part]
    target[key] = True
    assert validate(distribution)


def test_distinct_exact_variants_can_share_one_weights_repository():
    distribution = {
        "source_url": SOURCE,
        "weights": [
            {"id": "example-4b", "url": WEIGHTS_URL},
            {"id": "example-8b", "url": WEIGHTS_URL},
        ],
    }
    assert validate(distribution) == []


def test_distinct_weights_repositories_do_not_require_invented_variant_ids():
    distribution = {
        "source_url": SOURCE,
        "weights": [
            {"url": f"{WEIGHTS_URL}-small"},
            {"url": f"{WEIGHTS_URL}-large"},
        ],
    }
    assert validate(distribution) == []


def test_exact_variant_ids_cannot_repeat_even_with_different_repository_urls():
    distribution = {
        "source_url": SOURCE,
        "weights": [
            {"id": "example-4b", "url": WEIGHTS_URL},
            {"id": "example-4b", "url": f"{WEIGHTS_URL}-mirror"},
        ],
    }
    assert validate(distribution)


@pytest.mark.parametrize("ids", [(None, None), (None, "example-4b"), ("example-4b", None)])
def test_repeated_weights_repository_requires_distinct_explicit_variant_ids(ids):
    weights = [{"url": WEIGHTS_URL}, {"url": WEIGHTS_URL}]
    for weight, variant_id in zip(weights, ids):
        if variant_id is not None:
            weight["id"] = variant_id
    assert validate({"source_url": SOURCE, "weights": weights})


def test_distribution_is_not_a_hosted_provider_binding_fact():
    facts = copy.deepcopy(CATALOGUE)
    binding = next(iter(first(facts)["providers"].values()))
    binding["distribution"] = copy.deepcopy(DISTRIBUTION)
    assert check.check(facts, SCHEMA)


@pytest.mark.parametrize("placement", ["binding", "model", "operation"])
def test_distribution_cannot_be_attached_to_endpoint_variants(placement):
    facts = copy.deepcopy(CATALOGUE)
    if placement == "binding":
        target = next(iter(first(facts)["providers"].values()))
    elif placement == "model":
        target = first(facts, "three_d.models")
    else:
        target = facts["three_d.rig_check.operation"]
    endpoint = copy.deepcopy(ENDPOINT)
    endpoint["distribution"] = copy.deepcopy(DISTRIBUTION)
    target["endpoints"] = [endpoint]
    assert check.check(facts, SCHEMA)


def test_distribution_is_not_a_rig_check_operation_fact():
    facts = copy.deepcopy(CATALOGUE)
    facts["three_d.rig_check.operation"]["distribution"] = copy.deepcopy(DISTRIBUTION)
    assert check.check(facts, SCHEMA)
