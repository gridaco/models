# Contributing

## Submitting changes

Add or correct a model by opening a pull request that changes its card in
[`models/`](./models/), regenerates the catalogue with `uv run scripts/build.py`, and cites a first-party source
for every new fact. Contributor and agent conventions live in
[`AGENTS.md`](./AGENTS.md) and [`.agents/skills/`](./.agents/skills/).

A public contract change also updates the [schema changelog](./catalogue/SCHEMA_CHANGELOG.md#maintaining-this-log)
in the same PR, including compatible extensions and changes to consumer-visible
validation or generation semantics. Explain the before/after behavior,
compatibility and migration. The PR schema-content check catches a missing log
update for changed JSON Schemas; reviewers must also check semantic changes
implemented elsewhere. Catalogue-only model, provider and price changes need no
schema entry.

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
- **One card per agent.** Agent cards in `agents/<agent-id>.toml` map exact selectable IDs
  to canonical text cards. Maintainers review public evidence for each row.
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
