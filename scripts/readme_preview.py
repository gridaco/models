"""Render the desktop and compact README release index from catalogue data."""

from __future__ import annotations

import base64
import io
import json
from calendar import month_abbr
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from xml.etree import ElementTree as ET

from fontTools import subset
from fontTools.ttLib import TTFont
from PIL import Image
from resvg_py import svg_to_bytes

ASSETS = Path(__file__).with_name("readme_assets")
SVG_NS = "http://www.w3.org/2000/svg"
FAMILIES = {"text": "Text", "image": "Image", "video": "Video", "audio": "Audio", "three_d": "3D"}
SHADES = ("#262626", "#454545", "#606060", "#777", "#909090", "#a3a3a3")
RELEASE_LIMIT = 5


@dataclass(frozen=True)
class Model:
    id: str
    label: str
    lab: str | None
    family: str
    released: date | None


def model_cards(snapshot: dict) -> list[Model]:
    models = []
    for section, table in snapshot.items():
        if not isinstance(table, dict) or section.endswith(".operation"):
            continue
        family = FAMILIES.get(section.partition(".")[0], "Other")
        for model_id, card in table.items():
            release = card["release"]
            released = (
                date.fromisoformat(release["date"])
                if release["basis"] == "model" and release["date"]
                else None
            )
            models.append(Model(model_id, card["label"], card.get("vendor"), family, released))
    return models


def recent_releases(models: list[Model]) -> list[Model]:
    ordered = sorted(
        (model for model in models if model.released),
        key=lambda model: (-model.released.toordinal(), model.id),
    )
    if len(ordered) <= RELEASE_LIMIT:
        return ordered
    cutoff = ordered[RELEASE_LIMIT - 1].released
    return [model for model in ordered if model.released >= cutoff]


def element(parent: ET.Element, tag: str, **attrs: object) -> ET.Element:
    attributes = {key.replace("_", "-"): str(value) for key, value in attrs.items()}
    return ET.SubElement(parent, tag, attributes)


def text(
    parent: ET.Element, x: float, y: int, value: str, size: int, weight: int = 450,
    color: str = "#161616", *, anchor: str = "start", tracking: float = 0,
    max_width: float | None = None,
) -> None:
    node = element(parent, "text", x=x, y=y, font_size=size, font_weight=weight,
                   fill=color, text_anchor=anchor, letter_spacing=tracking)
    if max_width is not None:
        node.set("textLength", str(max_width))
        node.set("lengthAdjust", "spacingAndGlyphs")
    node.text = value


def line(parent: ET.Element, x: int, y: int, end: int, color: str) -> None:
    element(parent, "path", d=f"M{x} {y}H{end}", fill="none", stroke=color)


class Inter:
    def __init__(self) -> None:
        self.font = TTFont(ASSETS / "Inter-Latin.woff", recalcTimestamp=False)
        self.units = self.font["head"].unitsPerEm
        metrics = self.font["hmtx"].metrics
        self.advances = {char: metrics[glyph][0] for char, glyph in self.font.getBestCmap().items()}

    def width(self, value: str, size: int) -> float:
        # Allow for the heavier weights and browser fallback glyphs.
        return 2 + 1.045 * size * sum(self.advances.get(ord(char), self.units) for char in value) / self.units

    def wrap(self, value: str, size: int, width: int) -> list[str]:
        lines = []
        current = ""
        for word in value.split():
            candidate = f"{current} {word}".strip()
            if current and self.width(candidate, size) > width:
                lines.append(current)
                current = word
            else:
                current = candidate
        return lines + [current]

    def embed(self, root: ET.Element) -> None:
        options = subset.Options()
        options.hinting = False
        options.name_IDs = [0, 1, 2, 4, 6, 13, 14, 16, 17]
        with TTFont(ASSETS / "Inter-Latin.woff", recalcTimestamp=False) as font:
            subsetter = subset.Subsetter(options=options)
            subsetter.populate(text="".join(node.text for node in root.iter("text")))
            subsetter.subset(font)
            buffer = io.BytesIO()
            font.save(buffer)
        font_data = base64.b64encode(buffer.getvalue()).decode("ascii")
        element(root, "style").text = (
            "@font-face{font-family:CatalogueInter;src:url(data:font/woff;base64,"
            + font_data
            + ") format('woff');font-weight:400 650}"
            "text{font-family:CatalogueInter,Inter,Arial,sans-serif}"
        )


