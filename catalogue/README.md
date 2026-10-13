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
canonical (`vendor/model`) and hold a `providers` record of bindings keyed by provider.
Other families retain their existing IDs and direct-provider facts, and may also add
`providers`; the same additions are supported on embeddings and the rig-check operation.

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
- **Facts only.** No product listing, lifecycle or routing defaults (`listed`, `status`,
  `legacy`, `deprecated`, `default`); those belong to each consumer.
  `reference_provider` identifies the native API for presentation, not a routing default.
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
`image`, `multi_image`, `video`, `audio`, `task`, or `asset`) and a first-party `source_url`. These identify
input variants, not a routing preference. The existing binding `id` retains its
provider-defined model or primary call identity; `references` and pricing retain
their existing meaning.
Endpoint IDs are unique within a binding. The list records documented variants,
not an assertion that a consumer supports every variant.

`vendor`, including on text cards, identifies the model's lab in `labs.json`.
It is independent of a model ID's namespace and its serving provider.

### Native reference and coverage

Every family, including embedding and the rig-check operation, may add a
`providers` record without changing its existing ID or direct-provider fields.
Each binding has exact `provider` and `id` values, an optional first-party
`source_url`, and independently sourced serving facts. A verified binding can
omit an unknown regular price; omission never means free inference. Optional
`qualifications` records nonempty `{ source_url, notes }` entries for unresolved
pricing or specification facts, without inventing a replacement value.

Optional `reference_provider` names a real native API binding, or the existing
direct `provider` when that card describes the native API already. Consumers may
present it first as the lab's reference. It does not prescribe which provider to
call, and JSON object order carries no meaning. Official weights do not establish
a native hosted API. This field records a sourced reference, not a provider registry.

`provider_coverage` maps provider names to `{ disposition, source_url, reason? }`:

- `listed` requires a binding or matching direct provider.
- `not_listed` records verified absence from that provider's published catalogue.
- `excluded` records an incompatible or unverifiable specification, identity or
  pricing contract that makes a reliable listing inappropriate, or an explicit
  modality scope such as fal media-only coverage. A scope exclusion is not a claim
  that the provider has no such model.

The last two require a public, source-backed `reason` and cannot coexist with a
binding for that provider. Do not use an exclusion for routing preference or
unfinished research. Missing coverage remains unrecorded, not proof of absence.
Maintain coverage for native APIs, OpenRouter, Vercel and fal media where verified.
Grida bindings describe only models actually offered by its public service;
other catalogue models remain useful independently.

### Published service prices and contracts

A binding or endpoint may record `published_pricing` with first-party
`source_url`, `currency: "USD"`, and nonempty `components`. This provider-neutral
shape expresses advertised regular prices, including Grida's public price, using:

- `meter`, `unit`, and exact decimal-string `usd_per_unit`; optional
  `per_quantity` is a positive decimal denominator (one when omitted).
- Optional `id` identifies a component uniquely within that price.
- Optional `when` is a JSON Schema predicate over public request parameters.
- Optional `quantity_range: { meter, min, max }` is a half-open range with decimal
  bounds; an omitted or null `max` leaves it unbounded. It selects a component for the range,
  not marginal volume pricing.
- Optional `quantity_rounding: { mode, increment }` preserves quantity rounding:
  `none` permits an omitted or null increment; `ceil` requires a positive decimal increment.

For TOML arrays, omit the optional null upper bound or increment; `null_keys`
addresses object paths, not array indexes. Omission has the same defined semantics
as JSON null here and never means a zero price.

Rates, ranges and rounding are sourced service facts. Internal margins, funding
fees, credit conversions, supplier routing and account-specific prices are excluded.
Do not derive a public service price from another provider's price without the
service's own published evidence. Unknown or promotional rates stay unrecorded.

Endpoints may name a public `operation` and `interface`, and link authoritative
`request_schema_url` and `result_schema_url`. Links are absolute HTTPS without
credentials; schemas are not copied or fetched by the catalogue checker.
Existing `parameters` remains partial descriptive metadata, not a substitute for
the linked contract. A provider-specific capability difference stays on its binding
or endpoint rather than overwriting the model's intrinsic facts.

## Model distribution

A card may record `distribution`, independently of its hosted provider bindings.
It requires a first-party `source_url` and at least `code` or `weights`:

- `code.repository_url` identifies the official source-code repository.
- `weights` is a nonempty array of official weight repositories or artifact pages.
  Each item has `url`; an optional `id` preserves the exact published weight variant.
  Distinct variants may share a repository URL, but their IDs must be distinct.
- Code and each weight item may independently record `license: { name, url }`.
  Use the publisher's license name and its license text or model-card URL, including
  custom licenses. An unverified license stays omitted; code and weights need not
  use the same license.
- A weight item's optional `access` is `public` or `gated`, as documented by its
  publisher. Omission means unrecorded access conditions. Public access does not
  establish unrestricted use or an open-source classification.

All URLs must be absolute HTTPS URLs without embedded credentials. Unknown
distribution facts stay omitted. These records describe published artifacts;
they do not establish a hosted API, an inference price, or permissions beyond the
linked licenses. `distribution` belongs to model cards, not provider bindings,
endpoint variants, or the rig-check operation. Existing cards remain valid
without it. See [TRELLIS.2](../models/microsoft/trellis-2/card.toml) for sourced
code and weight records.

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
  `input_cache_read`, `input_cache_write`, and `input_cache_write_1h` where published.
  Optional `scope` records a source-backed service tier or cache-duration qualification;
  a storage-per-hour rate does not belong in a per-token meter. Optional `tiers`
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
