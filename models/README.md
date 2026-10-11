# Models

The authored source of the catalogue: one directory per model card, grouped by lab.
[`catalogue/facts.json`](../catalogue/facts.json) is generated from these files by
[`scripts/build.py`](../scripts/build.py). Edit a card here, never `facts.json`.

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

## A card

A card is TOML holding the card's contract fields, in the shape
[`catalogue/README.md`](../catalogue/README.md) describes, plus two authoring keys that
are not written to `facts.json`:

| key         | meaning                                                                           |
| ----------- | --------------------------------------------------------------------------------- |
| `section`   | The `facts.json` section the card belongs to, e.g. `"image.models"`               |
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
uv run scripts/build.py   # regenerate catalogue/facts.json
uv run scripts/check.py   # cards, generated file, schema, invariants
```

Commit the card and the regenerated `facts.json` together. `facts.json` lists cards
sorted by ID within each section; that order carries no meaning.
