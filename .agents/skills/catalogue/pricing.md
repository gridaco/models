# Pricing shapes

Supplements [`SKILL.md`](./SKILL.md). Load this when you add or change a price.

## Rules

- **Published list price, in the provider's unit.** Record what the provider's public
  pricing page says, in the unit it bills: per million tokens, per image, per second, per
  run, per 1,000 characters, or provider credits with their published USD rate. Do not
  convert currencies. Exact decimal unit normalization is allowed when both the source
  unit and contract unit are explicit; it must not round or change billing semantics.
- **A price belongs to a binding.** The same model can cost different amounts on different
  providers. Each binding or endpoint carries its own price without changing intrinsic
  model facts. Public Grida service prices are eligible; its supplier selection, funding
  fees, credit conversions and margin are not catalogue data.
- **Regular, non-promotional rates only, even during an active promotion.** Do not
  maintain promotional prices, expiry dates, or a promotion calendar. Verify the regular
  rate from that provider's own source; a discounted feed or another provider's rate is
  insufficient. See the lifecycle rules in [`SKILL.md`](./SKILL.md).
- **No usable unit, no price.** If a provider shows a placeholder price (for example,
  $0/MTok for video), leave that price out. A verified endpoint can still have a binding;
  document unknown regular rates. Use a sourced exclusion only for a contract that cannot
  be reliably listed, not to hide unfinished research.
- **Estimates are not prices.** `avg_cost_usd` and `cost_usd` are coarse per-request
  estimates, not published facts. Keep them consistent with the published rates and never
  cite them as a source.

## Shapes in use

These are the `pricing.type` values in the current authored data. Before adding a new
shape, check whether an existing one can express the price without loss.

`published_pricing` is an additive provider-neutral shape for publicly advertised
USD meter components, conditions, request-wide quantity bands, and quantity
rounding. Its contract is in
[`catalogue/README.md`](../../../catalogue/README.md#published-service-prices-and-contracts).
Use it only from the service's own public evidence. Its source is the advertised
price, not assumptions about that service's suppliers or margins.

`token_pricing` records exact decimal USD-per-token rates. Keep cache-write TTLs
distinct: `input_cache_write_1h` records the one-hour rate when published;
`scope` qualifies the standard tier and the base cache-write duration. A
cache-storage-per-hour amount is a different unit and must not be inserted as
a per-token write price.

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
3. Verify that the quoted rate is regular and non-promotional. Record its source and
   applicable conditions (region, service tier, batch mode, billing unit) in
   `PROVENANCE.md` when needed. Do not record promotional rates or end dates. If public
   sources establish only a promotional rate, leave the regular price unrecorded and
   document the verification gap; do not guess it.
4. If two first-party pages disagree, follow "When sources disagree" in
   [`SKILL.md`](./SKILL.md).