def lab_mark(path: str, content: bytes) -> tuple[str, int, int]:
    if path.endswith(".svg"):
        content = svg_to_bytes(svg_string=content.decode("utf-8"), width=320, skip_system_fonts=True)
    with Image.open(io.BytesIO(content)) as original:
        image = original.convert("RGBA")
    if box := image.getbbox():
        image = image.crop(box)
    image.thumbnail((64, 64), Image.Resampling.LANCZOS)
    # Source metadata belongs on the catalogue asset. Embed only the display pixels.
    image.info.clear()
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", compress_level=0)
    pixels = base64.b64encode(buffer.getvalue()).decode("ascii")
    width, height = image.size
    # Use the same PNG encoder on each platform so build --check can compare bytes.
    png = svg_to_bytes(svg_string=(
        f'<svg xmlns="{SVG_NS}" width="{width}" height="{height}">'
        f'<image width="{width}" height="{height}" href="data:image/png;base64,{pixels}"/>'
        '</svg>'
    ), skip_system_fonts=True)
    uri = "data:image/png;base64," + base64.b64encode(png).decode("ascii")
    return uri, width, height


def index_rows(
    root: ET.Element, models: list[Model], labs: dict, marks: dict, compact: bool, font: Inter,
) -> int:
    pad, end = (16, 359) if compact else (34, 846)
    y = 57 if compact else 101
    model_x, lab_x = (110, 110) if compact else (206, 653)
    model_size, row_step = (18, 21) if compact else (28, 30)
    model_width = (end if compact else lab_x - 22) - model_x
    if not compact:
        line(root, pad, 64, end, "#222")
        for x, heading in [(35, "Released"), (207, "Model"), (653, "Lab")]:
            text(root, x, 90, heading, 14, 520, "#595959")

    previous = None
    for model in models:
        released = model.released
        first_on_day = released != previous
        group = element(root, "g", data_model=model.id, data_released=released.isoformat())
        line(group, pad if first_on_day else model_x, y, end, "#c8c8c8" if first_on_day else "#e4e4e4")
        if first_on_day:
            stamp = f"{released.day} {month_abbr[released.month]} {released.year}"
            text(group, pad if compact else 35, y + (26 if compact else 34),
                 stamp, 13 if compact else 17, 500, "#383838")
        baseline = y + (27 if compact else 37)
        names = font.wrap(model.label, model_size, model_width)
        for i, name in enumerate(names):
            text(group, model_x, baseline + row_step * i, name, model_size, 570,
                 tracking=-.5 if compact else -1.2,
                 max_width=model_width if font.width(name, model_size) > model_width else None)
        extra_height = row_step * (len(names) - 1)
        if model.lab in labs:
            lab_y = baseline + extra_height + 21 if compact else y + 34
            name_x = lab_x
            if model.lab in marks:
                size = 14 if compact else 21
                element(group, "use", href=f"#lab-{model.lab}", x=lab_x,
                        y=lab_y - (11.5 if compact else 17), width=size, height=size)
                name_x += 21 if compact else 32
            name, size = labs[model.lab]["name"], 13 if compact else 18
            text(group, name_x, lab_y, name, size, 480, "#515151" if compact else "#161616",
                 max_width=end - name_x if font.width(name, size) > end - name_x else None)
        y += (61 if compact else 54) + extra_height
        previous = released
    return y + 2


