# Grida Models

**A hand-curated, source-backed catalogue of AI models.**

Each entry records what a model is, what it can do, where it can be called, and what it costs.
Every fact has a source. The catalogue is maintained by hand and reviewed like code, so one
place answers "which models exist and what are they" for every Grida product.

Optional [illustrative costs](./catalogue/README.md#illustrative-costs) explain a
specific scenario separately from published rates. They carry explicit manual
provenance and may omit source links when no durable reference exists.

[Grida](https://grida.co) · [Catalogue](./catalogue/)

> **Status: early.** The catalogue is at schema version 2. Snapshots are published as
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
import agentModels from "@grida/ai-models/agent-models.json" with { type: "json" };
```

Agent Models lists documented primary model selectors for an agent access surface. Resolve
its canonical model IDs against `models.json` from the same snapshot. Use the agent's own
discovery interface for the current account's availability. Older v2 snapshots predate
Agent Models. [Agent Models contract](./catalogue/README.md#agent-models)

For fetching at runtime, use the package through jsDelivr's CDN: compressed, cached at the
edge, and with no redirects. `@2` follows the newest snapshot of schema version 2; a full
version pins one snapshot.

```
https://cdn.jsdelivr.net/npm/@grida/ai-models@2/models.json
https://cdn.jsdelivr.net/npm/@grida/ai-models@2/agent-models.json
https://cdn.jsdelivr.net/npm/@grida/ai-models@2/schemas/agent-models.schema.json
```

Pin both URLs to the same full version when the files are used together.

The GitHub Release assets suit scripts and archiving. The newest snapshot is always at:

```sh
curl -LO https://github.com/gridaco/models/releases/latest/download/models.v2.json
curl -LO https://github.com/gridaco/models/releases/latest/download/labs.v2.json
curl -LO https://github.com/gridaco/models/releases/latest/download/agent-models.v2.json
```

The `v2` in the file name is the schema version. GitHub `latest` follows the newest
release across schema majors. Assets keep versioned names, so an old asset name
stops resolving after a major change instead of serving a different shape. To pin
a snapshot, use its version instead of `latest`:
`https://github.com/gridaco/models/releases/download/<version>/models.v2.json`.

Current releases hold the following assets.

| asset                                          | contents                                                                                      |
| ---------------------------------------------- | --------------------------------------------------------------------------------------------- |
| `models.v2.json`, `labs.v2.json`               | Model cards and labs (`catalogue/models.json`, `catalogue/labs.json`)                         |
| `agent-models.v2.json`                         | Agent model profiles (`catalogue/agent-models.json`)                                          |
| `models.v2.schema.json`, `labs.v2.schema.json` | Their JSON Schemas                                                                            |
| `agent-models.v2.schema.json`                  | JSON Schema for Agent Models, also at `@grida/ai-models/schemas/agent-models.schema.json`     |
| `grida-models-<version>.tar.gz`, `.zip`        | The whole catalogue, logos included, with `LICENSE` and `manifest.json`                       |
| `manifest.json`                                | Version, schema version, source commit, content digest, counts, and the SHA-256 of every file |
| `SHA256SUMS`                                   | Checksums of the other assets: `sha256sum -c SHA256SUMS --ignore-missing`                     |

Versions read `v<schema>.<YYYYMMDD>.<n>`: the schema version,
the UTC date of the source commit, and a counter for snapshots on the same day. They are valid
semver, so a range such as `^2` follows every snapshot without crossing a breaking schema
change. A release is published only when the catalogue's content changes, and the archives
are reproducible from the same commit. Release notes list the models, labs, schemas, and
other files that changed since the previous release.

The authored [schema changelog](./catalogue/SCHEMA_CHANGELOG.md) explains contract
changes, compatibility and consumer migration. It is included in snapshot archives
and the npm package, and linked from generated release notes. Ordinary model and
price updates remain in those release notes rather than growing the schema log.

### Migrating from schema version 1

Version 2 lets a decision offering omit `underlying_model` when no relationship is
documented. Its existing meaning and all other record fields are retained. A new
record without that field fails the version 1 schema, so update the validator and
handle an absent relationship before selecting a version 2 snapshot. The Models
`$schema` value and both published schema `$id`s now end in `v2`.

Existing npm `^1` ranges and CDN `@1` URLs stay on version 1. Immutable version 1
release URLs remain available, for example:

```text
https://github.com/gridaco/models/releases/download/v1.20261113.1/models.v1.json
https://cdn.jsdelivr.net/npm/@grida/ai-models@1.20261113.1/models.json
```

Publishing the first version 2 release moves GitHub `latest`. Moving URLs such as
`releases/latest/download/models.v1.json` and the matching labs/schema assets then
stop resolving. Choose an explicit old tag to remain on version 1, or update both
the asset names and reader to version 2. Labs retain their record shape; both
schemas and asset names follow the catalogue's single release major.

The catalogue data is MIT licensed. Lab logos are trademarks of their owners and are not
covered by that license.

Snapshots describe public model facts, not a consuming application's live offering. For
models currently served by Grida, see the [model directory](https://grida.co/ai/models) or
[Gateway discovery](https://gateway.grida.ai/v1/models).

When updating a consumer, handle unfamiliar optional display metadata gracefully rather
than reject the whole catalogue. Execution and pricing fields still need explicit support.
Coordinate breaking contract changes with consumer updates.

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
- **Agent model selection is documented by surface.** Agent Models profiles map exact
  selectable IDs to canonical text cards. Maintainers review public evidence for each row.
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

A public contract change also updates the [schema changelog](./catalogue/SCHEMA_CHANGELOG.md#maintaining-this-log)
in the same PR, including compatible extensions and changes to consumer-visible
validation or generation semantics. Explain the before/after behavior,
compatibility and migration. The PR schema-content check catches a missing log
update for changed JSON Schemas; reviewers must also check semantic changes
implemented elsewhere. Catalogue-only model, provider and price changes need no
schema entry.

## License

[MIT](./LICENSE). The lab logos in `models/` and `catalogue/logos/` are trademarks of their
owners and are not covered by this license; each lab's entry links its source and, where
published, its brand guidelines.
