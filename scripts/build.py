"""Generate the catalogue from the authored source in `models/` and `agents/`.

- `catalogue/models.json` from the model cards (`models/<lab>/<model>/card.toml`)
- `catalogue/labs.json` from the lab files (`models/<lab>/lab.toml`)
- `catalogue/logos/<lab>.<ext>`, copied from each lab's logo (`models/<lab>/logo.<ext>`)
- `catalogue/agents.json` from agent cards (`agents/<agent-id>.toml`)
- `.github/images/release-index*.svg` from the generated models and labs

Usage:
    uv run scripts/build.py           # write the generated files
    uv run scripts/build.py --check   # exit 1 if a generated file is out of date

Edit the authored TOML, then regenerate the JSON.
"""

from __future__ import annotations

import json
import sys
import tomllib
from pathlib import Path
from typing import Any

from cards import (
    assemble,
    assemble_labs,
    dumps,
    layout_errors,
    load_cards,
    load_labs,
    logo_output,
)

ROOT = Path(__file__).resolve().parent.parent
MODELS = ROOT / "models"
MODELS_JSON = ROOT / "catalogue" / "models.json"
LABS = ROOT / "catalogue" / "labs.json"
LOGOS = ROOT / "catalogue" / "logos"
MODELS_SCHEMA = ROOT / "catalogue" / "schemas" / "models.schema.json"
AGENTS_SOURCE = ROOT / "agents"
AGENTS_JSON = ROOT / "catalogue" / "agents.json"
AGENTS_SCHEMA = ROOT / "catalogue" / "schemas" / "agents.schema.json"


def sections() -> list[str]:
    """Declared family sections, with optional families after existing required ones."""
    with MODELS_SCHEMA.open(encoding="utf-8") as f:
        schema = json.load(f)
        return schema["required"] + [
            name for name in schema["properties"]
            if name != "$schema" and name not in schema["required"]
        ]


def required_sections() -> list[str]:
    with MODELS_SCHEMA.open(encoding="utf-8") as f:
        return json.load(f)["required"]


def schema_id(path: Path = MODELS_SCHEMA) -> str:
    """The schema `$id` written as the generated document's `$schema`."""
    with path.open(encoding="utf-8") as f:
        return json.load(f)["$id"]


def load_agent_cards(root: Path) -> tuple[dict[str, Any], list[str]]:
    agents = {}
    errors = []
    for path in sorted(root.rglob("*.toml")):
        relative = path.relative_to(root)
        location = f"agents/{relative.as_posix()}"
        if len(relative.parts) != 1:
            errors.append(f"{location}: expected agents/<agent-id>.toml")
            continue
        try:
            with path.open("rb") as f:
                agent = tomllib.load(f)
        except (tomllib.TOMLDecodeError, UnicodeDecodeError) as error:
            errors.append(f"{location}: {error}")
            continue
        if isinstance(models := agent.get("models"), dict):
            agent["models"] = dict(sorted(models.items()))
        agents[path.stem] = agent
    return agents, errors


def build() -> tuple[dict[Path, bytes], list[str]]:
    """Return the content of each generated file, and any layout errors."""
    cards = load_cards(MODELS)
    labs = load_labs(MODELS)
    names = sections()
    agents, errors = load_agent_cards(AGENTS_SOURCE)
    errors.extend(layout_errors(cards, names))
    documents = (
        (MODELS_JSON, assemble(cards, names, schema_id(), required_sections())),
        (LABS, assemble_labs(labs)),
        (AGENTS_JSON, {"$schema": schema_id(AGENTS_SCHEMA), "agents": agents}),
    )
    outputs = {}
    for path, document in documents:
        try:
            outputs[path] = dumps(document).encode()
        except (TypeError, ValueError) as error:
            return {}, [
                *errors,
                f"{path.relative_to(ROOT)}: cannot generate valid JSON ({error})",
            ]
    for lab in labs:
        path, name = logo_output(lab), lab.data.get("logo", {}).get("file")
        if path and name in lab.files:
            outputs[ROOT / "catalogue" / path] = lab.files[name]
    return outputs, errors


def stale(outputs: dict[Path, bytes], committed: dict[Path, bytes] | None = None) -> list[Path]:
    """The generated files whose committed content differs from what the source generates."""
    def read(path: Path) -> bytes | None:
        if committed is not None and path in committed:
            return committed[path]
        return path.read_bytes() if path.exists() else None

    return [path for path, content in outputs.items() if read(path) != content]


def orphans(outputs: dict[Path, bytes]) -> list[Path]:
    """Files in catalogue/logos/ that no lab generates."""
    if not LOGOS.exists():
        return []
    return [path for path in sorted(LOGOS.iterdir()) if path not in outputs and not path.name.startswith(".")]


def main() -> int:
    outputs, errors = build()
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        return 1
    # Keep README images outside the published catalogue snapshot.
    from readme_preview import render_previews

    logos = {path.relative_to(LABS.parent).as_posix(): data for path, data in outputs.items() if path.parent == LOGOS}
    previews = render_previews(outputs[MODELS_JSON], outputs[LABS], logos)
    outputs.update({ROOT / ".github" / "images" / name: data for name, data in previews.items()})
    out_of_date, extra = stale(outputs), orphans(outputs)
    if "--check" in sys.argv[1:]:
        for path in out_of_date:
            print(f"{path.relative_to(ROOT)} is out of date: run uv run scripts/build.py", file=sys.stderr)
        for path in extra:
            print(f"{path.relative_to(ROOT)} is not generated by any lab: run uv run scripts/build.py", file=sys.stderr)
        if out_of_date or extra:
            return 1
        print("ok: generated files match the authored source")
        return 0
    for path in out_of_date:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(outputs[path])
        print(f"wrote {path.relative_to(ROOT)}")
    for path in extra:
        path.unlink()
        print(f"removed {path.relative_to(ROOT)}")
    if not out_of_date and not extra:
        print("generated files already up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
