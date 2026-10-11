# Models

The authored source of the catalogue: one directory per model card, grouped by lab.
[`catalogue/models.json`](../catalogue/models.json) is generated from these files by
[`scripts/build.py`](../scripts/build.py). Edit a card here, never `models.json`.

## Layout

```
models/<lab>/<model>/card.toml
```

| part      | value                                                                                                               |
| --------- | ------------------------------------------------------------------------------------------------------------------- |
| `<lab>`   | The card's `vendor`. A card without `vendor` uses the first segment of its `id`                                     |
| `<model>` | The `id` without its first segment (`openai/gpt-5.5` → `gpt-5.5`), or the whole `id` when it has none (`eleven_v3`) |

Examples:

| id                                      | vendor              | directory                       |
| --------------------------------------- | ------------------- | ------------------------------- |
| `openai/gpt-image-2.5-flare`            | `openai`            | `openai/gpt-image-2.5-flare/`   |
| `bfl/flux-2-pro`                        | `black-forest-labs` | `black-forest-labs/flux-2-pro/` |
| `eleven_v3`                             | `elevenlabs`        | `elevenlabs/eleven_v3/`         |
| `fal-ai/trellis-2`                      | `microsoft`         | `microsoft/trellis-2/`          |
| `anthropic/claude-opus-5` (no `vendor`) | —                   | `anthropic/claude-opus-5/`      |

The directory is derived, never chosen: `uv run scripts/check.py` reports a card that is
not where its lab and ID put it. A directory holds one card and may later hold the card's
assets; it never contains another card.

A card without `vendor` sits under its ID namespace, which for a provider-hosted model is
the publisher on that provider, not necessarily the lab that made the model (for example
`nightmareai/real-esrgan`). Adding a sourced `vendor` moves the card to its lab.

## A lab

Every lab directory holds a `lab.toml`, generated into
[`catalogue/labs.json`](../catalogue/labs.json):

```toml
name = "Black Forest Labs"   # display name, as the lab writes it
url = "https://bfl.ai/"      # the lab's first-party homepage

# The guidelines allow the symbol alone in small-scale use; the logotype is primary.
[logo]
file = "logo.svg"            # logo.svg, logo.png, or logo.webp, beside lab.toml
kind = "symbol"              # symbol, wordmark, or lockup
source_url = "https://…"     # the asset's URL, or the first-party page it came from
guidelines_url = "https://…" # the lab's brand guidelines, when it publishes them
retrieved = "2026-10-12"
```

A logo is the lab's official artwork from a first-party source: its brand kit, press kit, or
its own website. Never an aggregator or a redrawing. Prefer SVG, then PNG, then WebP; prefer
the lab's symbol to its wordmark unless the lab's guidelines say otherwise. Keep the artwork unchanged, and say in a comment above
`[logo]` how it was obtained when it was not a plain download (for example, extracted from
the site header). `check.py` rejects SVGs with scripts, event attributes, `foreignObject`, or
external references. Logos are trademarks of their owners and are not covered by this
repository's license.

The directory name is the lab ID; the file has no `id`. A new lab needs a `lab.toml` in the
same change as its first card, and a `lab.toml` with no cards is reported. Publisher
namespaces that are not labs (`851-labs`, `nightmareai`) have no `lab.toml`; they are listed
in `KNOWN_UNREGISTERED_LABS` in [`scripts/check.py`](../scripts/check.py) until their cards
get a sourced `vendor`.

## A card

A card is TOML holding the card's contract fields, in the shape
[`catalogue/README.md`](../catalogue/README.md) describes, plus two authoring keys that
are not written to `models.json`:

| key         | meaning                                                                           |
| ----------- | --------------------------------------------------------------------------------- |
| `section`   | The `models.json` section the card belongs to, e.g. `"image.models"`              |
| `null_keys` | Dotted paths written as JSON `null`, which TOML cannot express, e.g. `["styles"]` |

```toml
id = "openai/gpt-5.5"
section = "text.catalog"

label = "GPT-5.5"
tool_call = true
context_window = 1_050_000
output_limit = 128_000

[release]
date = "2026-04-23"
basis = "model"
source_url = "https://openai.com/index/introducing-gpt-5-5/"

[cost]
input = 5
output = 30
cache_read = 0.5
```

A section that is one object rather than a table of cards
(`three_d.rig_check.operation`) is authored as
`models/<provider>/<binding_id>/operation.toml`.

## After editing

```sh
uv run scripts/build.py   # regenerate catalogue/models.json, labs.json, and logos/
uv run scripts/check.py   # cards, generated file, schema, invariants
```

Commit the source and the regenerated files together. `models.json` lists cards
sorted by ID within each section; that order carries no meaning.
