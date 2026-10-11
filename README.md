# Grida Models

**A hand-curated, source-backed catalogue of AI models.**

Each entry records what a model is, what it can do, where it can be called, and what it costs.
Every fact has a source. The catalogue is maintained by hand and reviewed like code, so one
place answers "which models exist and what are they" for every Grida product.

[Grida](https://grida.co) · [Catalogue](./catalogue/)

> **Status: early.** The catalogue is at schema version 1. Snapshots are published as
> [GitHub Releases](https://github.com/gridaco/models/releases); see
> [Get the catalogue](#get-the-catalogue).

## Get the catalogue

Every change to the catalogue on `main` is published as a
[release](https://github.com/gridaco/models/releases). The newest snapshot is always at:

```sh
curl -LO https://github.com/gridaco/models/releases/latest/download/facts.json
curl -LO https://github.com/gridaco/models/releases/latest/download/labs.json
```

To pin a snapshot, use its version instead of `latest`:
`https://github.com/gridaco/models/releases/download/<version>/facts.json`.

Each release holds:

| asset                                   | contents                                                                                      |
| --------------------------------------- | --------------------------------------------------------------------------------------------- |
| `facts.json`, `labs.json`               | Model cards and labs                                                                          |
| `facts.schema.json`, `labs.schema.json` | Their JSON Schemas                                                                            |
| `grida-models-<version>.tar.gz`, `.zip` | The whole catalogue, logos included, with `LICENSE` and `manifest.json`                       |
| `manifest.json`                         | Version, schema version, source commit, content digest, counts, and the SHA-256 of every file |
| `SHA256SUMS`                            | Checksums of the other assets: `sha256sum -c SHA256SUMS --ignore-missing`                     |

Versions read `v<schema>.<YYYYMMDD>.<n>`, for example `v1.20261012.0`: the schema version,
the UTC date of the source commit, and a counter for snapshots on the same day. They are valid
semver, so a range such as `^1` follows every snapshot without crossing a breaking schema
change. A release is published only when the catalogue's content changes, and the archives
are reproducible from the same commit. Release notes list the models, labs, schemas, and
other files that changed since the previous release.

The catalogue data is MIT licensed. Lab logos are trademarks of their owners and are not
covered by that license.

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
  name, first-party homepage, and official logo, published as `catalogue/labs.json` and
  `catalogue/logos/`. A card's `vendor` is a lab ID.
- **Snapshots are GitHub Releases.** Each content change to `catalogue/` on `main` is
  published as a versioned, checksummed release (`scripts/release.py`,
  `.github/workflows/release.yml`).
- **Facts only.** Product policy (which models a product lists, its tiers and defaults)
  stays with each product.

## Open decisions

These are deliberately undecided, and are tracked here so nobody mistakes them for settled.

1. **Further distribution.** Whether to publish beyond GitHub Releases: a package registry,
   a hosted HTTP endpoint, or both.
2. **Provider registry.** Whether this repository also owns display labels, logos, and
   ID-prefix rules for providers.

## Contributing

Add or correct a model by opening a pull request that changes its card in
[`models/`](./models/), regenerates `catalogue/facts.json`, and cites a first-party source
for every new fact. Contributor and agent conventions live in
[`AGENTS.md`](./AGENTS.md) and [`.agents/skills/`](./.agents/skills/).

## License

[MIT](./LICENSE). The lab logos in `models/` and `catalogue/logos/` are trademarks of their
owners and are not covered by this license; each lab's entry links its source and, where
published, its brand guidelines.
