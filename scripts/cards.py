"""Read the authored cards in `models/` and project them to `catalogue/models.json`.

Layout: `models/<lab>/<model>/card.toml`, one directory per card.

- `<lab>` is the card's `vendor`, or the first segment of its `id` when the card has no
  `vendor`.
- `<model>` is the `id` without its first segment (`openai/gpt-5.5` -> `gpt-5.5`), or the
  whole `id` when it has none (`eleven_v3`).

A card holds its contract fields plus two authoring keys that are not projected:

- `section`: the `models.json` section the card belongs to, e.g. `"image.models"`.
- `null_keys`: dotted paths emitted as JSON `null`, which TOML cannot express.

A section that is a single object rather than a table of cards is authored as
`models/<provider>/<binding_id>/operation.toml`.

Each lab directory holds a `lab.toml` (`name`, `url`, and an optional `[logo]`), projected
to `catalogue/labs.json`. A lab's logo file sits beside it as `logo.svg`, `logo.png`, or
`logo.webp`, and is copied to `catalogue/logos/<lab>.<ext>`.
"""

from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass, field
from xml.etree import ElementTree
from pathlib import Path
from typing import Any, Iterator

CARD_FILE = "card.toml"
OPERATION_FILE = "operation.toml"
LAB_FILE = "lab.toml"
LOGO_TYPES = {".svg": "image/svg+xml", ".png": "image/png", ".webp": "image/webp"}
SVG_NS = "{http://www.w3.org/2000/svg}"
AUTHORING_KEYS = ("section", "null_keys")


@dataclass
class Card:
    path: str  # directory relative to models/, posix
    file: str  # CARD_FILE or OPERATION_FILE
    data: dict[str, Any]


@dataclass
class Lab:
    id: str  # the lab directory name
    data: dict[str, Any]
    files: dict[str, bytes] = field(default_factory=dict)  # other files beside lab.toml


def load_cards(root: Path) -> list[Card]:
    cards = []
    for file in sorted(root.rglob("*.toml")):
        if file.name == LAB_FILE and file.parent.parent == root:
            continue
        with file.open("rb") as f:
            data = tomllib.load(f)
        cards.append(Card(file.parent.relative_to(root).as_posix(), file.name, data))
    return cards


def load_labs(root: Path) -> list[Lab]:
    labs = []
    for file in sorted(root.glob(f"*/{LAB_FILE}")):
        with file.open("rb") as f:
            data = tomllib.load(f)
        files = {
            other.name: other.read_bytes()
            for other in sorted(file.parent.iterdir())
            if other.is_file() and other.name != LAB_FILE and not other.name.startswith(".")
        }
        labs.append(Lab(file.parent.name, data, files))
    return labs


def svg_errors(data: bytes) -> Iterator[str]:
    """An SVG logo is plain vector artwork: no scripts, no external references."""
    try:
        text = data.decode("utf-8")
        root = ElementTree.fromstring(text)
    except (UnicodeDecodeError, ElementTree.ParseError) as error:
        yield f"is not a well-formed UTF-8 SVG ({error})"
        return
    if "<!DOCTYPE" in text or "<!ENTITY" in text:
        yield "declares a DOCTYPE or entities"
    if root.tag != f"{SVG_NS}svg":
        yield "root element is not an SVG <svg>"
    elif "viewBox" not in root.attrib:
        yield "has no viewBox"
    if re.search(r"url\(\s*['\"]?(?!#)", text):
        yield "references an external url()"
    for element in root.iter():
        tag = str(element.tag).rsplit("}", 1)[-1]
        if tag in ("script", "foreignObject"):
            yield f"contains <{tag}>"
        for name, value in element.attrib.items():
            attribute = name.rsplit("}", 1)[-1]
            if attribute.lower().startswith("on"):
                yield f"has an event attribute ({attribute})"
            if attribute == "href" and not value.startswith("#"):
                yield f"references {value[:60]!r}"


