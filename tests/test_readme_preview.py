import json
from xml.etree import ElementTree as ET

from readme_preview import render_previews

NS = "{http://www.w3.org/2000/svg}"


def test_release_index_keeps_cutoff_ties_and_counts_remaining_cards():
    def card(label, day, basis="model"):
        return {"label": label, "release": {"date": day, "basis": basis}}

    catalogue = {
        "text.catalog": {
            "latest": card("Latest", "2026-11-18"),
            "second": card("Second", "2026-11-17"),
            "third": card("Third", "2026-11-16"),
            "unknown": card("Unknown release", None),
        },
        "image.models": {
            "cutoff-a": card("A & B", "2026-11-15"),
            "cutoff-b": card("Same day B", "2026-11-15"),
            "cutoff-c": card("Same day C", "2026-11-15"),
            "endpoint": card("New provider endpoint", "2026-11-20", "provider_endpoint"),
        },
        "three_d.rig_check.operation": card("Rig check", "2026-11-20"),
    }

    previews = render_previews(json.dumps(catalogue).encode(), b"{}", {})
    for asset in previews.values():
        root = ET.fromstring(asset)
        rows = list(root.iter(NS + "g"))
        assert [row.get("data-model") for row in rows] == [
            "latest", "second", "third", "cutoff-a", "cutoff-b", "cutoff-c",
        ]
        assert rows[-1].get("data-released") == "2026-11-15"
        labels = [node.text for node in root.iter(NS + "text")]
        assert {"A & B", "2 more models", "Image 1", "Text 1"}.issubset(labels)
        assert labels.count("15 Nov 2026") == 1
