# Schema changelog

Authored history of the catalogue's public contract: fields, validation rules and
their meanings. Model additions, provider coverage and price changes belong in
the generated [snapshot release notes](https://github.com/gridaco/models/releases).

Entries are grouped by schema major, newest first. Entry dates identify when a
change was documented; tagged releases establish when a snapshot was published.
An entry linked to an open PR does not mean the change has been released. See
[Maintaining this log](#maintaining-this-log) for contributor requirements.

## Schema v2

### 2026-11-21 — Agent Models catalogue

References [issue #64](https://github.com/gridaco/models/issues/64) and
[PR #65](https://github.com/gridaco/models/pull/65).

**Change** adds `agent-models.json` and its schema. The `agents` map holds one
card per agent, linking exact primary model selectors to canonical `text.catalog` IDs.
Each selector has a first-party source and can record sourced Fast and Ultrafast
service tiers on that same selector.

**Compatibility** is additive within schema v2. The Agent Models schema is a
separate contract and supports an empty `agents` map.

**Migration** is optional. Use the Agent Models asset from the same pinned snapshot
as `models.json` when resolving canonical model IDs. Use the agent's live discovery
for the active account's choices.

### 2026-11-19 — Text bindings may describe Fast offerings and modes

References [issue #53](https://github.com/gridaco/models/issues/53) and
[PR #54](https://github.com/gridaco/models/pull/54).

**Change** adds optional `offerings` and `modes` on text provider bindings. A
dedicated Fast call ID has its own offering record linked to its canonical model.
Same-ID Fast uses `modes.fast` with a provider request selector. The records carry
their own sourced serving terms. Existing input endpoints retain their meaning.
Generation rejects non-finite numbers, including in nested request selectors,
before writing catalogue JSON.

**Compatibility** is additive. Existing cards continue to validate, and the
previous v2 schema accepts the new optional binding fields. The v2 envelope,
model IDs and existing binding and price fields retain their meanings.

**Migration** is optional for consumers using existing fields. Consumers that
offer exact provider-ID lookup can index dedicated `offerings` by provider and
call ID. Consumers that display same-ID Fast should read `modes.fast` on the base
binding. Review compatibility before defining additional modes.

### 2026-11-15 — Decision offerings may omit an underlying model

Reference: [#44](https://github.com/gridaco/models/pull/44).

**Change:** `decision_card.underlying_model` is optional. It continues to record
the canonical identity of a documented underlying model when present, with the
existing nonempty-string constraint. Omission means no relationship is recorded;
it does not infer a parent, a self-reference or inherited chat capabilities.

The validation change is:

```diff
- "required": ["vendor", "underlying_model", "providers"]
+ "required": ["vendor", "providers"]
```

**Compatibility:** breaking for v1 readers that require this relationship. The
new validator accepts cards with the relationship retained, but a newly emitted
card without it fails the old v1 validator. The Models `$schema`, both schema
`$id`s and release/package major move to v2. Labs retain their record shape and
follow the same release major.

`decision.models` remains semantic grouping, not a shared execution protocol.
Provider request/result contracts, uncertainty meanings, usage and prices remain
independent. No new primitive set, model card or published rate is introduced.

**Migration:** update the reader/validator before selecting a v2 snapshot and
handle an absent relationship. Existing v1 pins remain on v1; GitHub `latest`
moves across majors, so moving v1 asset URLs stop resolving after the first v2
release. See the [v1-to-v2 migration instructions](https://github.com/gridaco/models/blob/5fd023df088af38a135246c8e476f60d7c30cbc6/README.md#migrating-from-schema-version-1)
for schema identifiers, asset names and pin choices.

## Schema v1

Version 1 predates this authored log. Its contract history remains in the
[tagged snapshots and release notes](https://github.com/gridaco/models/releases)
and [schema Git history](https://github.com/gridaco/models/commits/main/catalogue/schemas).
This log starts with the v2 transition rather than reconstructing an incomplete
history of v1 changes.

## Maintaining this log

Update this file in the same PR as a public contract change, including compatible
extensions. This covers added/removed fields, requiredness, types, enum values,
constraints and field meanings, plus consumer-visible validation or generation
behavior implemented outside the JSON Schemas. A new model fitting the existing
contract needs no entry.

Keep each entry short: state the field/rule and before/after behavior, whether
the change is breaking, the consumer action needed (or why none is needed), and
the PR link. Add dated entries under the relevant schema major; changing snapshot
dates or counters does not create another entry. Follow the catalogue's existing
[versioning rules](https://github.com/gridaco/models/blob/main/catalogue/README.md#rules)
for a breaking change.

Exclude model facts, model/provider additions, rates, provenance-only corrections,
tooling-only refactors and formatting-only changes. Preserve published history;
make corrections explicit instead of silently rewriting an earlier contract's
meaning.

The PR check compares JSON content under `catalogue/schemas/` and requires a
non-whitespace changelog update when that content changes, including schema
additions or removals. It ignores JSON formatting and object-key order. This
check cannot judge prose accuracy or detect every behavioral change outside the
schemas: contributors and reviewers must check those changes against this log.
