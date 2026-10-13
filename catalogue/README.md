# Catalogue

This directory is the contract: language-agnostic JSON that consumers read. Its facts are
authored as one card per model in [`models/`](../models/); everything else outside it
(scripts, tests, skills) is tooling for maintaining it.

| file                         | role                                                                                                                 |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `models.json`                | Generated from `models/`. Model identities, release provenance, provider bindings, capabilities, limits, list prices |
| `labs.json`                  | Generated from `models/<lab>/lab.toml`. The labs that make catalogued models                                         |
| `schemas/models.schema.json` | JSON Schema 2020-12 for `models.json`                                                                                |
| `logos/`                     | Generated from `models/<lab>/logo.*`. Each lab's official logo                                                       |
| `schemas/labs.schema.json`   | JSON Schema 2020-12 for `labs.json`                                                                                  |
| `PROVENANCE.md`              | Source notes and qualifications that don't fit in JSON                                                               |

Released snapshots of this directory, versioned `v<schema>.<YYYYMMDD>.<n>`, are published at
[github.com/gridaco/models/releases](https://github.com/gridaco/models/releases); see the
[repository README](../README.md#get-the-catalogue).

## Origin

Imported byte-identical from [gridaco/grida](https://github.com/gridaco/grida) (`data/ai/`,
commit `f053893047af`), with the shape unchanged. It was then split into per-model cards in
`models/`, from which the file is generated with the same data; only the order of cards and
keys changed. It was named `facts.json` until release `v1.20261011.0`, and published under
that name in that release; its schema `$id` keeps the original `ai-model-facts-v1` until the
next breaking change.

## Shape

`models.json` starts with `$schema`, the `$id` of its schema, so a copy of the file says what
it is. The rest is an object of sections. Each section key is a dotted family path, and each
section is a table of cards keyed by card ID:

| section                           | cards                                        |
| --------------------------------- | -------------------------------------------- |
| `text.catalog`                    | Language models                              |
| `image.models`                    | Image generation, with per-provider bindings |
| `video.models`                    | Video generation, with per-provider bindings |
| `audio.music.models`              | Music generation                             |
| `audio.sound_effects.models`      | Sound effects                                |
| `audio.text_to_speech.models`     | Speech                                       |
| `three_d.models`                  | 3D generation endpoints                      |
| `three_d.model_generation.models` | 3D model generation                          |
| `three_d.rigging.models`          | Rigging                                      |
| `three_d.rig_check.operation`     | One operation, not a table                   |
| `image_tools.models`              | Background removal and upscaling             |
| `embedding.models`                | Embeddings                                   |

Cards are listed in ID order within each section; the order carries no meaning. Every
card has `id` (equal to its table key), `label`, and `release`
(`{ date, basis, source_url }`). The rest depends on the family. Image and video cards are
canonical (`vendor/model`) and hold a `providers` record of bindings keyed by provider;
other families have one card per provider endpoint.

## Labs

`labs.json` is an object keyed by lab ID. Each lab has `id` (equal to its key), `name` (the
display name as the lab writes it), and `url` (its first-party homepage). A card's `vendor`
is a lab ID. Its `$id` is `https://grida.co/schemas/ai-model-labs-v1.json`.

A lab may have a `logo`: `path` (the file in `logos/`, relative to `labs.json`),
`media_type`, `kind` (`symbol`, `wordmark`, or `lockup`), `source_url`, optional
`guidelines_url`, and `retrieved`. Logo files are the labs' official artwork, copied
unchanged. They are trademarks of their owners, are not covered by this repository's
license, and are used under each owner's guidelines.

## Rules

- **Additive.** Add fields; never rename, remove, or repurpose one in schema version 1. A
  breaking change needs a new schema version and a new `$id`.
- **IDs are exact.** Model and provider IDs keep the spelling their owner uses.
- **Fields are `lower_snake_case`.**
- **Facts only.** No listing, lifecycle, ordering, or default choices (`listed`, `status`,
  `legacy`, `deprecated`, `default`); those belong to each consumer.
- **Sourced.** Every value traces to a first-party page; qualifications go in `PROVENANCE.md`.

The schema's `$id` is `https://grida.co/schemas/ai-model-facts-v1.json`. It is kept
unchanged from its origin; changing it is a breaking change.

## Field notes

- `avg_cost_usd` (bindings and some cards) and `cost_usd` (image tools) are coarse
  per-request estimates, not published prices. Published prices are under `pricing`/`cost`.

## Known exceptions

Carried unchanged from the origin and listed in `KNOWN_EXCEPTIONS` in
[`scripts/check.py`](../scripts/check.py), which reports them as stale once fixed:

- `embedding.models` / `google/gemini-embedding-2` has `deprecated: false`, a policy field.
  Its `dimensions: 1536` is also a storage choice rather than a model limit
  (the model emits 3072 dimensions and can be truncated).

## Validate

From the repository root:

```sh
uv run scripts/check.py   # schema + invariants
uv run pytest             # the checker rejects what it should
```

## Provider endpoints

A provider binding may list `endpoints`: exact call IDs with `input` (`text`,
`image`, `video`, `audio`, or `task`) and a first-party `source_url`. These identify
input variants, not a routing preference. The existing binding `id` remains its
primary call ID; `references` and pricing retain their existing meaning.
Endpoint IDs are unique within a binding. The list records documented variants,
not an assertion that a consumer supports every variant.

`vendor`, including on text cards, identifies the model's lab in `labs.json`.
It is independent of a model ID's namespace and its serving provider.

## Published calculators and serving facts

Optional additions record the facts at the scope their source describes. A card's
`output_token_calculator` and `vision_tokenization` describe the model. A binding's
`capabilities`, `limits`, and `token_pricing` describe what its provider serves.
Endpoint `parameters` and `image_constraints` describe one exact input variant.
Do not flatten a provider's limits or price bands into intrinsic model facts.
Missing fields mean unrecorded facts, never unsupported features or zero prices.

- **Output calculators.** `output_token_calculator` carries a first-party
  `source_url`, an optional `source_js_url` for the published calculator asset,
  `area_offset`, `area_divisor`, `short_axis_rounding`, `token_rounding`, and
  `quality_axes` (quality name to its positive integer axis). This shape describes
  the published formula `ceil(K × round(K × min(width, height) / max(width, height))
× (area_offset + width × height) / area_divisor)`. `nearest_ties_even` rounds the
  short axis; `ceil` rounds output tokens. `examples` records sourced width,
  height, quality, and `output_tokens` and/or `usd`. An optional `usd_precision`
  records the number of decimal places in a published rounded price. A rounded
  price is evidence of that price, not a basis for inventing an exact token count.
  The checker reproduces any recorded token count from the formula and rejects
  duplicate size/quality examples.
- **Vision tokenization.** `vision_tokenization` is a sourced set of the rules the
  vendor actually publishes: `patch_size_px`, `token_multiplier`,
  `detail_patch_budgets`, `detail_token_budgets`, `detail_maximum_edges`,
  `maximum_patch_count`, `maximum_tokens_per_image`, `tokens_per_image`, and
  `token_rounding`, when applicable. Patch counts, token budgets, and edge limits
  retain distinct meanings. `token_counts_approximate: true` preserves a source's
  qualification that its token examples or budgets are approximate. Omit rules
  that have not been published.
- **Capabilities and limits.** A sourced `capabilities` object may record boolean
  `image_input`, `tools`, `reasoning`, `structured_output`, and `streaming`. A
  provider's sourced `limits` may record positive `context_tokens` and
  `max_output_tokens`. Neither object chooses a consumer's supported features.
- **Token pricing.** `token_pricing` records `unit: "usd_per_token"`, a
  `source_url`, and exact decimal strings for `input`, `output`,
  `input_cache_read`, and `input_cache_write` where published. Optional `tiers`
  carry `meter`, an inclusive `minimum_input_tokens`, an exclusive
  `maximum_input_tokens`, and `usd_per_token`. An omitted or null maximum means
  no published upper bound. Bands may differ by meter and cannot overlap for the
  same meter. These are provider list prices, not converted application prices.
- **Endpoint parameters.** `parameters` maps exact provider field names, including
  dotted paths such as `image_size.width`, to their published `type`, `enum`,
  numeric `minimum`/`maximum`/`multiple_of`, array `min_items`/`max_items`, or text
  `min_length`/`max_length`. Endpoint `source_url` covers these facts; a parameter
  may override `source_url` when one bound is published on a different page.
  This is partial descriptive metadata, not a complete request JSON Schema. For
  example, string presets and custom-size object fields may be recorded
  separately. No defaults or consumer choices are included.
- **Image envelopes.** `image_constraints` keeps `step`, `min_edge`, `max_edge`,
  `min_pixels`, `max_pixels`, and `aspect_ratio: { min, max }` at endpoint scope,
  under that endpoint's source. Each field is optional; do not infer the rest.

Single-provider cards and `three_d.rig_check.operation` may also carry
`endpoints`, with the same shape as a binding's endpoint variants. New sourced
objects have strict field vocabularies; pre-existing card and price shapes remain
unchanged in schema version 1.
