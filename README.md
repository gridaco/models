# Grida Models

**A hand-curated, source-backed catalogue of AI models.**

Each entry records what a model is, what it can do, where it can be called, and what it costs.
Every fact has a source. The catalogue is maintained by hand and reviewed like code, so one
place answers "which models exist and what are they" for every Grida product.

[Grida](https://grida.co) · [Catalogue](./catalogue/)

> **Status: early.** The catalogue is at schema version 1. How it is distributed is not
> decided yet; see [Open decisions](#open-decisions).

## Why

Model metadata fragments quickly. The same model ID, context window, price, or release date
ends up in an application package, a gateway's route table, a pricing page, a marketing
section, and a CLI, and each copy drifts on its own schedule. A stale entry is not a
conservative answer; it is a wrong one.

This repository is meant to be the single place those facts are authored. Everything else
consumes a projection of it.

## What is in a catalogue entry

| Kind                   | Examples                                                                                      |
| ---------------------- | --------------------------------------------------------------------------------------------- |
| **Identity**           | Canonical ID (`vendor/model`), label, vendor, family (text, image, video, audio, 3D, …)       |
| **Release provenance** | First broad public release date, its basis, and the first-party source URL                    |
| **Capabilities**       | Modalities, accepted image formats, tool calling, audio, transparent background               |
| **Limits**             | Context window, output limit, sizes, aspect ratios, durations, size constraints               |
| **Provider bindings**  | The exact ID a provider uses for the model (Vercel AI Gateway, fal, OpenRouter, Replicate, …) |
| **Published prices**   | Public list prices per provider, in the provider's own billing unit                           |

## What it is not

- **Not a router or SDK.** A provider binding records that an endpoint exists and what it
  costs. It does not implement a client or grant permission to call it.
- **Not billing.** The catalogue holds published list prices. Credits, markups, tariffs, and
  negotiated or account-specific rates belong to their owners, not here.
- **Not a live mirror.** Nothing is scraped into this repository automatically. Discovery
  tools such as [models.dev](https://models.dev) give leads; a person verifies each fact
  against a first-party source.
- **Not an endorsement.** Being catalogued does not mean any Grida product offers the model.
  Which models a product lists, and in what order, is that product's decision.

Each model is authored as one TOML card in [`models/`](./models/), grouped by lab
(`models/openai/gpt-5.5/card.toml`). The contract consumers read,
[`catalogue/facts.json`](./catalogue/facts.json), is generated from those cards: plain JSON
with a JSON Schema, readable from any language. Its shape and rules are documented in
[`catalogue/README.md`](./catalogue/README.md).

## Principles

- **Every fact has a source.** Prices, limits, and release dates cite a first-party page.
- **The catalogue states what is true now.** Price the steady state, not the promotion.
  Deprecate a model someone might still pick; remove one whose successor is strictly better.
- **An ID is never portable.** The same model has different IDs, availability, and prices on
  different providers. Bindings are recorded per provider.
- **Additive by default.** Consumers depend on the shape. Fields are added; breaking changes
  get a new schema version.

## Decided

- **The contract is language-agnostic.** Consumers read JSON, JSON Schema, and provenance
  notes. Tooling and tests use whichever language fits (currently Python). Typed bindings
  and code generation live in each consumer.
- **One card per model.** Facts are authored as TOML cards in `models/<lab>/<model>/`, and
  `catalogue/facts.json` is generated from them. A card's directory leaves room for
  per-model material such as example assets.
- **Labs are registered.** Each lab directory holds a `lab.toml` with the lab's display
  name and first-party homepage, published as `catalogue/labs.json`. A card's `vendor` is a
  lab ID.
- **Facts only.** Product policy (which models a product lists, its tiers and defaults)
  stays with each product.

## Open decisions

These are deliberately undecided, and are tracked here so nobody mistakes them for settled.

1. **Distribution.** How consumers pin and receive the catalogue: tagged releases, a
   published package, a submodule, an HTTP endpoint, or a combination.
2. **Provider registry and logos.** Whether this repository also owns display labels and
   ID-prefix rules for providers, and logo assets for labs or providers.

## Contributing

Add or correct a model by opening a pull request that changes its card in
[`models/`](./models/), regenerates `catalogue/facts.json`, and cites a first-party source
for every new fact. Contributor and agent conventions live in
[`AGENTS.md`](./AGENTS.md) and [`.agents/skills/`](./.agents/skills/).

## License

[MIT](./LICENSE).
