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

| section                                    | cards                                        |
| ------------------------------------------ | -------------------------------------------- |
| `decision.models` (optional)               | Bounded classification and scoring offerings |
| `text.catalog`                             | Language models                              |
| `image.models`                             | Image generation, with per-provider bindings |
| `video.models`                             | Video generation, with per-provider bindings |
| `audio.music.models`                       | Music generation                             |
| `audio.sound_effects.models`               | Sound effects                                |
| `audio.text_to_speech.models`              | Speech                                       |
| `audio.transcription.models` (optional)    | Batch and streaming speech recognition       |
| `audio.realtime.models` (optional)         | Conversational speech-to-speech agents       |
| `audio.voice_design.models` (optional)     | Voice creation from text descriptions        |
| `audio.voice_conversion.models` (optional) | Voice conversion from recorded speech        |
| `three_d.models`                           | 3D generation endpoints                      |
| `three_d.model_generation.models`          | 3D model generation                          |
| `three_d.rigging.models`                   | Rigging                                      |
| `three_d.rig_check.operation`              | One operation, not a table                   |
| `image_tools.models`                       | Background removal and upscaling             |
| `embedding.models`                         | Embeddings                                   |

Cards are listed in ID order within each section; the order carries no meaning. Every
card has `id` (equal to its table key), `label`, and `release`
(`{ date, basis, source_url }`). The rest depends on the family. Image and video cards are
canonical (`vendor/model`) and hold a `providers` record of bindings keyed by provider.
Other families retain their existing IDs and direct-provider facts, and may also add
`providers`; the same additions are supported on embeddings and the rig-check operation.

## Compatibility boundary

