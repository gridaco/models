"""Generate the catalogue contract from the authored source in `models/`.

- `catalogue/facts.json` from the model cards (`models/<lab>/<model>/card.toml`)
- `catalogue/labs.json` from the lab files (`models/<lab>/lab.toml`)

Usage:
    uv run scripts/build.py           # write the generated files
    uv run scripts/build.py --check   # exit 1 if a generated file is out of date

`models/` is the source. Never edit the generated files by hand.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from cards import assemble, assemble_labs, dumps, layout_errors, load_cards, load_labs

ROOT = Path(__file__).resolve().parent.parent
MODELS = ROOT / "models"
FACTS = ROOT / "catalogue" / "facts.json"
LABS = ROOT / "catalogue" / "labs.json"
FACTS_SCHEMA = ROOT / "catalogue" / "schemas" / "facts.schema.json"


def sections() -> list[str]:
    """The facts.json sections, in the order the schema requires them."""
    with FACTS_SCHEMA.open(encoding="utf-8") as f:
        return json.load(f)["required"]


def build() -> tuple[dict[Path, str], list[str]]:
    """Return the text of each generated file, and any layout errors."""
    cards = load_cards(MODELS)
    names = sections()
    outputs = {
        FACTS: dumps(assemble(cards, names)),
        LABS: dumps(assemble_labs(load_labs(MODELS))),
    }
    return outputs, list(layout_errors(cards, names))


def stale(outputs: dict[Path, str], committed: dict[Path, str] | None = None) -> list[Path]:
    """The generated files whose committed text differs from what the source generates."""
    def read(path: Path) -> str | None:
        if committed is not None and path in committed:
            return committed[path]
        return path.read_text(encoding="utf-8") if path.exists() else None

    return [path for path, text in outputs.items() if read(path) != text]


def main() -> int:
    outputs, errors = build()
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        return 1
    out_of_date = stale(outputs)
    if "--check" in sys.argv[1:]:
        for path in out_of_date:
            print(f"{path.relative_to(ROOT)} is out of date: run uv run scripts/build.py", file=sys.stderr)
        if out_of_date:
            return 1
        print("ok: generated files match models/")
        return 0
    for path in out_of_date:
        path.write_text(outputs[path], encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")
    if not out_of_date:
        print("generated files already up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
