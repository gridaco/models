"""Read the authored cards in `models/` and project them to `catalogue/facts.json`.

Layout: `models/<lab>/<model>/card.toml`, one directory per card.

- `<lab>` is the card's `vendor`, or the first segment of its `id` when the card has no
  `vendor`.
- `<model>` is the `id` without its first segment (`openai/gpt-5.5` -> `gpt-5.5`), or the
  whole `id` when it has none (`eleven_v3`).

A card holds its contract fields plus two authoring keys that are not projected:

- `section`: the `facts.json` section the card belongs to, e.g. `"image.models"`.
- `null_keys`: dotted paths emitted as JSON `null`, which TOML cannot express.

A section that is a single object rather than a table of cards is authored as
`models/<provider>/<binding_id>/operation.toml`.
"""

from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

CARD_FILE = "card.toml"
OPERATION_FILE = "operation.toml"
AUTHORING_KEYS = ("section", "null_keys")


@dataclass
class Card:
    path: str  # directory relative to models/, posix
    file: str  # CARD_FILE or OPERATION_FILE
    data: dict[str, Any]


def load_cards(root: Path) -> list[Card]:
    cards = []
    for file in sorted(root.rglob("*.toml")):
        with file.open("rb") as f:
            data = tomllib.load(f)
        cards.append(Card(file.parent.relative_to(root).as_posix(), file.name, data))
    return cards


def expected_path(card: Card) -> str | None:
    data = card.data
    if card.file == OPERATION_FILE:
        provider, binding = data.get("provider"), data.get("binding_id")
        if isinstance(provider, str) and isinstance(binding, str):
            return f"{provider}/{binding}"
        return None
    card_id = data.get("id")
    if not isinstance(card_id, str) or not card_id:
        return None
    head, _, tail = card_id.partition("/")
    lab = data.get("vendor") or (head if tail else None)
    if not isinstance(lab, str) or not lab:
        return None
    return f"{lab}/{tail or card_id}"


def layout_errors(cards: list[Card], sections: list[str]) -> Iterator[str]:
    seen: dict[tuple[str, str], str] = {}
    dirs = {card.path for card in cards}
    for card in cards:
        where = f"models/{card.path}/{card.file}"
        if card.file not in (CARD_FILE, OPERATION_FILE):
            yield f"{where}: unexpected file; a card is named {CARD_FILE}"
            continue
        section = card.data.get("section")
        if section not in sections:
            yield f"{where}: section {section!r} is not a facts.json section"
        elif card.file == OPERATION_FILE and not section.endswith(".operation"):
            yield f"{where}: an operation belongs to an .operation section"
        elif card.file == CARD_FILE and section.endswith(".operation"):
            yield f"{where}: an .operation section is authored as {OPERATION_FILE}"
        expected = expected_path(card)
        if expected is None:
            yield f"{where}: cannot derive its directory (missing id, vendor, or binding_id)"
        elif card.path != expected:
            yield f"{where}: belongs in models/{expected}/"
        key = (str(section), str(card.data.get("id", card.path)))
        if key in seen:
            yield f"{where}: duplicates {seen[key]}"
        seen[key] = where
        if any(other.startswith(card.path + "/") for other in dirs):
            yield f"{where}: a card directory cannot contain another card"
        null_keys = card.data.get("null_keys", [])
        if not isinstance(null_keys, list) or not all(isinstance(k, str) for k in null_keys):
            yield f"{where}: null_keys must be a list of dotted paths"


def project(card: Card) -> dict[str, Any]:
    data = {k: v for k, v in card.data.items() if k not in AUTHORING_KEYS}
    for dotted in card.data.get("null_keys", []):
        *parents, leaf = dotted.split(".")
        target = data
        for part in parents:
            target = target.setdefault(part, {})
        target[leaf] = None
    return data


def assemble(cards: list[Card], sections: list[str]) -> dict[str, Any]:
    """Build facts.json: sections in schema order, cards sorted by id."""
    facts: dict[str, Any] = {section: {} for section in sections}
    for card in sorted(cards, key=lambda c: str(c.data.get("id", ""))):
        section = card.data.get("section")
        if section not in facts:
            continue
        if card.file == OPERATION_FILE:
            facts[section] = project(card)
        else:
            facts[section][card.data["id"]] = project(card)
    return facts


def dumps(facts: dict[str, Any]) -> str:
    return json.dumps(facts, indent=2, ensure_ascii=False) + "\n"