The default vocabulary for new common discovery metadata follows
[Vercel AI Gateway](https://vercel.com/docs/ai-gateway/sdks-and-apis/rest-api):
optional `type` (`language`, `embedding`, `reranking`, `image`, `video`, `speech`,
`transcription`, `realtime`, `evaluation`) and `modalities: { input, output }` with nonempty,
distinct `text`, `image`, `pdf`, `audio` or `video` values. Each requires a
first-party `source_url` at the same card or binding scope. These fields describe
discovery capabilities, not the request or response serialization. Model-level
facts need native evidence; a provider's narrower or different offering stays on
its binding. Omission means unrecorded, not unsupported.

Vercel is a compatibility target, not a formal interchange standard. Its
[AI SDK speech](https://ai-sdk.dev/docs/ai-sdk-core/speech) and
[transcription](https://ai-sdk.dev/docs/ai-sdk-core/transcription) interfaces are
the reference for common execution concepts. This catalogue does not implement
them or inherit a capability merely because an SDK exposes it. Native music and
sound generation fit the baseline's `speech` discovery class; their existing
sections retain the more specific organization. Voice design and conversion
remain distinct sections without inventing new baseline `type` values.

Provider-specific parameters, output formats and events retain the provider's
contract and belong on its binding or endpoint. Link authoritative
[JSON Schema](https://json-schema.org/draft/2020-12),
[OpenAPI](https://spec.openapis.org/oas/latest.html) or
[AsyncAPI](https://www.asyncapi.com/docs/reference/specification/latest)
documents; preserve their own dialect and keywords, such as `maxLength`, instead
of recreating a parameter language. The four optional audio sections are
organizational groupings, not four new request or result specifications.

Our own layer records provenance, canonical identities, provider-ID relationships
and documented extensions. An operation outside the baseline, such as Tripo
rigging, still mirrors its native request and result schemas. A provider-specific
feature does not become a new shared field just because the baseline omits it.
Released v1 fields and existing price shapes remain compatible. New structured
extensions need their own documented gap and review; when the current shape
cannot faithfully express a fact, retain its source and qualification rather
than inventing an API parameter. A catalog-layout migration requires a separately
versioned change.

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
- **Sourced facts.** Model facts and published tariffs trace to first-party pages;
  qualifications go in `PROVENANCE.md`. The separately labelled
  [illustrative costs](#illustrative-costs) may be manually curated estimates with
  their own provenance and optional supporting links.

The schema's `$id` is `https://grida.co/schemas/ai-model-facts-v1.json`. It is kept
unchanged from its origin; changing it is a breaking change.

## Field notes

- `avg_cost_usd` (bindings and some cards) and `cost_usd` (image tools) are coarse
  per-request estimates, not published prices. Published prices are under `pricing`/`cost`.
  These legacy fields retain their meaning; they do not establish a measured
  average or inherit a scenario from `illustrative_costs`.

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
New bindings should use the linked native schema instead of extending that
legacy shorthand. A schema link may identify a request/response schema inside an
OpenAPI document by JSON Pointer; it retains the external document's dialect.
For WebSocket protocols, the official AsyncAPI reference is authoritative even
when no standalone schema document is published. Do not label an HTML reference
page as a machine-readable request or result schema.

## Illustrative costs

Optional `illustrative_costs` is a nonempty array on a **provider binding or
endpoint**. A legacy card or operation with an explicit direct `provider` may
also use it for that provider. A canonical multi-provider card cannot carry a
global illustration: a native example does not establish another provider's
cost. Binding and endpoint arrays are independent; no inheritance, merging or
override behavior is implied.

Each item describes an **illustrative cost for one stated scenario and charge
scope**, not a billing rate, attainable starting price, statistical average,
reservation ceiling or guaranteed request total:

- `amount`: an exact nonnegative decimal **string**, without exponent notation.
- `currency`: the original `USD` or `CNY` currency; no conversion is implied.
- Optional `unit` and `per_quantity` appear together or are both omitted. `unit`
  is a lowercase token (`image`, `character`, `second`, for example), at most 64
  characters. `per_quantity` is a positive exact decimal string, at most 64
  characters, using the same spelling as `amount`; `1.0` and `0.50` retain their
  precision, while zero, signs, exponents, leading zeros and whitespace are
  invalid. The amount covers that selected quantity and configuration; it is
  not an executable unit rate. For `image`, count generated output images,
  never input/reference images. Other units retain the scope stated in the
  scenario, such as 500 billed input characters.
- Optional `label`: nonblank plain text, at most 256 characters, for a short
  configuration label such as `1024 × 1024 · Medium · 1 reference`. It does not
  replace the complete scenario or encode parameters or price rules.
- `scenario`: nonblank plain text stating configuration and quantities. Retain
  the provider's native parameter names where useful; no new parameter language
  or formula is required for a maintainer judgement.
- `coverage`: nonblank plain text stating included charges, exclusions and any
  unknown coverage. An output-only amount must say that input or ancillary fees
  are separate; an unknown charge is not zero.
- `provenance`: an object with `maintenance: "manual"`, nonblank `description`
  explaining the origin/derivation/assumptions, and a real calendar `reviewed_on`
  date (`YYYY-MM-DD`). Optional `source_urls` is a nonempty, distinct list of
  absolute HTTPS references without credentials. Omit the list when no useful,
  maintainable link exists; a URL is not required for a manual illustration.

For example, a manually chosen scenario may be authored without a source URL:

```json
{
  "illustrative_costs": [
    {
      "amount": "0.05",
      "currency": "USD",
      "unit": "image",
      "per_quantity": "1",
      "label": "Medium · 1 output image",
      "scenario": "One image at the author's chosen medium-quality setting.",
      "coverage": "Illustrative output budget only; input and ancillary fees are unknown.",
      "provenance": {
        "maintenance": "manual",
        "description": "Maintainer judgement for comparison, not a provider quote or a measured average.",
        "reviewed_on": "2026-11-13"
      }
    }
  ]
}
```

This documentation example does not advertise a price for any model. An authored
item may instead explain a provider-published example, a third-party estimate,
or a calculation from published rates. `maintenance` says how it is maintained,
not how certain it is. Preserve genuine supporting references when available;
do not invent a homepage/anchor or attribute a judgement to a provider. This
narrow estimate exception does not relax first-party evidence for actual model
facts, regular tariffs, limits or capabilities. A source URL alone does not turn
an estimate into a verified price.

Use existing `pricing`, `token_pricing` or `published_pricing` when a clear
per-generation, image, second, character or other unit rate already communicates
the cost. An illustration adds a scenario; it does not duplicate or replace the
authoritative price schedule. Omit it where neither a useful qualified example
nor a reasonable explicit maintainer judgement is available. Omission does not
mean free inference, provider absence, or unsupported capabilities.

Authors review an illustration and its provenance together whenever a relevant
rate, model/endpoint, formula, scenario or included charge changes. Revise it or
remove it until reviewed; do not automatically advance `reviewed_on`, reuse a
stale value, or regenerate a legacy average as a new illustration. The checker
validates structure, scope, dates and supporting URLs; it cannot verify prose,
price arithmetic or a maintainer's judgement and does not fetch sources. Review
remains manual, including for changed assumptions not represented as a formula.

Consumers can present these as **estimated media costs** and show the scenario and charge
coverage alongside the amount, with provenance available in details. Keep exact
rates accessible. Formatting/localization and whether to show an illustration
belong to consumers; receiving this field does not change execution or billing.
An explicit `image` / `1` denominator can display as `$0.05/image`. An amount
of `$0.20` covering `image` / `2` stays `$0.20 / 2 images`; do not automatically
divide or normalize it. An explicit `character` / `500` amount is for those 500
characters, not one character. Without the pair, display the amount without an
inferred denominator. Never infer output count from model kind or English prose,
or inherit the pair from another example or binding. Use `label` for a compact
configuration list, falling back to `scenario` when it is absent; both remain
display text, with full coverage and provenance available.
Unknown additive metadata must not invalidate the rest of a catalogue. Existing
fields, schema version and `$id` remain unchanged; this contract requires no paid
sampling or runtime source lookup.

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
  duplicate size/quality examples. Optional `quality_multipliers` supplies exact positive
  decimal strings for every quality axis, together with `result_rounding:
"nearest_ties_up"`. Apply the multiplier after the base output-token ceiling, then
  round to the nearest integer with half ties upward. This preserves the GPT Image
  2.6 calculator's second step; older calculators omit both fields and keep their
  original formula. The multiplier map must match the quality-axis keys exactly.
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

## Decision offerings

The optional `decision.models` section describes bounded decision offerings separately
from text generation. Existing version 1 snapshots remain valid without the section;
the generator emits it only when a card is authored there. A decision card uses the
common identity, vendor, release and provider fields, and requires `underlying_model`
(the canonical identity of the underlying model) and nonempty provider bindings.
This relationship does not inherit that model's chat capabilities, limits or prices.
Decision cards reject chat-only top-level fields such as `context_window`, `output_limit`
and `cost`; use sourced provider limits and prices for this offering's exact interface.

Optional `decision_contract` on a card, binding or endpoint records sourced descriptive
facts: `question_types` (exact wire vocabulary, such as `predicate` or `noul`),
`input_forms` (`string`, `user_messages`, or `state`), `question_container`
(`array` or `named_object`), `image_input_forms` (`data_url`, `http_url`, or `file_id`),
`image_details`, `maximum_questions`, `maximum_images`, choice and score bounds
(`minimum_choices`, `maximum_choices`, `minimum_score_levels`, `maximum_score_levels`),
`typed_choice_values`, and `partial_refusals`. Every object requires a first-party
`source_url`; omitted fields are unrecorded, not unsupported. Minimum and maximum
pairs cannot be inverted. Typed choice values distinguish a boolean from its string
spelling; a false value records that the provider rejects such a collision.

The endpoint's `interface` and source link remain authoritative for the full wire
contract and answer semantics. Provider vocabularies, image envelopes and pricing
remain independent even when the underlying model is identical. No ZDR eligibility,
probability calibration guarantee or output-generation pricing is inferred from
this family membership.
