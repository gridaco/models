"""Agent model cards resolve exact selectors and canonical text cards."""

import json

import pytest

import build
import check

SCHEMA = check.load(build.AGENT_MODELS_SCHEMA)
SOURCE_URL = "https://example.com/model-selection"
AGENT_ID = "example-agent"
SELECTOR = "Model.V1"
TEXT_ID = "example/model.v1"
IMAGE_ID = "example/image.v1"
FACTS = {"text.catalog": {TEXT_ID: {"id": TEXT_ID}}, "image.models": {IMAGE_ID: {"id": IMAGE_ID}}}


@pytest.fixture
def agent_models():
    return {
        "$schema": SCHEMA["$id"],
        "agents": {
            AGENT_ID: {
                "label": "Example Agent",
                "source_url": SOURCE_URL,
                "models": {
                    SELECTOR: {
                        "canonical_model_id": TEXT_ID,
                        "source_url": SOURCE_URL,
                        "modes": {
                            "fast": {"service_tier": "priority", "source_url": SOURCE_URL},
                            "ultrafast": {"service_tier": "ultrafast", "source_url": SOURCE_URL},
                        },
                    },
                    "example/alias": {"canonical_model_id": TEXT_ID, "source_url": SOURCE_URL},
                },
            },
        },
    }


def test_exact_selectors_can_share_a_canonical_model(agent_models):
    assert list(check.agent_model_errors(agent_models, SCHEMA, FACTS)) == []


def test_rejects_namespaced_agent_ids(agent_models):
    agents = agent_models["agents"]
    agents["example/agent"] = agents.pop(AGENT_ID)
    assert list(check.agent_model_errors(agent_models, SCHEMA, FACTS))


@pytest.mark.parametrize("mode", ["fast", "ultrafast"])
def test_each_speed_mode_can_appear_on_its_own(agent_models, mode):
    model = agent_models["agents"][AGENT_ID]["models"][SELECTOR]
    model["modes"] = {mode: model["modes"][mode]}
    assert list(check.agent_model_errors(agent_models, SCHEMA, FACTS)) == []


def test_modes_map_must_be_nonempty_when_present(agent_models):
    agent_models["agents"][AGENT_ID]["models"][SELECTOR]["modes"] = {}
    errors = list(check.agent_model_errors(agent_models, SCHEMA, FACTS))
    assert len(errors) == 1
    assert "non-empty" in errors[0]


@pytest.mark.parametrize("target", ["example/absent", "example/Model.V1", IMAGE_ID])
def test_rejects_targets_outside_text_catalog(agent_models, target):
    agent_models["agents"][AGENT_ID]["models"][SELECTOR]["canonical_model_id"] = target
    assert list(check.agent_model_errors(agent_models, SCHEMA, FACTS)) == [
        f"agents/{AGENT_ID}/models/{SELECTOR}: canonical_model_id {target!r} must identify a text.catalog card",
    ]


@pytest.mark.parametrize("level", ["agent", "model", "fast", "ultrafast"])
def test_rejects_source_urls_with_credentials(agent_models, level):
    agent = agent_models["agents"][AGENT_ID]
    model = agent["models"][SELECTOR]
    records = {"agent": agent, "model": model, **model["modes"]}
    records[level]["source_url"] = "https://user@example.com/selection"
    errors = list(check.agent_model_errors(agent_models, SCHEMA, FACTS))
    assert len(errors) == 1
    assert "absolute HTTPS URL without credentials" in errors[0]


@pytest.mark.parametrize("mode_name", ["fast", "ultrafast"])
def test_speed_mode_requires_evidence_and_keeps_the_base_selector(agent_models, mode_name):
    mode = agent_models["agents"][AGENT_ID]["models"][SELECTOR]["modes"][mode_name]
    mode.pop("source_url")
    mode["model"] = f"{SELECTOR}-{mode_name}"
    errors = list(check.agent_model_errors(agent_models, SCHEMA, FACTS))
    assert len(errors) == 2
    assert any("'source_url' is a required property" in error for error in errors)
    assert any("'model' was unexpected" in error for error in errors)


def test_build_sorts_selectors_without_normalizing_them(tmp_path, monkeypatch):
    root = tmp_path / "agents"
    root.mkdir()
    card_path = root / f"{AGENT_ID}.toml"
    card_path.write_text(f'''
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
    assert list(document["agents"][AGENT_ID]["models"]) == [SELECTOR, "example/alias"]
    assert list(check.agent_model_errors(document, SCHEMA, FACTS)) == []


def test_source_rejects_duplicate_selectors_and_nested_cards(tmp_path):
    folder = tmp_path / "example"
    folder.mkdir()
    (tmp_path / f"{AGENT_ID}.toml").write_text('[models."same"]\n[models."same"]\n', encoding="utf-8")
    (folder / "nested.toml").write_text("", encoding="utf-8")
    agents, errors = build.load_agent_cards(tmp_path)
    assert agents == {}
    assert len(errors) == 2
    assert any(error.startswith(f"agents/{AGENT_ID}.toml: Cannot declare") for error in errors)
    assert "agents/example/nested.toml: expected agents/<agent-id>.toml" in errors


def test_source_rejects_stale_agent_models():
    assert "catalogue/agent-models.json is out of date" in "\n".join(
        check.source_errors({build.AGENT_MODELS_JSON: b"{}\n"}),
    )
