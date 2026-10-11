# Pricing shapes

Supplements [`SKILL.md`](./SKILL.md). Load this when you add or change a price.

## Rules

- **Published list price, in the provider's unit.** Record what the provider's public
  pricing page says, in the unit it bills: per million tokens, per image, per second, per
  run, per 1,000 characters, or provider credits with their published USD rate. Do not
  convert units or currencies.
- **A price belongs to a binding.** The same model can cost different amounts on different
  providers. On canonical entries (image, video), each binding carries its own `pricing`.
- **Steady state, not promotion.** See the lifecycle rules in [`SKILL.md`](./SKILL.md).
- **No usable unit, no binding.** If a provider shows a placeholder price (for example,
  $0/MTok for video), leave the binding out.
- **Estimates are not prices.** `avg_cost_usd` and `cost_usd` are coarse per-request
  estimates, not published facts. Keep them consistent with the published rates and never
  cite them as a source.

## Shapes in use

These are the `pricing.type` values in the current authored data. Before adding a new
shape, check whether an existing one can express the price without loss.

### Text

Text entries use a `cost` object instead of a typed `pricing` union. Values are USD per
1M tokens. The values below are illustrative:

```json
{
  "input": 5,
  "output": 30,
  "cache_read": 0.5,
  "cache_write": 6.25,
  "long_context": { "input_tokens_above": 272000, "input_multiplier": 2, "output_multiplier": 1.5 }
}
```

`long_context` records a request-wide price band: above the token threshold, the whole
request is billed at the multipliers. Note the source for the threshold in `PROVENANCE.md`.

### Image

| type               | shape                                                          | typical provider |
| ------------------ | -------------------------------------------------------------- | ---------------- |
| `per_image_tiered` | `tiers: { "<quality>/<W>x<H>": usd }`, optional `tokens` rates | OpenAI, fal      |
| `per_image_flat`   | `usd`                                                          | BFL, fal         |
| `per_token`        | `input`, `output`, optional `cached_input`, `image_input`, …   | Google, Vercel   |

### Video

`per_second`, keyed by the exact `(resolution, audio mode)` combinations the provider serves
and meters, with an optional `usd_per_input_image` surcharge:

```json
{
  "type": "per_second",
  "usd_per_second": {
    "720p": { "audio": 0.4, "silent": 0.2 },
    "1080p": { "audio": 0.4, "silent": 0.2 },
    "4k": { "audio": 0.6, "silent": 0.4 }
  }
}
```

List only the combinations that provider actually sells. If a provider does not sell 4K or
silent output, omit those keys rather than copying another provider's rates.

### Audio

| type                  | shape                                                                  |
| --------------------- | ---------------------------------------------------------------------- |
| `per_run_flat`        | `usd` per generation                                                   |
| `per_1000_characters` | `usd` per 1,000 input characters                                       |
| `provider_credits`    | Credit counts as published; the credit's USD rate stated by its source |

### 3D

| type                                  | shape                                                          |
| ------------------------------------- | -------------------------------------------------------------- |
| `per_generation_base_plus_surcharges` | `base_usd` plus named `surcharges_usd` for options             |
| `per_generation_credits`              | Credit counts per option, `usd_per_credit`, and a `source_url` |

### Embedding

`per_token_input`: `input` in USD per 1M input tokens.

## Verifying a price

1. Open the provider's own pricing page or model page (see [`providers.md`](./providers.md)).
2. Record the date you checked it in the PR description.
3. If the page qualifies the price (region, tier, batch discount, promotion end date), note
   the qualification and URL in `PROVENANCE.md`.
4. If two first-party pages disagree, follow "When sources disagree" in
   [`SKILL.md`](./SKILL.md).