def raster_errors(data: bytes, suffix: str) -> Iterator[str]:
    if suffix == ".png" and not data.startswith(b"\x89PNG\r\n\x1a\n"):
        yield "is not a PNG file"
    if suffix == ".webp" and not (data[:4] == b"RIFF" and data[8:12] == b"WEBP"):
        yield "is not a WebP file"


def logo_errors(lab: Lab) -> Iterator[str]:
    where = f"models/{lab.id}"
    logo = lab.data.get("logo")
    expected = None
    if logo is not None:
        name = logo.get("file") if isinstance(logo, dict) else None
        suffix = Path(str(name)).suffix
        if name != f"logo{suffix}" or suffix not in LOGO_TYPES:
            yield f"{where}/{LAB_FILE}: logo.file must be one of " + ", ".join(f"logo{s}" for s in LOGO_TYPES)
        elif name not in lab.files:
            yield f"{where}/{LAB_FILE}: logo.file {name!r} does not exist"
        else:
            expected = name
            data = lab.files[name]
            problems = svg_errors(data) if suffix == ".svg" else raster_errors(data, suffix)
            for problem in dict.fromkeys(problems):
                yield f"{where}/{name}: {problem}"
    for name in lab.files:
        if name != expected:
            yield f"{where}/{name}: unexpected file; a lab directory holds {LAB_FILE} and its logo"


def lab_errors(labs: list[Lab], cards: list[Card], unregistered: set[str]) -> Iterator[str]:
    """Every lab directory with cards has a lab.toml, and every lab.toml has cards.

    `unregistered` names lab directories known to lack a lab.toml (for example a
    publisher namespace that is not a lab); an entry that no longer applies is reported.
    """
    registered = {lab.id for lab in labs}
    used = {card.path.split("/", 1)[0] for card in cards}
    for lab in sorted(used - registered - unregistered):
        yield f"models/{lab}/: lab directory has no {LAB_FILE}"
    for lab in sorted(registered - used):
        yield f"models/{lab}/{LAB_FILE}: lab has no cards"
    for lab in sorted(unregistered & registered):
        yield f"stale unregistered lab {lab!r}: it now has a {LAB_FILE}"
    for lab in sorted(unregistered - used):
        yield f"stale unregistered lab {lab!r}: it has no cards"
    for lab in labs:
        yield from logo_errors(lab)


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
            yield f"{where}: section {section!r} is not a models.json section"
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


def assemble(
    cards: list[Card], sections: list[str], schema_id: str | None = None,
    required_sections: list[str] | None = None,
) -> dict[str, Any]:
    """Build models.json: its `$schema` first, then sections in schema order, cards sorted by id."""
    facts: dict[str, Any] = {"$schema": schema_id} if schema_id else {}
    required = sections if required_sections is None else required_sections
    used = {card.data.get("section") for card in cards}
    facts.update({section: {} for section in sections if section in required or section in used})
    for card in sorted(cards, key=lambda c: str(c.data.get("id", ""))):
        section = card.data.get("section")
        if section not in facts:
            continue
        if card.file == OPERATION_FILE:
            facts[section] = project(card)
        else:
            facts[section][card.data["id"]] = project(card)
    return facts


def logo_output(lab: Lab) -> str | None:
    """The logo's path in catalogue/, relative to labs.json."""
    logo = lab.data.get("logo")
    if not isinstance(logo, dict):
        return None
    suffix = Path(str(logo.get("file"))).suffix
    return f"logos/{lab.id}{suffix}" if suffix in LOGO_TYPES else None


def project_lab(lab: Lab) -> dict[str, Any]:
    data = {"id": lab.id, **lab.data}
    logo = data.get("logo")
    if isinstance(logo, dict):
        rest = {k: v for k, v in logo.items() if k != "file"}
        suffix = Path(str(logo.get("file"))).suffix
        data["logo"] = {"path": logo_output(lab), "media_type": LOGO_TYPES.get(suffix), **rest}
    return data


def assemble_labs(labs: list[Lab]) -> dict[str, Any]:
    """Build labs.json: labs sorted by id."""
    return {lab.id: project_lab(lab) for lab in sorted(labs, key=lambda lab: lab.id)}


def dumps(value: dict[str, Any]) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"
