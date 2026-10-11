# Providers, IDs, and sources

Supplements [`SKILL.md`](./SKILL.md). Load this when you add a binding or look up where to
verify a fact.

## Vendor vs. provider

- **Vendor:** who made the model (OpenAI, Anthropic, Google, Black Forest Labs, ByteDance,
  …). Intrinsic facts such as release date, capabilities, and limits come from the vendor.
- **Provider:** who serves an endpoint for it (Vercel AI Gateway, fal, OpenRouter,
  Replicate, or the vendor's own API). Binding IDs and binding prices come from the
  provider.

Adding a provider binding never changes a vendor fact. For example, a new route does not
change a `basis: "model"` release date.

## ID formats

| provider          | ID format, examples                                                     |
| ----------------- | ----------------------------------------------------------------------- |
| Vercel AI Gateway | `vendor/model`: `google/veo-3.1-generate-001`, `bytedance/seedance-2.0` |
| fal               | Endpoint path: `fal-ai/veo3.1/image-to-video`, `fal-ai/flux-2-pro/edit` |
| OpenRouter        | `vendor/model`: `google/veo-3.1`, `google/veo-3.1-fast`                 |
| Replicate         | `owner/model`: `google/lyria-3`, `nightmareai/real-esrgan`              |

On fal, the capability is often part of the ID (`…/image-to-video`, `…/edit`). A different
capability on fal is a different endpoint, so it is a different binding.

## Where to verify

| source            | URL                                                                                                        |
| ----------------- | ---------------------------------------------------------------------------------------------------------- |
| OpenAI            | `https://developers.openai.com/api/docs/models/<model_id>`                                                 |
| Anthropic         | `https://docs.anthropic.com/en/docs/about-claude/models`                                                   |
| Google            | `https://ai.google.dev/pricing`                                                                            |
| Black Forest Labs | `https://docs.bfl.ml/pricing`                                                                              |
| fal               | `https://fal.ai/models/<endpoint-id>`; pricing API: `https://fal.ai/docs/documentation/model-apis/pricing` |
| OpenRouter        | `https://openrouter.ai/<vendor>/<model>`                                                                   |
| Vercel AI Gateway | `https://vercel.com/ai-gateway/models/<model>`                                                             |
| models.dev        | `https://models.dev/api.json`. **Discovery only**, never a source                                          |

## Known quirks

- **Availability differs by provider.** A model can be on OpenRouter and fal but not on the
  Vercel AI Gateway. A canonical entry simply omits the binding it does not have.
- **Metering differs by provider.** For one video model, one provider may meter audio and
  silent output and 4K, while another sells only audio-on output at 720p/1080p. Record each
  provider's own matrix.
- **Placeholder prices.** OpenRouter can show `$0/MTok` for video models. That is not a
  usable price: leave the binding out.
- **Namespaces differ from vendor IDs.** For example, image IDs may use a short namespace
  (`bfl/…`) while the vendor field is `black-forest-labs`. Keep whatever the authored data
  uses; do not "fix" an ID to match a vendor name.
