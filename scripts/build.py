"""Generate `catalogue/facts.json` from the authored cards in `models/`.

Usage:
    uv run scripts/build.py           # write catalogue/facts.json
    uv run scripts/build.py --check   # exit 1 if catalogue/facts.json is out of date

`models/` is the source. Never edit `catalogue/facts.json` by hand.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from cards import assemble, dumps, layout_errors, load_cards

ROOT = Path(__file__).resolve().parent.parent
MODELS = ROOT / "models"
FACTS = ROOT / "catalogue" / "facts.json"
FACTS_SCHEMA = ROOT / "catalogue" / "schemas" / "facts.schema.json"


def sections() -> list[str]:
    """The facts.json sections, in the order the schema requires them."""
    with FACTS_SCHEMA.open(encoding="utf-8") as f:
        return json.load(f)["required"]


def build() -> tuple[str, list[str]]:
    cards = load_cards(MODELS)
    names = sections()
    return dumps(assemble(cards, names)), list(layout_errors(cards, names))


def main() -> int:
    text, errors = build()
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        return 1
    current = FACTS.read_text(encoding="utf-8") if FACTS.exists() else None
    if "--check" in sys.argv[1:]:
        if current != text:
            print(f"{FACTS.relative_to(ROOT)} is out of date: run uv run scripts/build.py", file=sys.stderr)
            return 1
        print(f"ok: {FACTS.relative_to(ROOT)} matches models/")
        return 0
    if current != text:
        FACTS.write_text(text, encoding="utf-8")
        print(f"wrote {FACTS.relative_to(ROOT)}")
    else:
        print(f"{FACTS.relative_to(ROOT)} already up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