def catalogue_mix(root: ET.Element, y: int, counts: Counter, compact: bool, font: Inter) -> int:
    pad, end = (16, 359) if compact else (34, 846)
    line(root, pad, y, end, "#b4b4b4")
    total = counts.total()
    if not total:
        return y + 16

    unit = "model" if total == 1 else "models"
    text(root, pad, y + 30, f"{total:,} more {unit}", 18 if compact else 21, 570, tracking=-.6)
    buckets = sorted(counts.items(), key=lambda pair: (pair[0] == "Other", -pair[1], pair[0]))
    span, gap = end - pad, 3 if compact else 5
    bar_width = span - gap * (len(buckets) - 1)
    x, starts, labels = pad, [], []
    for (name, count), color in zip(buckets, SHADES, strict=False):
        width = bar_width * count / total
        element(root, "rect", x=round(x, 2), y=y + (46 if compact else 49),
                width=round(width, 2), height=4, rx=1, fill=color)
        starts.append(x)
        labels.append(f"{name} {count:,}")
        x += width + gap

    if compact:
        for i, label in enumerate(labels):
            x = round(pad + (i % 3) * span / 3, 2)
            baseline = y + 73 + (i // 3) * 24
            element(root, "rect", x=x, y=baseline - 8, width=7, height=7, rx=1, fill=SHADES[i])
            text(root, round(x + 12, 2), baseline, label, 14, 500, "#363636")
        return y + 68 + 24 * ((len(labels) + 2) // 3)

    # Keep labels separate even when a proportional segment is narrower than its label.
    right_edge = end
    for i in reversed(range(len(labels))):
        starts[i] = min(starts[i], right_edge - font.width(labels[i], 14))
        right_edge = starts[i] - 9
    for label, start in zip(labels, starts, strict=True):
        text(root, round(start, 2), y + 75, label, 14, 500, "#363636", tracking=-.18)
    return y + 96


def render_previews(models_json: bytes, labs_json: bytes, logo_files: dict[str, bytes]) -> dict[str, bytes]:
    models = model_cards(json.loads(models_json))
    labs = json.loads(labs_json)
    featured = recent_releases(models)
    visible = {model.id for model in featured}
    counts = Counter(model.family for model in models if model.id not in visible)
    marks = {}
    for lab in sorted({model.lab for model in featured if model.lab in labs}):
        if path := labs[lab].get("logo", {}).get("path"):
            marks[lab] = lab_mark(path, logo_files[path])

    font = Inter()
    outputs = {}
    for name, compact in [("release-index.svg", False), ("release-index-mobile.svg", True)]:
        width, pad = (375, 16) if compact else (880, 34)
        root = ET.Element("svg", {"xmlns": SVG_NS, "width": str(width), "role": "img", "aria-labelledby": "title desc"})
        element(root, "title", id="title").text = "Grida Models — Latest model releases"
        description = [f"{model.label} ({model.released.isoformat()})" for model in featured]
        if counts:
            description.append(f"{counts.total()} more models")
            description.extend(f"{family} {count}" for family, count in counts.most_common())
        element(root, "desc", id="desc").text = ". ".join(description) + "."
        element(root, "metadata").text = (ASSETS / "Inter-LICENSE.txt").read_text(encoding="utf-8")
        defs = element(root, "defs")
        for lab, (uri, w, h) in marks.items():
            symbol = element(defs, "symbol", id=f"lab-{lab}", viewBox=f"0 0 {w} {h}")
            element(symbol, "image", width=w, height=h, href=uri)

        background = element(root, "rect", width=width, fill="#fff")
        brand = element(root, "svg", x=pad - 2, y=13 if compact else 15,
                        width=28 if compact else 32, height=28 if compact else 32, viewBox="0 0 240 240")
        official_mark = ET.parse(ASSETS / "grida-symbol-240.svg").getroot()
        for path in official_mark:
            element(brand, "path", **path.attrib)
        baseline = 34 if compact else 40
        text(root, pad + (35 if compact else 42), baseline, "/", 17 if compact else 21, color="#777")
        text(root, pad + (50 if compact else 60), baseline, "Models", 17 if compact else 21, 540, tracking=-.4)
        text(root, width - pad, baseline, "Latest model releases", 15 if compact else 18,
             540, anchor="end", tracking=-.35)
        footer_y = index_rows(root, featured, labs, marks, compact, font)
        height = catalogue_mix(root, footer_y, counts, compact, font)
        root.attrib.update(height=str(height), viewBox=f"0 0 {width} {height}")
        background.set("height", str(height))
        font.embed(root)
        ET.indent(root)
        outputs[name] = (
            b"<!-- Generated by scripts/build.py from the model catalogue. -->\n"
            + ET.tostring(root, encoding="utf-8")
            + b"\n"
        )
    return outputs
