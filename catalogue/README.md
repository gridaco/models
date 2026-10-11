# Catalogue

This directory is the contract: language-agnostic JSON that consumers read. Everything
outside it (scripts, tests, skills) is tooling for maintaining it.

| file                        | role                                                                                     |
| --------------------------- | ---------------------------------------------------------------------------------------- |
| `facts.json`                | Model identities, release provenance, provider bindings, capabilities, limits, list prices |
| `schemas/facts.schema.json` | JSON Schema 2020-12 for `facts.json`                                                      |
| `PROVENANCE.md`             | Source notes and qualifications that don't fit in JSON                                    |

## Origin

Imported byte-identical from [gridaco/grida](https://github.com/gridaco/grida) (`data/ai/`,
commit `f053893047af`), with the shape unchanged.

## Shape

`facts.json` is an object of sections. Each section key is a dotted family path, and each
section is a table of cards keyed by card ID:

| section                           | cards                                               |
| --------------------------------- | --------------------------------------------------- |
| `text.catalog`                    | Language models                                     |
| `image.models`                    | Image generation, with per-provider bindings        |
| `video.models`                    | Video generation, with per-provider bindings        |
| `audio.music.models`              | Music generation                                    |
| `audio.sound_effects.models`      | Sound effects                                       |
| `audio.text_to_speech.models`     | Speech                                              |
| `three_d.models`                  | 3D generation endpoints                             |
| `three_d.model_generation.models` | 3D model generation                                 |
| `three_d.rigging.models`          | Rigging                                             |
| `three_d.rig_check.operation`     | One operation, not a table                          |
| `image_tools.models`              | Background removal and upscaling                    |
| `embedding.models`                | Embeddings                                          |

Every card has `id` (equal to its table key), `label`, and `release`
(`{ date, basis, source_url }`). The rest depends on the family. Image and video cards are
canonical (`vendor/model`) and hold a `providers` record of bindings keyed by provider;
other families have one card per provider endpoint.

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
