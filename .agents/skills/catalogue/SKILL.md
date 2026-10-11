---
name: catalogue
description: >
  Research, add, update, deprecate, or remove AI model catalogue entries —
  text, image, video, audio, 3D, image tools, and embedding models — with
  their capabilities, limits, provider bindings, and published prices.
  Covers what an entry is, per-provider ID rules, pricing shapes, lifecycle
  rules (steady-state pricing, deprecate vs. delete), and the verification
  checklist. Use when bumping a model version, adding a model or provider
  binding, updating a price, or auditing entries against provider docs.
  Release dates are covered by $provenance.
---

# Catalogue — research and update workflow

Use this when a model fact changes: a new model or version, a new provider route, a price
change, a limit correction, a deprecation, or an audit against provider documentation.

## Where to edit

| file                                   | holds                                                                                   |
| -------------------------------------- | --------------------------------------------------------------------------------------- |
| `models/<lab>/<model>/card.toml`       | One card: identity, release provenance, provider bindings, capabilities, limits, prices |
| `models/<lab>/lab.toml`                | The lab's display name and first-party homepage. Required for every lab                 |
| `catalogue/models.json`                | Generated from `models/` by `scripts/build.py`. Never edit by hand                      |
| `catalogue/schemas/models.schema.json` | JSON Schema for `models.json`                                                           |
| `catalogue/PROVENANCE.md`              | Source notes and qualifications that do not fit in JSON                                 |

Card layout and the `section` / `null_keys` authoring keys are in
[`models/README.md`](../../../models/README.md); the shape and its rules are in
[`catalogue/README.md`](../../../catalogue/README.md). Product
policy (which models a product lists, tiers, defaults) is not part of the catalogue.

## What an entry is

An entry is a set of facts about one model, each traceable to a source:

- **Identity:** `id`, `label`, `vendor`, family.
- **Release:** see `$provenance`.
- **Capabilities:** modalities, accepted image MIME types, tool calling, audio, transparent
  background, and so on. Never derive one capability from another (for example, image MIME
  types from `multimodal`); record each from its own source.
- **Limits:** context window and output limit (text); sizes, size constraints, aspect ratios
  (image); durations and aspect ratios (video).
- **Bindings:** for each provider that serves it, the provider's exact ID, its published
  price, and optionally a URL and a deprecation flag.

Facts are independent of products. Adding a verified fact does not list the model in any
Grida product, and removing a product listing does not delete the fact.

## IDs are never portable

The same model has different IDs, availability, and prices on different providers.

- **Text, audio, image tools, 3D:** one entry per provider endpoint. The `id` is in that
  provider's format, and the provider or namespace fixes the route.
- **Image and video:** one canonical entry (`vendor/model`, e.g. `google/veo-3.1`) holding the
  model's intrinsic facts, plus a `providers` record keyed by provider. Each binding has its
  own call ID and price. Bindings carry no preference order; choosing a provider is a
  consumer's decision.

Preserve IDs exactly as the provider spells them. Never case-convert or normalize them.
Per-provider ID formats, pricing pages, and known quirks are in
[`providers.md`](./providers.md).

## Lifecycle rules

The catalogue states what is true and useful **now**. Its shape must never record how
recently someone got round to updating it.

- **Price the steady state, not the promotion.** If a vendor runs an introductory or
  time-limited rate, record the price that applies after it ends, and note the promotion and
  its end date in `PROVENANCE.md`. Otherwise the promotion ending is a silent cost increase.
  Recheck when the date passes: a promotion can become permanent, which changes the fact.
- **Deprecate an entry that is still a real choice.** Mark it deprecated (Grida's
  `legacy: true`) when someone might reasonably still pick it: same price as its successor,
  or better at something.
- **Delete an entry whose successor is strictly dominant:** never worse on any axis, better
  on at least one. An entry nobody should choose is noise in every picker.
- **A binding needs a usable, verified price.** If a provider exposes no billable unit for a
  model (for example, a $0/MTok placeholder for video), leave that binding out rather than
  inventing a price.
- **Catalogue only what is used.** Do not add a capability, endpoint variant, or field for a
  case nobody serves yet. Add it when the second case arrives.

Removing an entry is a contract change for consumers: some embed the catalogue at build
time and only see the change in their next release. Say so in the PR.

## When sources disagree

- **Intrinsic facts** (release, capabilities, limits) come from the vendor. **Binding facts**
  (call ID, binding price, served resolutions) come from that provider's own page; another
  provider's page is not evidence.
- Aggregators (models.dev, comparison sites, search snippets) are leads, never sources. A
  remembered value is a claim about the past; re-read the page.
- Copies in consumers (generated literals, snapshots, hand-copied docs tables) are never
  authoritative, even when they agree. Report their drift; don't edit the catalogue to match.
- When two first-party sources conflict, first check they describe the same thing (variant,
  provider, region, tier, resolution, date). If they truly conflict, decide which wins and
  why (more specific page, dated changelog), record it in `catalogue/PROVENANCE.md`, and
  never average. If it can't be resolved from public sources, leave the value and ask.

## Pricing

Record the provider's published list price in the provider's own billing unit. Never
convert to credits, add margin, or substitute a negotiated or account-specific rate. The
pricing shapes in use and their rules are in [`pricing.md`](./pricing.md).

## Workflow

1. **Discover.** Use the lookup script for leads:

   ```sh
   python3 -I .agents/skills/catalogue/scripts/model_info.py <model_id>
   python3 -I .agents/skills/catalogue/scripts/model_info.py --image <model_id>
   python3 -I .agents/skills/catalogue/scripts/model_info.py --image --all
   ```

   It reads [models.dev](https://models.dev/api.json). Treat everything it prints as a lead:
   it has per-token prices but no per-image tiers, and its release dates are hints.

2. **Verify.** Confirm each fact on a first-party page: the vendor's model page or pricing
   page, or the provider's own page for a binding. See [`providers.md`](./providers.md).
3. **Ground the release.** Follow `$provenance`.
4. **Edit the card in `models/`.** A new model gets a new directory at
   `models/<lab>/<model>/card.toml` (see [`models/README.md`](../../../models/README.md)).
   A model from a new lab also needs `models/<lab>/lab.toml`, sourced from the lab's own
   homepage, and its official logo (see [`models/README.md`](../../../models/README.md#a-lab)).
   Fields are `lower_snake_case`; IDs keep their exact spelling. Run
   `uv run scripts/build.py`, then `uv run scripts/check.py`.
5. **Record qualifications** that do not fit the JSON (promotions, long-context bands,
   ambiguous units) in `catalogue/PROVENANCE.md`, with source URLs.

## After any update

- [ ] Every new or changed fact has a first-party source, cited in the PR description
- [ ] No value was estimated, rounded, or copied from an aggregator without verification
- [ ] Prices are published list prices in the provider's own unit, at the steady state
- [ ] IDs are exact; field names are `lower_snake_case`
- [ ] Every entry has a complete `release` (`$provenance`)
- [ ] Deprecated vs. deleted was decided by the lifecycle rules above
- [ ] `catalogue/models.json` was regenerated with `uv run scripts/build.py`, not edited by hand
- [ ] `uv run scripts/check.py` passes
- [ ] Nothing from a private source made it into the diff, the commit, or the PR (see `AGENTS.md`)
