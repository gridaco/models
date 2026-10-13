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
[release](https://github.com/gridaco/models/releases) and as the npm package
[`@grida/ai-models`](https://www.npmjs.com/package/@grida/ai-models), which holds the same
files and no code.

```sh
npm install @grida/ai-models
```

```js
import models from "@grida/ai-models/models.json" with { type: "json" };
```

For fetching at runtime, use the package through jsDelivr's CDN: compressed, cached at the
edge, and with no redirects. `@1` follows the newest snapshot of schema version 1; a full
version pins one snapshot.

```
https://cdn.jsdelivr.net/npm/@grida/ai-models@1/models.json
https://cdn.jsdelivr.net/npm/@grida/ai-models@1.20261011.1/models.json
```

The GitHub Release assets suit scripts and archiving. The newest snapshot is always at:

```sh
curl -LO https://github.com/gridaco/models/releases/latest/download/models.v1.json
curl -LO https://github.com/gridaco/models/releases/latest/download/labs.v1.json
```

The `v1` in the file name is the schema version. `latest` always serves the newest snapshot
that is compatible with it; after a breaking change, the `v1` names stop resolving instead of
serving a different shape. To pin a snapshot, use its version instead of `latest`:
`https://github.com/gridaco/models/releases/download/<version>/models.v1.json`.

Each release holds:

| asset                                          | contents                                                                                      |
| ---------------------------------------------- | --------------------------------------------------------------------------------------------- |
| `models.v1.json`, `labs.v1.json`               | Model cards and labs (`catalogue/models.json`, `catalogue/labs.json`)                         |
| `models.v1.schema.json`, `labs.v1.schema.json` | Their JSON Schemas                                                                            |
| `grida-models-<version>.tar.gz`, `.zip`        | The whole catalogue, logos included, with `LICENSE` and `manifest.json`                       |
| `manifest.json`                                | Version, schema version, source commit, content digest, counts, and the SHA-256 of every file |
| `SHA256SUMS`                                   | Checksums of the other assets: `sha256sum -c SHA256SUMS --ignore-missing`                     |

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

| Kind                      | Examples                                                                                |
| ------------------------- | --------------------------------------------------------------------------------------- |
| **Identity**              | Canonical ID (`vendor/model`), label, vendor, family (text, image, video, audio, 3D, …) |
| **Release provenance**    | First broad public release date, its basis, and the first-party source URL              |
| **Capabilities**          | Modalities, accepted image formats, tool calling, audio, transparent background         |
| **Limits**                | Context window, output limit, sizes, aspect ratios, durations, size constraints         |
| **Provider bindings**     | Exact provider IDs, a native API reference, and sourced coverage/exclusion reasons      |
| **Model distribution**    | Official code and weight links, exact variants, access conditions and separate licenses |
| **Published prices**      | Public list prices per provider, in the provider's own billing unit                     |
| **Published calculators** | Sourced output-token formulae, examples, and image-input tokenization rules             |

## What it is not

- **Not a router or SDK.** A provider binding records that an endpoint exists and what it
  costs. It does not implement a client or grant permission to call it.
- **Not billing execution.** The catalogue holds publicly advertised regular prices,
  including Grida's public service price. Funding fees, credit conversion, margins,
  supplier selection and negotiated/account-specific rates stay with their owners.
- **Not a live mirror.** Nothing is scraped into this repository automatically. Discovery
  tools such as [models.dev](https://models.dev) give leads; a person verifies each fact
  against a first-party source.
- **Not an endorsement.** Being catalogued does not mean any Grida product offers the model.
  Which models a product lists, and in what order, is that product's decision.

Each model is authored as one TOML card in [`models/`](./models/), grouped by lab
(`models/openai/gpt-5.5/card.toml`). The contract consumers read,
[`catalogue/models.json`](./catalogue/models.json), is generated from those cards: plain JSON
with a JSON Schema, readable from any language. Its shape and rules are documented in
[`catalogue/README.md`](./catalogue/README.md).

## Principles

- **Every fact has a source.** Prices, limits, and release dates cite a first-party page.
- **Regular prices, without promotion tracking.** Record sourced, non-promotional
  provider rates even during an active discount. Do not maintain discounted prices or
  promotion expiry dates. Existing models remain available for consumer review; provider
  coverage changes do not silently remove them.
- **An ID is never portable.** The same model has different IDs, availability, parameters
  and prices on different providers. Bindings retain those differences. A sourced native
  `reference_provider` is presented first; it does not choose a consumer's route.
- **Additive by default.** Consumers depend on the shape. Fields are added; breaking changes
  get a new schema version.

## Decided

- **The contract is language-agnostic.** Consumers read JSON, JSON Schema, and provenance
  notes. Tooling and tests use whichever language fits (currently Python). Typed bindings
  and code generation live in each consumer.
- **One card per model.** Facts are authored as TOML cards in `models/<lab>/<model>/`, and
  `catalogue/models.json` is generated from them. A card's directory leaves room for
  per-model material such as example assets.
- **Labs are registered.** Each lab directory holds a `lab.toml` with the lab's display
  name, first-party homepage, and official logo, published as `catalogue/labs.json` and
  `catalogue/logos/`. A card's `vendor` is a lab ID.
- **Snapshots are GitHub Releases and an npm package.** Each content change to `catalogue/`
  on `main` is published as a versioned, checksummed release and as `@grida/ai-models` on
  npm, through trusted publishing (`scripts/release.py`, `.github/workflows/release.yml`).
- **Facts only.** Product policy (which models a product lists, its tiers and defaults)
  stays with each product.

## Open decisions

These are deliberately undecided, and are tracked here so nobody mistakes them for settled.

1. **Hosted endpoint.** Whether to serve the catalogue from a domain of its own, beyond
   GitHub Releases, npm, and the CDNs that mirror npm.
2. **Provider registry.** Whether this repository also owns display labels, logos, and
   ID-prefix rules for providers.

## Contributing

Add or correct a model by opening a pull request that changes its card in
[`models/`](./models/), regenerates `catalogue/models.json`, and cites a first-party source
for every new fact. Contributor and agent conventions live in
[`AGENTS.md`](./AGENTS.md) and [`.agents/skills/`](./.agents/skills/).

## License

[MIT](./LICENSE). The lab logos in `models/` and `catalogue/logos/` are trademarks of their
owners and are not covered by this license; each lab's entry links its source and, where
published, its brand guidelines.
