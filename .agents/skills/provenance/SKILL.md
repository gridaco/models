---
name: provenance
description: >
  Ground a model's release date and record source qualifications for the AI
  model catalogue. Covers the `release` object (date, basis, source_url),
  what the date means, what must never be substituted for it, the source
  priority order, the narrow rule for `date: null`, and when to write a
  PROVENANCE.md note. Use when adding a model, auditing release dates, or
  when a price or limit needs a qualification that does not fit in JSON.
---

# Provenance

Use this when an entry needs a `release`, when an existing date is in doubt, or when a fact
needs a qualification recorded next to it.

## The `release` object

Every entry carries one:

```json
{
  "date": "2026-07-09",
  "basis": "model",
  "source_url": "https://vendor.example/release-note"
}
```

- `date`: `YYYY-MM-DD`, or `null` under the narrow rule below.
- `basis`: `model` or `provider_endpoint`.
- `source_url`: an HTTPS page that supports the date.

## What the date means

The earliest day the exact named model or variant became **broadly available**. A public
preview counts. A closed, invitation-only, or limited preview does not.

It is a fact about the model, so adding a provider binding never changes a
`basis: "model"` date. Use `basis: "provider_endpoint"` only when the fact describes a
serving route because no launch of the exact upstream model can be established. An
endpoint-shaped entry can still use `basis: "model"` when its exact underlying model and
launch are documented.

## Never substitute

- a snapshot's `generated_at`
- the date the entry was added to the catalogue
- the date one provider added a binding
- a later GA date when an exact public preview date exists
- an API object's opaque `created` timestamp
- the order of search results, a repository's commit time, or this repository's history

## Source priority

1. A vendor release note, changelog, announcement, or model card that names the exact variant.
2. A vendor-maintained repository, or official provider documentation for the exact endpoint.
3. A first-party vendor social post, when no durable release page exists.
4. Serving-provider history, only for `basis: "provider_endpoint"` or when the vendor has no
   usable record.
5. [models.dev](https://models.dev): discovery only. Verify its date against one of the above.

When two sources at the same level disagree, decide which wins and why, never average, and
record the reasoning in a provenance note.

A `source_url` is evidence. It must be HTTPS and first-party, point at the page that states
the fact (not a home page), and carry no tracking parameters, session tokens, or guessed
`#fragments`.

## When `date` may be `null`

Only with `basis: "provider_endpoint"`, and only when no authoritative source establishes
the exact day. `source_url` must still point to an HTTPS page showing the endpoint's
history. Never fill in an approximate day.

## Provenance notes

A JSON value cannot hold its own caveats. Write a note in
[`catalogue/PROVENANCE.md`](../../../catalogue/PROVENANCE.md) when a fact needs one. For example:

- A promotion: the steady-state price that was recorded, and the promotion's end date.
- A pricing band, such as long-context multipliers, with its threshold and source.
- A capability shared by a model family, with the page that states it.
- A conflict between sources, and why one was chosen.

Each note names the entry it qualifies and includes the source URLs. Update the note in the
same change as the fact it qualifies; a note that disagrees with the data is worse than none.

## Checklist

- [ ] The date is first broad public availability of the exact variant
- [ ] `basis` is right: `model` unless no upstream launch can be established
- [ ] `source_url` is first-party, HTTPS, and supports the exact date
- [ ] `null` is used only under the narrow rule
- [ ] Any qualification is in a provenance note with its sources
