---
name: catalogue
description: >
  Research, add, update, deprecate, or remove AI model catalogue entries —
  text, decision, image, video, audio, 3D, image tools, and embedding models — with
  their capabilities, limits, provider bindings, and published prices.
  Covers what an entry is, per-provider ID rules, regular pricing, native
  reference and provider coverage, public distribution, and the verification
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
- **Distribution:** official code and weight links, exact weight variants, access
  conditions, and separately sourced code/weight licenses. Use the model-level
  `distribution` shape in [`catalogue/README.md`](../../../catalogue/README.md#model-distribution).
  Leave unknown facts omitted. Available weights do not establish a native hosted API;
  public downloads do not establish an open-source classification or unrestricted use.
- **Capabilities:** modalities, accepted image MIME types, tool calling, audio, transparent
  background, and so on. Never derive one capability from another (for example, image MIME
  types from `multimodal`); record each from its own source.
- **Limits:** context window and output limit (text); sizes, size constraints, aspect ratios
  (image); durations and aspect ratios (video).
- **Bindings:** exact call IDs, sourced regular prices when known, and provider-specific
  contracts. A native `reference_provider` is a presentation choice. Explicit
  `provider_coverage` distinguishes listed providers from source-backed absence/exclusion.

Facts are independent of products. Adding a verified fact does not list the model in any
Grida product, and removing a product listing does not delete the fact.

## IDs are never portable

The same model has different IDs, availability, and prices on different providers.

- **Text, audio, image tools, 3D:** retain existing endpoint-shaped IDs and direct-provider
  facts. Add `providers` bindings without rewriting those existing identities.
- **Image and video:** one canonical entry (`vendor/model`, e.g. `google/veo-3.1`) holding the
  model's intrinsic facts, plus a `providers` record keyed by provider. Each binding has its
  own call ID and price. `reference_provider` identifies the verified native API to show
  first; choosing which provider to call remains a consumer decision.

Preserve IDs exactly as the provider spells them. Never case-convert or normalize them.
Per-provider ID formats, pricing pages, and known quirks are in
[`providers.md`](./providers.md).

## Lifecycle rules

The catalogue states what is true and useful **now**. Its shape must never record how
recently someone got round to updating it.

- **Regular, non-promotional prices only.** Record the provider's sourced regular rate,
  even when an introductory or time-limited discount is active when adding or updating a
  model. Do not track promotional rates, end dates, or expiry rechecks. A discounted live
  feed does not establish the regular price; do not infer it from a discount percentage or
  another provider's rate. If the regular rate cannot be verified, report the missing
  evidence and leave the price unrecorded.
- **Preserve existing entries during coverage work.** Do not delete a model because a
  successor exists or because a consumer does not currently serve it. Lifecycle and
  offering changes need separate review. Do not introduce product policy fields.
- **Unknown prices remain unknown.** Verified endpoint existence can be recorded without
  a price. A $0/MTok video placeholder is not a usable unit; omit that price and record
  the qualification. If the contract itself cannot be represented reliably, use a
  source-backed exclusion rather than inventing capabilities or amounts.
- **Coverage is source-backed.** Add the native API and verified OpenRouter, Vercel and
  fal media bindings. Add Grida only where its public service actually offers the model.
  An unserved catalogue entry remains useful; do not invent a Grida binding.

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
  never average. If it cannot be resolved from public sources, leave the disputed fact
  unrecorded and document the gap. Aggregate behavioral questions for a separately
  approved probe; do not make paid inference calls as part of catalogue maintenance.

## Pricing

Record the provider's advertised regular price in its published billing unit. Public
Grida prices are provider facts too; they do not authorize disclosing internal economics
or deriving a different price from another provider. Never convert to credits, add an
internal margin, or substitute a negotiated/account-specific rate. The
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
5. **Record qualifications** that do not fit the JSON (regular-price evidence,
   long-context bands, ambiguous units) in `catalogue/PROVENANCE.md`, with source URLs.

## Decision offerings

Decision endpoints are distinct offerings even when they share the underlying chat
model. Author them in `decision.models`, with `underlying_model` pointing at that
canonical model. Qualify each provider's exact `interface`, question vocabulary,
input envelope and decision-only rates. Do not copy chat cache/output prices, tools,
reasoning parameters or limits. Put contract differences on sourced
`decision_contract` records and unresolved conflicts in provenance. See
[`catalogue/README.md`](../../../catalogue/README.md#decision-offerings).

## Reference pattern: text and image additions

The GPT-6 Sol, GPT-6 Luna, GPT-6.1 Sol and Gemini Nano Banana 2.1 cards demonstrate
a data-only addition across modalities ([reference PR #13](https://github.com/gridaco/models/pull/13)). Use their structure, not their values, as
the starting point for another model:

- Read the exact native model contract before copying a predecessor. GPT tool
  support varies by API and reasoning effort; Nano Banana 2.1 has different
  resolutions and billing meters from Nano Banana 2.
- Keep each provider's prices, thresholds, limits and parameter differences.
  A token-priced image example is not a fixed image price. A supported vision
  input does not establish a tokenization formula.
- Preserve unknown facts as sourced qualifications. Do not infer another
  model's image-token multiplier or another provider's regular rates.
- Add only verified service bindings. A consumer's planned launch is not public
  availability; add its binding after its published discovery and contracts
  confirm the offering.
- Regenerate and validate the catalogue, run `uv run pytest` and the pinned
  formatter, and review the complete diff. Submit the cards, generated output
  and provenance together. After merge, verify the automatic release contains
  those cards. Publishing this catalogue does not deploy a consuming service.

Free validation verifies the catalogue contract, not hosted inference behavior.
Record behavioral uncertainties for a separately approved, bounded paid test;
do not make catalogue checks consume provider credits.

## After any update

- [ ] Every new or changed fact has a first-party source, cited in the PR description
- [ ] No value was estimated, rounded, or copied from an aggregator without verification
- [ ] Prices are sourced regular, non-promotional rates in the provider's own unit;
      promotional rates and expiry tracking are excluded
- [ ] IDs are exact; field names are `lower_snake_case`
- [ ] Distribution links are official; code and weight licenses/access are independently
      sourced, with no inferred hosted API or license permissions
- [ ] Every entry has a complete `release` (`$provenance`)
- [ ] Native reference, canonical provider coverage and any exclusions are sourced; existing
      model identities and unserved entries are preserved
- [ ] `catalogue/models.json` was regenerated with `uv run scripts/build.py`, not edited by hand
- [ ] `uv run scripts/check.py` passes
- [ ] Nothing from a private source made it into the diff, the commit, or the PR (see `AGENTS.md`)
