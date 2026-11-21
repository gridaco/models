"""Agent model profiles resolve exact selectors and canonical text cards."""

import json

import pytest

import build
import check

SCHEMA = check.load(build.AGENT_MODELS_SCHEMA)
SOURCE_URL = "https://example.com/model-selection"
PROFILE_ID = "example/agent-chat"
SELECTOR = "Model.V1"
TEXT_ID = "example/model.v1"
IMAGE_ID = "example/image.v1"
FACTS = {"text.catalog": {TEXT_ID: {"id": TEXT_ID}}, "image.models": {IMAGE_ID: {"id": IMAGE_ID}}}


@pytest.fixture
def agent_models():
    return {
        "$schema": SCHEMA["$id"],
        "profiles": {
            PROFILE_ID: {
                "label": "Example Agent",
                "source_url": SOURCE_URL,
                "models": {
                    SELECTOR: {
                        "canonical_model_id": TEXT_ID,
                        "source_url": SOURCE_URL,
                        "modes": {"fast": {"service_tier": "priority", "source_url": SOURCE_URL}},
                    },
                    "example/alias": {"canonical_model_id": TEXT_ID, "source_url": SOURCE_URL},
                },
            },
        },
    }


def test_exact_selectors_can_share_a_canonical_model(agent_models):
    assert list(check.agent_model_errors(agent_models, SCHEMA, FACTS)) == []


@pytest.mark.parametrize("target", ["example/absent", "example/Model.V1", IMAGE_ID])
def test_rejects_targets_outside_text_catalog(agent_models, target):
    agent_models["profiles"][PROFILE_ID]["models"][SELECTOR]["canonical_model_id"] = target
    assert list(check.agent_model_errors(agent_models, SCHEMA, FACTS)) == [
        f"profiles/{PROFILE_ID}/models/{SELECTOR}: canonical_model_id {target!r} must identify a text.catalog card",
    ]


@pytest.mark.parametrize("level", ["profile", "model", "fast"])
def test_rejects_source_urls_with_credentials(agent_models, level):
    profile = agent_models["profiles"][PROFILE_ID]
    model = profile["models"][SELECTOR]
    records = {"profile": profile, "model": model, "fast": model["modes"]["fast"]}
    records[level]["source_url"] = "https://user@example.com/selection"
    errors = list(check.agent_model_errors(agent_models, SCHEMA, FACTS))
    assert len(errors) == 1
    assert "absolute HTTPS URL without credentials" in errors[0]


def test_fast_requires_evidence_and_keeps_the_base_selector(agent_models):
    mode = agent_models["profiles"][PROFILE_ID]["models"][SELECTOR]["modes"]["fast"]
    mode.pop("source_url")
    mode["model"] = "Model.V1-Fast"
    errors = list(check.agent_model_errors(agent_models, SCHEMA, FACTS))
    assert len(errors) == 2
    assert any("'source_url' is a required property" in error for error in errors)
    assert any("'model' was unexpected" in error for error in errors)


def test_build_sorts_selectors_without_normalizing_them(tmp_path, monkeypatch):
    root = tmp_path / "agent-models"
    profile_path = root / "example" / "agent-chat.toml"
    profile_path.parent.mkdir(parents=True)
    profile_path.write_text(f'''
label = "Example Agent"
source_url = "{SOURCE_URL}"
[models."example/alias"]
canonical_model_id = "{TEXT_ID}"
source_url = "{SOURCE_URL}"
[models."{SELECTOR}"]
canonical_model_id = "{TEXT_ID}"
source_url = "{SOURCE_URL}"
''', encoding="utf-8")
    monkeypatch.setattr(build, "AGENT_MODELS_SOURCE", root)
    outputs, errors = build.build()
    assert errors == []
    document = json.loads(outputs[build.AGENT_MODELS_JSON])
    assert list(document["profiles"][PROFILE_ID]["models"]) == [SELECTOR, "example/alias"]
    assert list(check.agent_model_errors(document, SCHEMA, FACTS)) == []


def test_source_rejects_duplicate_selectors_and_misplaced_profiles(tmp_path):
    folder = tmp_path / "example"
    folder.mkdir()
    (folder / "agent-chat.toml").write_text('[models."same"]\n[models."same"]\n', encoding="utf-8")
    (tmp_path / "misplaced.toml").write_text("", encoding="utf-8")
    profiles, errors = build.load_agent_profiles(tmp_path)
    assert profiles == {}
    assert len(errors) == 2
    assert "agent-models/example/agent-chat.toml: Cannot declare" in errors[0]
    assert "agent-models/misplaced.toml: expected agent-models/<owner>/<surface>.toml" in errors[1]


def test_source_rejects_stale_agent_models():
    assert "catalogue/agent-models.json is out of date" in "\n".join(
        check.source_errors({build.AGENT_MODELS_JSON: b"{}\n"}),
    )
