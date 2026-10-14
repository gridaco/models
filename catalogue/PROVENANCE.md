# Catalogue research notes

Source-specific qualifications and references for the values in
[`models.json`](./models.json). The JSON holds the values; these notes explain
where they came from and any caveat a value cannot carry itself. Update a note
in the same change as the fact it qualifies.

Each `##` heading names the entry or declaration a note qualifies. The headings
are code fragments carried over from the TypeScript literals the catalogue was
first written as in [gridaco/grida](https://github.com/gridaco/grida), so they
keep that historical spelling (for example `imageInputMimes` rather than
`image_input_mimes`).

## `const OPENAI_IMAGE_INPUT_MIMES = [`

Provider-family capabilities are kept private so catalogue entries remain
explicit while sharing one source-backed value. Do not derive these from
`multimodal`; a future model may be multimodal without a documented image
input format set.
https://developers.openai.com/api/docs/guides/images-vision#image-input-requirements

## `const ANTHROPIC_IMAGE_INPUT_MIMES = [`

https://platform.claude.com/docs/en/build-with-claude/vision#supported-formats

## `const GOOGLE_IMAGE_INPUT_MIMES = [`

https://ai.google.dev/gemini-api/docs/image-understanding#supported-image-formats

## `const OPENAI_LONG_CONTEXT_PRICING = {`

OpenAI bills the full request at these multipliers once its total input
exceeds 272K tokens. The same rule is published for GPT-5.5, every
GPT-5.6 family member, and GPT-6 Astra.
https://developers.openai.com/api/docs/models/gpt-5.5
https://developers.openai.com/api/docs/models/gpt-5.6-sol
https://developers.openai.com/api/docs/models/gpt-6-astra

## `"openai/gpt-5.6-sol": {`

Base rates; OPENAI_LONG_CONTEXT_PRICING represents the request-wide
band that applies above 272K total input tokens.

Sol is cheaper than GPT-5.5, the card directly above it. It was
introduced carrying 5.5's rates verbatim; these are OpenAI's own.
https://developers.openai.com/api/docs/models/gpt-5.6-sol

## `"openai/gpt-6-astra": {`

OpenAI's September 3 introduction remained a limited rollout. The
September 4 date below is the exact Vercel AI Gateway route's broad availability,
which is the release fact relevant to this route card.
https://openai.com/products/release-notes/
https://vercel.com/ai-gateway/models/gpt-6-astra

## `"anthropic/claude-opus-5.5": {`

Anthropic API ID `claude-opus-5-5`; this is the Vercel AI Gateway ID, whose
model feed lists the same rates. Cache reads are 0.05x base input ($0.20);
`cache_write` is the 5-minute write ($5; the 1-hour write is $8). Released
2026-09-22 as generally available; only its fast mode is a research preview.
https://platform.claude.com/docs/en/models/opus-5-5/overview
https://platform.claude.com/docs/en/about-claude/pricing
https://vercel.com/ai-gateway/models/claude-opus-5.5

Claude Opus 5 stays catalogued. Opus 5.5 is cheaper, but it is not a drop-in
successor: thinking can't be disabled, forced tool use (`tool_choice`
`any`/`tool`) returns an error, and `computer_20251124` is not accepted on
the Claude API and Google Cloud. Opus 5 is still the choice for those.
https://platform.claude.com/docs/en/models/opus-5-5/whats-new-opus-5-5

## `"anthropic/claude-haiku-5.5": {`

Anthropic API ID `claude-haiku-5-5`; this is the Vercel AI Gateway ID. Priced
by prompt length: a request whose prompt is over 100,000 tokens, counting all
input tokens including cache reads and writes, pays $0.50 input, $2.50
output, $0.05 cache read and $0.625 5-minute cache write, 5x each base rate.
`long_context` records that band; its input multiplier also applies to cache
reads and writes. The gateway's model feed publishes the same tiers. The
1.1x US-only inference multiplier (`inference_geo`) also applies to the
higher band.
https://platform.claude.com/docs/en/models/haiku-5-5/overview
https://platform.claude.com/docs/en/about-claude/pricing
https://vercel.com/ai-gateway/models/claude-haiku-5.5

## `"anthropic/claude-sonnet-5.5": {`

Anthropic API ID `claude-sonnet-5-5`; this is the Vercel AI Gateway ID, whose
model feed lists the same rates. Same $2/$10 card as Claude Sonnet 5, with
cache reads at 0.05x base input ($0.10) instead of $0.20; `cache_write` is
the 5-minute write ($2.50; the 1-hour write is $4).
https://platform.claude.com/docs/en/models/sonnet-5-5/overview
https://platform.claude.com/docs/en/about-claude/pricing
https://vercel.com/ai-gateway/models/claude-sonnet-5.5

Claude Sonnet 5 stays catalogued. Sonnet 5.5 is not a drop-in successor:
forced tool use (`tool_choice` `any`/`tool`) returns a 400 error, thinking
can't be fully disabled (`between_tools` is its lowest setting), and
`computer_20251124` is not accepted on the Claude API and Google Cloud.
https://platform.claude.com/docs/en/models/sonnet-5-5/whats-new-sonnet-5-5

## `"anthropic/claude-sonnet-5": {`

$2/$10 per million input/output tokens is Anthropic's published regular rate.
Do not substitute an obsolete higher rate.
https://platform.claude.com/docs/en/about-claude/pricing

## `"anthropic/claude-fable-5.1": {`

Same input/output/cacheWrite card as Claude Fable 5, with cache reads
cut to $0.25/MTok. Not a drop-in successor — forced tool choice
(`tool_choice` `any`/`tool`) is rejected here — which is why Fable 5
stays catalogued rather than being removed.
https://platform.claude.com/docs/en/models/fable-5-1/overview

## `"anthropic/claude-fable-5": {`

Unlike Fable 5.1, this version accepts forced tool choice.

## `"anthropic/claude-opus-5": {`

Same $5/$25 rate card as Claude Opus 4.8, but not a drop-in successor, so
Opus 4.8 stays catalogued. On Opus 5, `thinking: {"type": "disabled"}` with
effort `xhigh` or `max` returns a 400 error, which Anthropic lists as a
breaking change from Opus 4.8; and Opus 5 thinks by default, where Opus 4.8
runs without thinking unless asked. (Corrects an earlier note that called
Opus 5 a drop-in successor.)
https://platform.claude.com/docs/en/release-notes/overview
https://platform.claude.com/docs/en/models/opus-5-5/migration-guide

## `"google/gemini-3.8-flash": {`

Google's cache model is read + hourly storage (no one-time write
premium that matches `cacheWrite` semantics), so the field is omitted.

The intrinsic cost records Google's published regular rates: $1.50 input,
$7.50 output, and $0.15 cached input per million tokens. Promotional rates
and their expiry dates are excluded. This evidence applies to Google's
rates; each serving provider's regular prices need its own evidence.
Gemini 3.8 Flash is GA, and this exact id is listed on both Vercel AI Gateway
and OpenRouter.
https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash
https://ai.google.dev/gemini-api/docs/pricing
https://vercel.com/ai-gateway/models/gemini-3.8-flash
https://openrouter.ai/google/gemini-3.8-flash

## `"google/gemini-3.7-flash": {`

3.8 improves accuracy and reliability at the same rate, but Google
still recommends 3.7 when compute efficiency matters because 3.8 can
consume more tokens.
https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/guides/gemini-3-8-flash

## `longContext: {`

Google bills the full request at $4 in / $18 out / $0.40
cacheRead above 200K tokens. `inputMultiplier` covers every
input bucket, so cacheRead 0.2 x 2 lands on $0.40 without a
separate field.
https://ai.google.dev/gemini-api/docs/pricing

## `const GPT_IMAGE_2_5_FAL_PRICING: PerTokenPricing = {`

Both 2.5 variants use this fal meter. Keep the separate text-output
rate: fal publishes it even though its result schema exposes only images.
https://fal.ai/models/openai/gpt-image-2.5/flare/text-to-image
https://fal.ai/models/openai/gpt-image-2.5/sunburst/text-to-image

## `const GPT_IMAGE_2_5_VERCEL_AI_GATEWAY_PRICING: PerTokenPricing = {`

Each serving provider publishes its own meter; do not copy fal's extra
image-cache/text-output rates into providers that do not advertise them.
https://ai-gateway.vercel.sh/v1/models (verified 2026-09-09 KST)

## `const GPT_IMAGE_2_5_OPENROUTER_PRICING: PerTokenPricing = {`

Both variants' /api/v1/images/models/{id}/endpoints publish this meter.
https://openrouter.ai/api/v1/images/models/openai/gpt-image-2.5-flare/endpoints
https://openrouter.ai/api/v1/images/models/openai/gpt-image-2.5-sunburst/endpoints

## `"openai/gpt-image-2": {`

---

OpenAI
-----------------------------------------------------------------

https://developers.openai.com/api/docs/models/gpt-image-2

## `transparent_background: true,`

Native transparency added 2026-08-20; provider exposure differs.
https://developers.openai.com/api/docs/changelog

## `providers: {`

ids/prices verified 2026-06-29, see github.com/gridaco/grida/issues/908

## `transparent_background: null,`

This provider's page does not establish background support.
https://vercel.com/ai-gateway/models/gpt-image-2 (2026-09-09)

## `transparent_background: false,`

Published background enum is auto | opaque (2026-09-09).
https://openrouter.ai/api/v1/images/models/openai/gpt-image-2/endpoints

## `references: { id: "openai/gpt-image-2", max: 16 },`

input_references advertised by OpenRouter (0–16), 2026-07-01.

## `},`

Inherits native transparency: fal-ai/gpt-image-2's published
background enum includes transparent (verified 2026-09-09).

## `"openai/gpt-image-2.5-flare": {`

Released as two distinct models. All three providers now list both
variants; fal separates generation and edit endpoint ids, while
OpenRouter advertises input_references on the same id (2026-09-09 KST).

## `transparent_background: true,`

Both fal generation and edit schemas expose background=transparent.
https://fal.ai/models/openai/gpt-image-2.5/flare/text-to-image/api
https://fal.ai/models/openai/gpt-image-2.5/flare/edit/api

## `url: "https://vercel.com/ai-gateway/models/gpt-image-2.5-flare",`

The model page exposes background=transparent; reference input
is not established by the Vercel AI Gateway feed (2026-09-09 KST).

## `transparent_background: false,`

Endpoint schema's background enum is auto | opaque.

## `constraints: {`

Model-specific fal documentation overrides its generic ImageSize
component's wider bounds. The API also accepts auto-sized output.
https://fal.ai/models/openai/gpt-image-2.5/flare/text-to-image/api

## `avg_cost_usd: 0.055,`

High 1024² output estimate is $0.05268, plus a small input allowance.
Not a fixed per-image price: actual cost depends on all billed tokens.
https://developers.openai.com/api/docs/guides/image-generation

## `transparent_background: true,`

Both fal generation and edit schemas expose background=transparent.
https://fal.ai/models/openai/gpt-image-2.5/sunburst/text-to-image/api
https://fal.ai/models/openai/gpt-image-2.5/sunburst/edit/api

## `url: "https://vercel.com/ai-gateway/models/gpt-image-2.5-sunburst",`

The model page exposes background=transparent; reference input
is not established by the Vercel AI Gateway feed (2026-09-09 KST).

## `transparent_background: false,`

Endpoint schema's background enum is auto | opaque.

## `constraints: {`

https://fal.ai/models/openai/gpt-image-2.5/sunburst/text-to-image/api

## `"openai/gpt-image-1.5": {`

https://developers.openai.com/api/docs/models/gpt-image-1.5

## `constraints: null,`

Preset-only — provider rejects arbitrary sizes.

## `pricing: {`

https://developers.openai.com/api/docs/models/gpt-image-1.5

## `"openai/gpt-image-1-mini": {`

https://developers.openai.com/api/docs/models/gpt-image-1-mini

## `constraints: null,`

Preset-only — provider rejects arbitrary sizes.

## `pricing: {`

https://developers.openai.com/api/docs/models/gpt-image-1-mini

## `"google/gemini-3.1-flash-image-preview": {`

---

Google (multimodal LLMs with native image output)
-----------------------------------------------------------------

python .tools/model_info.py --image gemini-3.1-flash-image
Vercel AI Gateway pricing: $0.50/MTok input, $3.00/MTok output

## `providers: {`

"Nano Banana 2"; ids/prices verified 2026-06-29, see issues/908

## `vercel: {`

Vercel AI Gateway serves the graduated `google/gemini-3.1-flash-image`
and the `-preview` alias at identical rates (feed, 2026-09-02).
Bindings call the graduated id; the canonical key above stays
`-preview` because it is persisted in selections and published
in the catalogue snapshot — renaming it is a separate change.

## `references: { id: "google/gemini-3.1-flash-image", max: 14 },`

input_references advertised by OpenRouter (0–14), 2026-07-01.

## `fal: {`

fal's graduated endpoint is `fal-ai/nano-banana-2`; same $0.08
per 1K image as the `-preview` endpoint (2K ×1.5, 4K ×2).

## `"google/gemini-3-pro-image": {`

python .tools/model_info.py --image gemini-3-pro-image
Vercel AI Gateway pricing: $2.00/MTok input, $12.00/MTok output

## `providers: {`

"Nano Banana Pro"; ids/prices verified 2026-06-29, see issues/908

## `references: { id: "google/gemini-3-pro-image-preview", max: 14 },`

input_references advertised by OpenRouter (0–14), 2026-07-01.

## `"google/gemini-3.1-flash-lite-image": {`

"Nano Banana 2 Lite" — GA 2026-06-30. The cost/speed tier of the 3.1
Flash family: ~half of Nano Banana 2's meter, and 1K-only output
(2K/4K unsupported — the differentiator). Vercel AI Gateway + OpenRouter both
meter it at $0.25/$1.50 (verified 2026-07-01); fal id not verified,
so left out. OpenRouter doesn't advertise input_references for the
Lite (t2i only per its model page), so no `references` (TOOL-DESIGN:
no unverified capability).

## `avg_cost_usd: 0.034,`

Published 1K per-image cost (the card default): $0.034 = 1120 tokens
× $30/1M image-output (Google/Vercel AI Gateway changelog, 2026-07-01). The
budget meter charges this per image, so it must be the real cost.

## `"bfl/flux-2-pro": {`

---

Black Forest Labs (via Vercel AI Gateway)
-----------------------------------------------------------------

https://vercel.com/docs/ai-gateway/capabilities/image-generation/ai-sdk
https://docs.bfl.ml/pricing

## `providers: {`

All three providers meter $0.03 per megapixel (Vercel AI Gateway model page,
OpenRouter endpoint `cost_usd`/megapixel, fal "first megapixel");
represented as flat at the 1MP baseline. The Vercel AI Gateway binding shipped
at $0.06 — a 2x hosted over-billing — corrected 2026-09-02. The
Vercel AI Gateway feed carries no `pricing` for BFL cards, so the page is the
source.

## `references: { id: "black-forest-labs/flux.2-pro", max: 8 },`

input_references advertised by OpenRouter (0–8), 2026-07-01.

## `"bfl/flux-2-max": {`

---

Black Forest Labs — Flux 2 Max
-----------------------------------------------------------------

BFL's top Flux 2 line (2025-12-16). $0.07 per megapixel on all three
(Vercel AI Gateway model page — the feed carries no BFL pricing; OpenRouter
`cost_usd`/megapixel; fal "first megapixel", +$0.03 each additional).
Represented as flat at the 1MP baseline. Verified 2026-09-02.

## `references: { id: "black-forest-labs/flux.2-max", max: 8 },`

OpenRouter `supported_parameters.input_references` 0–8
(2026-09-02). As on Flux 2 Pro.

## `constraints: null,`

The inherited Flux 2 Pro edge envelope was unverified for Max and is withdrawn.
See the 2026-10-13 media qualifications below for the independently sourced
fal endpoint bounds.

## `providers: {`

$0.04 on both providers: Vercel AI Gateway feed `pricing.image` + fal's model
page ("Fixed $0.04 cost per image edit"), verified 2026-09-02.

## `"bytedance/seedream-5.0-pro": {`

---

ByteDance — Seedream 5.0 Pro
-----------------------------------------------------------------

Vercel AI Gateway feed `pricing.image` $0.035 (the model page's rate table shows
$0.04 while its copy says $0.035 — the feed is the billing contract);
OpenRouter `cost_usd` $0.045 at 1K ($0.09 high-res, +$0.003 per
input image, not modelled); fal $0.0675 for ≤1536² area, $0.135 up
to 2048². Represented at the 1024² baseline. Verified 2026-09-02.

## `references: { id: "bytedance-seed/seedream-5-0-pro", max: 14 },`

OpenRouter `supported_parameters.input_references` 0–14
(2026-09-02). Same endpoint as t2i, as on 4.5.

## `constraints: {`

fal: total pixels between 1024x1024 and 2048x2048, aspect ratio
between 1:16 and 16:1 — an area bound, not a per-edge one, so a
512x2048 request is in-envelope and a 2048x2048 one is the ceiling.

## `"bytedance/seedream-5.0-lite": {`

---

ByteDance — Seedream 5.0 Lite
-----------------------------------------------------------------

Universal: $0.035/img on all three (Vercel AI Gateway feed `pricing.image`,
OpenRouter `cost_usd`, fal page payload), verified 2026-09-02. A
2K–4K model: fal scales requests below 2560x1440 up to its floor.

## `references: { id: "bytedance-seed/seedream-5-0-lite", max: 14 },`

OpenRouter `supported_parameters.input_references` 0–14
(2026-09-02).

## `constraints: { min_pixels: 3_686_400, max_pixels: 16_777_216 },`

fal: total pixels between 2560x1440 and 4096x4096 (requests below
the floor are scaled up to it); Vercel AI Gateway and OpenRouter serve 2K/4K
only. An area envelope, so the default is a 2K request.

## `"bytedance/seedream-4.5": {`

---

ByteDance — Seedream 4.5
-----------------------------------------------------------------

$0.04/img on all three providers (re-verified 2026-09-02).

## `references: { id: "bytedance-seed/seedream-4.5", max: 14 },`

i2i verified live 2026-07-01 (OpenRouter /api/v1/images
input_references; same endpoint as t2i). max from
supported_parameters.input_references.

## `"xai/grok-imagine-image-2.0": {`

---

SpaceXAI — Grok Imagine Image 2.0
-----------------------------------------------------------------

Tiered by quality (low/medium) × resolution (1K/2K); the same four
rates on all three providers (Vercel AI Gateway feed
`image_dimension_quality_pricing`, OpenRouter `cost_usd` variants,
fal page). OpenRouter also bills $0.01 per input image (not
modelled). Verified 2026-09-02.

## `references: { id: "x-ai/grok-imagine-image-2.0", max: 3 },`

OpenRouter `supported_parameters.input_references` 0–3
(2026-09-02). OR bills $0.01 per input image on top (not modelled).

## `"meta/muse-image-1.0": {`

---

Meta — Muse Image 1.0
-----------------------------------------------------------------

Meta's agentic image model (2026-08-26): $0.01/img on Vercel AI Gateway (feed
`pricing.image`) and fal (page payload). OpenRouter lists it but
exposes no serving endpoint.
fal exposes aspect ratio only (no size control). Verified 2026-09-02.

## `constraints: null,`

Muse picks output dimensions from the aspect ratio; neither
provider exposes a size envelope, so none is claimed.

## `"recraft/recraft-v4.1": {`

---

Recraft — V4.1
-----------------------------------------------------------------

Universal: $0.035/img raster on every provider (Vercel AI Gateway feed
`pricing.image`, OpenRouter endpoint `cost_usd`, fal page payload),
verified 2026-09-02. Vector styles are $0.08 and a separate route on
fal/OpenRouter (`.../text-to-vector`, `recraft-v4.1-vector`) — not
catalogued; `styles: null` here means the raster route only.
OpenRouter org slug is `recraft`, not `recraft-ai`.

## `references: { id: "recraft/recraft-v4.1", max: 1 },`

OpenRouter `supported_parameters.input_references` 0–1
(2026-09-02).

## `"recraft/recraft-v3": {`

---

Recraft — V3
-----------------------------------------------------------------

$0.04/img raster on every provider (re-verified 2026-09-02; Recraft's
own pricing table agrees).

## `pricing: { type: "per_run_flat", usd: 0.04 },`

Source: replicate.com/google/lyria-3 — "$0.04 per output audio file"

## `pricing: { type: "per_run_flat", usd: 0.08 },`

Source: replicate.com/google/lyria-3-pro — "$0.08 per output audio file"

## `pricing: {`

API: 100 credits when duration is automatic, or 11 credits/s when set.

## `pricing: { type: "per_1000_characters", usd: 0.1 },`

Source: elevenlabs.io/pricing/api — $0.10 per 1,000 characters.

## `"tripo/rig-v2.5": {`

Follow the documented compatibility table, not its contradictory biped example.

## `"google/veo-3.1": {`

---

Google — Veo 3.1
-----------------------------------------------------------------

## `vercel: {`

Vercel AI Gateway — vercelAiGateway.videoModel(id), image-to-video. The
Vercel AI Gateway meters both audio modes and sells 4K; the matrix is
identical to fal's. Verified against Vercel AI Gateway's own
/v1/models feed (`video_duration_pricing`) on 2026-09-02 — the
previous card claimed "audio-on only, ≤1080p", which the feed
contradicts.

`silent` is catalogued as provider truth but is not yet
reachable on Grida's hosted route: the video wire carries no
audio-mode field, so `generateVideo` prices the card's default
mode ([`editor/lib/ai/server.ts`](https://github.com/gridaco/grida/blob/main/editor/lib/ai/server.ts) in gridaco/grida). `"4k"` IS reachable — the
request path maps a 2160 short edge to that label and today
rejects it for want of a rate.
https://vercel.com/ai-gateway/models/veo-3.1-generate-001

## `fal: {`

fal.ai — image-to-video endpoint `fal-ai/veo3.1/image-to-video`; the
separate text-to-video endpoint `fal-ai/veo3.1` is also catalogued. Rate
matrix is identical to the Vercel AI Gateway's: $0.40/s audio and
$0.20/s silent at 720p/1080p, $0.60/$0.40 at 4K.
https://fal.ai/models/fal-ai/veo3.1/image-to-video

## `openrouter: {`

OpenRouter — async `/api/v1/videos` (job → poll → unsigned url).
Text-to-video + image-to-video; native audio. "from $0.40/s"
(verified 2026-06-29, https://openrouter.ai/google/veo-3.1).

## `"google/veo-3.1-fast": {`

---

Google — Veo 3.1 Fast
-----------------------------------------------------------------

Same envelope as Veo 3.1 (16:9/9:16, 4/6/8s, native audio, ≤4K) at
~2.7x lower cost. Rate matrix is identical on Vercel AI Gateway and fal —
Vercel AI Gateway feed `video_duration_pricing` and fal's stated per-second
rates, verified 2026-09-02.

## `"google/veo-3.1-lite": {`

---

Google — Veo 3.1 Lite
-----------------------------------------------------------------

The budget Veo: 720p/1080p only, 4/6/8s, native audio. Rates
identical on Vercel AI Gateway and fal (verified 2026-09-02). Vercel AI Gateway
supports both text and image input (FAQ verified 2026-09-07); the fal binding
requires an image.

## `"alibaba/wan-3.0": {`

---

Alibaba — Wan 3.0
-----------------------------------------------------------------

Per-second by resolution, audio bundled into the rate (Vercel AI Gateway
feed has no audio axis; fal exposes an `audio` toggle but bills the
same). Identical on Vercel AI Gateway and fal, verified 2026-09-02. 2–30s.

## `"bytedance/seedance-2.0": {`

ByteDance — Seedance 2.0
-----------------------------------------------------------------

## `providers: {`

NO Vercel AI Gateway binding, deliberately. Vercel AI Gateway serves
`bytedance/seedance-2.0` but meters it PER TOKEN
(`video_token_pricing`: $7.00/MTok at 480p/720p, $7.70 at 1080p,
$4.00 at 4K; reduced with video input; "minimum token floors based
on output duration"). `PerSecondPricing` cannot express that, the
hosted route pre-prices rate×duration, and ByteDance publishes no
tokens-per-second figure — so there is no honest per-second rate,
and the per-second Vercel AI Gateway binding this card shipped with was
invented. Withheld until the hosted path can meter post-flight;
hosted requests fail with "not available on the hosted provider".
See gridaco/grida#1019 (Blocker A). Feed checked 2026-09-02.

## `fal: {`

fal — image-to-video. fal also meters tokens underneath
($0.014/1K), but states a per-second price for the two
resolutions it prices: $0.3034/s @720p, $0.682/s @1080p, audio
bundled. Those are fal's own figures, not a conversion of ours.
https://fal.ai/models/bytedance/seedance-2.0/image-to-video

## `openrouter: {`

OpenRouter — async `/api/v1/videos`. Flat $0.06726/s (verified
2026-06-29, https://openrouter.ai/bytedance/seedance-2.0) — far
below Vercel AI Gateway's per-resolution rate (the proprietary-pricing-
diverges finding, #908). No separate silent meter surfaced.

## `"bytedance/seedance-2.5": {`

---

ByteDance — Seedance 2.5
-----------------------------------------------------------------

Newer generation (2026-07-31), NOT a drop-in successor: ~55% more
per token on Vercel AI Gateway ($10.70/MTok at 480p/720p, $11.70 at 1080p
vs 2.0's $7.00/$7.70), ~56–71% more per second on fal, and no 4K.
It buys 4–30s clips, video-editing and extend-video. 2.0 is cheaper
and serves 4K. Vercel AI Gateway bills tokens, so there is no comparable
per-second Vercel AI Gateway meter here. fal states per-second prices, audio bundled.

## `fal: {`

fal's stated rates: $0.2205/s @480p, $0.4730/s @720p, $1.164/s
@1080p (fal meters $0.0214/1K tokens underneath). 2026-09-02.
https://fal.ai/models/bytedance/seedance-2.5/image-to-video

## `"xai/grok-imagine-video-1.5": {`

---

SpaceXAI — Grok Imagine Video 1.5
-----------------------------------------------------------------

Image-to-video only (no t2v, per SpaceXAI docs); native lip-synced audio
bundled into the rate. Per-second by resolution, identical on Vercel AI Gateway
(no markup) and fal: $0.08/s @480p, $0.14/s @720p, $0.25/s @1080p.
Both also bill $0.01 per input image, captured separately from the
output meter.

## `vercel: {`

Vercel AI Gateway — image-to-video; mirrors SpaceXAI's list price (no markup).
Vercel AI Gateway namespaces every SpaceXAI model under `spacexai/`, so the
call id deliberately differs from this card's canonical `xai/` id.
https://vercel.com/changelog/grok-imagine-video-1-5-on-ai-gateway

## `fal: {`

fal.ai — image-to-video endpoint; same per-second rate.
https://fal.ai/models/xai/grok-imagine-video/v1.5/image-to-video

## `pricing: { type: "per_token_input", input: 0.15 },`

VERIFY before prod: models.dev lists no per-1M price for
gemini-embedding-2 yet; using the gemini-embedding-001 family
input rate ($0.15 / 1M) as a conservative stand-in.

## Text labs and Vercel endpoints (2026-10-13)

Text cards identify the lab named by their existing first-party release source:
OpenAI, Anthropic, or Google. Their exact serving IDs are verified against
[Vercel's public model discovery](https://ai-gateway.vercel.sh/v1/models),
which lists all 17 recorded text models. These identifiers record availability,
not a routing preference. Existing model release dates are unchanged. Standard
serving prices, bands and limits are qualified separately below.

## fal input variants (2026-10-13)

Bindings list the text and image variants documented on their exact fal API
pages. Each endpoint includes its own source URL; existing `references` fields
remain unchanged. GPT Image 2's ID is corrected to `openai/gpt-image-2` from
[fal's API example](https://fal.ai/models/openai/gpt-image-2/api); the overview's
hand-written quick start still shows `fal-ai/gpt-image-2`, which disagrees with
the generated API documentation. The generated endpoint-specific API example
is the more specific source. This correction does not change prices.

## Tripo rig check

[Tripo's rig-check documentation](https://developers.tripo3d.ai/en/docs/animations-rig-check)
identifies the operation and lab but does not establish its first public release
day. It carries `basis: provider_endpoint` and `date: null`, as do the rigging
endpoints; a consumer must not substitute its own integration date.

## Media endpoint parameters and limits (2026-10-13)

The recorded fal image, video and 3D variants now include native parameter facts
from their endpoint-specific API pages and public OpenAPI documents. Each
endpoint's `source_url` identifies that variant; a parameter with a different
source carries its own `source_url`. Names such as `image_size.width` denote
native nested fields. An `image_size` preset enum is the published string-option
list, not a complete validator for its string-or-object input.

Model-specific `x-fal` size metadata takes precedence over generic `ImageSize`
component bounds. The generic component alone does not establish a model's
intrinsic envelope. Area and aspect bounds are recorded only where the exact
endpoint publishes them. In particular:

- [Seedream 5.0 Lite's input schema](https://fal.ai/models/bytedance/seedream/v5/lite/text-to-image/api)
  explicitly states a 2560×1440 to 4096×4096 total-area range. Its below-floor
  scaling behavior is separate from that supported output range.
- Seedream edit's ten references and Grok Image edit's five references come from
  their exact endpoint schema descriptions, which are more specific than the
  missing JSON `maxItems` keywords. Nano Banana 2 and Pro's fourteen-reference
  limits come from their respective [Nano Banana 2 edit overview](https://fal.ai/models/fal-ai/nano-banana-2/edit)
  and [Nano Banana Pro edit overview](https://fal.ai/models/fal-ai/nano-banana-pro/edit).
- [Flux Pro's edit overview](https://fal.ai/models/fal-ai/flux-2-pro/edit) publishes
  nine references and 9MP total input. Flux Max's corresponding reference count
  is unspecified. Neither edit schema publishes the generation variant's
  `x-fal` dimension extension, so those generation bounds are not copied to edit.
- Flux and Recraft do not publish a `num_images` parameter in these endpoint
  schemas. Unpublished seed bounds and reference counts remain absent. A missing
  fact does not establish unlimited input or an intrinsic model limit.

### Intrinsic envelope corrections

[BytePlus's Seedance 2.0 documentation](https://docs.byteplus.com/en/docs/modelark/seedance-2-0)
and its [video-generation tutorial](https://docs.byteplus.com/id/docs/modelark/video-generation-tutorial)
establish the 4–15-second duration range and six aspect ratios: 21:9, 16:9, 4:3,
1:1, 3:4 and 9:16. The old five-second minimum and incomplete ratio list are
corrected. The exact fal text and image variants independently agree.

Gemini 3 Pro Image's inherited 1536-pixel edge limit is withdrawn. Its
[fal generation schema](https://fal.ai/models/fal-ai/nano-banana-pro/api) and
[edit schema](https://fal.ai/models/fal-ai/nano-banana-pro/edit/api) document
1K/2K/4K resolution choices. Those tier labels do not establish a universal
per-edge maximum: dimensions also depend on aspect ratio. No replacement
intrinsic envelope is inferred from another model's output-size table.

Flux Max's copied Pro edge envelope is also withdrawn. The
[lab overview](https://docs.bfl.ml/flux_2/flux2_overview) says up to 4MP without
establishing an exact pixel conversion. The
[fal generation schema](https://fal.ai/models/fal-ai/flux-2-max/api) independently
publishes 256–2560 per edge, steps of 16, and 4,194,304 total pixels. These are
provider-endpoint facts, not a conversion of the lab's 4MP statement.

### Variable fal image prices

The existing baseline `usd`, `type` and average-cost fields are unchanged.
Additive fields describe the published variable portions of those schedules:

- [Flux Pro](https://fal.ai/models/fal-ai/flux-2-pro/edit) bills $0.03 for the first
  output megapixel and $0.015 per additional input/output megapixel, rounded up.
  Its examples price 1024×1024 at $0.03 and 1920×1080 at $0.045. The first-unit
  scope is `output`; no precise universal pixels-per-megapixel conversion is
  inferred from those examples.
- [Flux Max](https://fal.ai/models/fal-ai/flux-2-max/edit) bills $0.07 for the first
  processed megapixel and $0.03 for each additional megapixel, including inputs.
  Its first-unit scope is `processed`. No rounding rule is copied from Pro.
- [Nano Banana 2](https://fal.ai/models/fal-ai/nano-banana-2) retains $0.08 per image.
  Published multipliers are 0.75× for 0.5K, 1.5× for 2K and 2× for 4K. Web search
  adds $0.015 and high thinking adds $0.002 when used. The
  [edit page](https://fal.ai/models/fal-ai/nano-banana-2/edit) states the same terms.
- [Nano Banana Pro](https://fal.ai/models/fal-ai/nano-banana-pro) retains $0.15 per
  image; 4K costs 2× and web search adds $0.015 when used. Its
  [edit page](https://fal.ai/models/fal-ai/nano-banana-pro/edit) agrees. No additional
  thinking fee or special 2K multiplier is inferred.

### Native 3D operation facts

Tripo generation, rigging and rig-check variants carry their own native API paths,
version enums and parameter facts. The sources are Tripo's separate
[P text-generation](https://developers.tripo3d.ai/en/docs/generation-text-to-model/p),
[P image-generation](https://developers.tripo3d.ai/en/docs/generation-image-to-model/p),
[P multiview](https://developers.tripo3d.ai/en/docs/generation-multiview-to-model/p),
[standard text-generation](https://developers.tripo3d.ai/en/docs/generation-text-to-model/standard),
[standard image-generation](https://developers.tripo3d.ai/en/docs/generation-image-to-model/standard),
[standard multiview](https://developers.tripo3d.ai/en/docs/generation-multiview-to-model/standard),
[rigging](https://developers.tripo3d.ai/en/docs/animations-rig) and
[rig-check](https://developers.tripo3d.ai/en/docs/animations-rig-check) pages.
Multiview is image input; its native path distinguishes the operation. Its
task-ID, four-slot legacy and named-view input forms do not justify one universal
array cardinality. H3.1's 2,000,000-face detailed bound does not replace its
1,500,000-face standard bound. No new seed limits or undocumented output-format
parameter are invented. The `fast` texture option requires the documented
`v3.5-20260815` texture version.

The fal [Hunyuan image](https://fal.ai/models/fal-ai/hunyuan-3d/v3.1/pro/image-to-3d/api),
[Hunyuan text](https://fal.ai/models/fal-ai/hunyuan-3d/v3.1/pro/text-to-3d/api) and
[TRELLIS.2](https://fal.ai/models/fal-ai/trellis-2/api) endpoints likewise record
their native input types, enums and bounds. Hunyuan's image-dimension prose
describes the reference input; it is not an output-image envelope. TRELLIS.2's
resolution, mesh, texture, sampling, guidance and UV parameters retain their
published units and bounds. These partial parameter maps do not claim to replace
the providers' complete request schemas or cross-field validation rules.

## Published image output calculators and examples (2026-10-13)

The GPT Image 2 and GPT Image 2.5 cards record the calculator in
[OpenAI's image generation guide](https://developers.openai.com/api/docs/guides/image-generation),
including its [published JavaScript](https://developers.openai.com/_astro/GptImageTokenCalculator.react.DukR73TZ.js).
That source supplies the quality coefficients, area constants, ties-to-even
short-axis rounding and final upward token rounding. The examples are estimates
from that calculator, not measured usage or guaranteed whole-request prices.
They exclude text/image inputs, reasoning and partial-image output charges.
Exact output-token examples were verified with the calculator rather than inferred
by dividing a rounded USD price by the token rate.

The GPT Image 2.5 cards also retain all six published size rows from fal's
[Flare](https://fal.ai/models/openai/gpt-image-2.5/flare/text-to-image) and
[Sunburst](https://fal.ai/models/openai/gpt-image-2.5/sunburst/text-to-image)
price tables. Their `1920x1080` row conflicts with the documented requirement that
both dimensions be divisible by 16: 1080 is not. That quoted USD example remains
source-backed, but has no `output_tokens` value. OpenAI's calculator UI rejects
that size; calling only its unvalidated arithmetic function is not evidence of
an admissible request. Example dimensions must therefore be checked against the
model and endpoint constraints before use.

[fal's GPT Image 2 page](https://fal.ai/models/openai/gpt-image-2) bills text and
image tokens, so its binding now records token rates instead of treating the
rounded per-image examples as a fixed tariff. All three fal GPT Image bindings
publish the same six native token rates and say total cost rounds upward to
`$0.0001`, recorded as `rounding_usd`. A rounded example is not an exact total
request maximum. OpenAI's separately published cached-input rates apply to its
Responses image-generation tool, not direct Images API requests; recording a
provider's cache price does not promise a cache hit or cached billing on every API.

The six fal image endpoints' option bounds come from their endpoint-specific
public OpenAPI schemas. Image 2 allows at most four outputs; Image 2.5 allows ten.
Prompt bounds are character counts, not bytes or tokens. The shared generic
`ImageSize` definition permits larger dimensions, but the model-specific size
description and OpenAI guide impose the stricter 3840px edge, pixel-area,
16px-step and aspect constraints recorded on the endpoints. No undocumented
minimum number of reference images is inferred from an array being required.

## Vision tokenization parameters (2026-10-13)

[OpenAI's vision guide](https://developers.openai.com/api/docs/guides/images-vision)
explicitly lists GPT-5.5, GPT-5.6 Sol/Terra/Luna and GPT-6 Astra as 32px patch
models with a 1.2 token multiplier. It also supplies detail-specific resizing
limits and the separate 30,000-patch rejection threshold. Low detail fits within
512px on each side; a 256-patch allowance can be derived from that square, but is
not recorded as an independently published patch budget. The guide does not
qualify GPT-5.5 Pro's patch formula, so that card has no invented formula.

[Claude's vision guide](https://platform.claude.com/docs/en/build-with-claude/vision)
identifies 28px visual-token patches, a 2576px long edge and a 4784 visual-token
ceiling for Claude 4.7 and later. These are processing limits: oversized native
images may be downscaled before tokenization.

[Google's media-resolution guide](https://ai.google.dev/gemini-api/docs/media-resolution)
labels the Gemini 3 family token counts approximate. The cards preserve that
qualification and each resolution's published budget, including the 2240-token
`ultra_high` budget. That maximum is not a fixed billable count for every image.
These parameters describe provider tokenization. Preflight estimates do not
establish final charges.

## Text provider references and regular pricing (2026-10-13)

All 17 text cards retain independent native, Vercel and OpenRouter bindings.
The native model pages establish exact IDs and synchronous limits. Claude's
[pricing table](https://platform.claude.com/docs/en/about-claude/pricing) separates
five-minute and one-hour cache writes. Google's
[Standard pricing](https://ai.google.dev/gemini-api/docs/pricing) excludes optional
cache storage, grounding and alternate service tiers. Native and intermediary
limits and input-length bands intentionally remain distinct; a native reference
is a presentation choice, not a routing preference.

[Vercel's model feed](https://ai-gateway.vercel.sh/v1/models) supplies serving
limits and supported capabilities. Prices were checked against each model's
public page for regular-rate qualification. The
[Gemini 3.7 Flash](https://vercel.com/ai-gateway/models/gemini-3.7-flash) and
[Gemini 3.8 Flash](https://vercel.com/ai-gateway/models/gemini-3.8-flash) pages
publish explicit list tiers of $1.50 input, $7.50 output and $0.15 cached input
per million tokens. These replace discounted feed values; they are not inferred
by reversing a percentage. OpenRouter's corresponding model pages independently
publish the same list rates. Standard/global pricing excludes regional premiums,
optional tools and alternate service tiers.

[OpenRouter's model feed](https://openrouter.ai/api/v1/models) supplies its exact
IDs, modalities, limits and capabilities. Each model page qualifies the rates;
provider input-length boundaries are preserved exactly. The
[GPT-5.6 Sol endpoint listing](https://openrouter.ai/api/v1/models/openai/gpt-5.6-sol/endpoints)
independently establishes the recorded Standard rates and tiers. Time-based
cache-storage rates are not per-token cache-write prices.

The native [GPT-5.6 Sol page](https://developers.openai.com/api/docs/models/gpt-5.6-sol)
and [OpenAI pricing](https://developers.openai.com/api/docs/pricing) qualify the
visible native rate as promotional without publishing a regular replacement.
That binding therefore omits pricing; unknown does not mean free. Its Vercel and
OpenRouter prices remain independently sourced. No discount schedule is tracked.
GPT-5.5 Pro has no invented native cache discount or unverified native
long-context price; intermediary bands remain separate provider facts.

## TRELLIS.2 distribution (2026-10-13)

Microsoft's [official repository](https://github.com/microsoft/TRELLIS.2) links
the [TRELLIS.2-4B weights](https://huggingface.co/microsoft/TRELLIS.2-4B).
The [code license](https://github.com/microsoft/TRELLIS.2/blob/main/LICENSE)
and the weight model card both identify MIT; these are recorded separately.
The Hugging Face model metadata reports `gated: false`, so the published weight
access is recorded as public. Dependency licenses remain separate from these
artifact licenses. Distribution links do not establish a hosted inference API,
free inference or permission for every possible use.

## Provider coverage and non-text differences (2026-10-13)

All existing cards are retained. Provider coverage was checked against
[OpenRouter discovery](https://openrouter.ai/api/v1/models) and its image, video
and embedding feeds, [Vercel discovery](https://ai-gateway.vercel.sh/v1/models),
and fal's endpoint catalogue. Exact aliases matter: OpenRouter's Muse and Lyria
preview IDs differ from canonical card IDs. `not_listed` records absence from
those inspected public listings, not a promise that a provider will never offer
an equivalent endpoint. fal coverage is restricted to media.

Native references now identify actual lab APIs, including BytePlus for ByteDance,
Google Developer API, Meta, BFL, Recraft, xAI and Alibaba. Open weights do not
invent a lab-hosted API. Native and reseller prices retain their own meters:

- OpenRouter GPT Image 2 uses separate text-input, image-input and image-output
  token meters. Its 2.5 endpoints now list transparency; its Image 2 endpoint
  lists only `auto` and `opaque`.
- Seedance video-token SKUs replace an inaccurate OpenRouter per-second estimate.
  Input-video, resolution and audio variants remain distinct. BytePlus's current
  [pricing page](https://docs.byteplus.com/en/docs/ModelArk/model-pricing)
  publishes Seedream Pro's 2.61-million-pixel threshold; older indexed material
  differs. The dated native model ID is retained.
- Google's [regular embedding prices](https://ai.google.dev/gemini-api/docs/pricing)
  distinguish text, image, audio and video inputs. A provider that only publishes
  some meters does not inherit the others by assumption.
- [BFL pricing](https://bfl.ai/pricing) distinguishes first versus additional/input
  megapixels, ceiling rounding, pixel units and capped input sizes. Its flat
  FLUX 1.1 image price is not fal's megapixel price. Native xAI input-image charges
  and Alibaba's documented International-region regular rates remain qualified.

fal Tripo P2, native Tencent Hunyuan and native Bria retain verified endpoints
without an invented regular USD price. Bria's hosted checkpoint is not pinned by
its API reference. OpenRouter Muse's image-specific endpoint metadata is empty;
its general endpoint token meters do not establish image parameter parity.
These gaps are explicit qualifications, not zero-price defaults or passed paid
behavior tests. Real-ESRGAN's official code link is distribution metadata, not
an invented native hosted provider.

## Grida public service bindings (2026-10-13)

Grida bindings cover its existing 40 models and the rig-check operation; the
other 21 retained model cards do not claim Grida availability. Public
[model discovery](https://gateway.grida.ai/v1/models),
[endpoint discovery](https://gateway.grida.ai/v1/endpoints), and
[operation schemas](https://gateway.grida.ai/schemas/operations.json) establish
service identities and contracts. Discovery requires authentication. Synchronous
image, asynchronous video and specialized operation interfaces stay explicit;
these bindings do not imply another provider's parameter compatibility.

`published_pricing` records advertised USD per named quantity, including bands,
conditions and rounding. Provider-specific normalized quantities are not raw
image counts or guaranteed per-request totals. Source unit identifiers are
preserved. Grida's Gemini 3.7/3.8 Flash bindings omit prices: the inspected
discovery does not independently establish a regular, non-promotional schedule.
Another provider's regular rates are not evidence of Grida's advertised rates.
Other recorded service rates match the inspected discovery.
This catalogue describes public service facts without supplier selection or
private financial policy.

## GPT-6 Sol, Luna and GPT-6.1 Sol (2026-10-13)

OpenAI's [Sol and Luna announcement](https://openai.com/index/introducing-gpt-6-sol-and-luna/)
and [DevDay announcement](https://openai.com/index/devday-2026-recap/) establish
their September 22 and September 29 releases. The native model pages for
[Sol](https://developers.openai.com/api/docs/models/gpt-6-sol),
[Luna](https://developers.openai.com/api/docs/models/gpt-6-luna) and
[6.1 Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol) establish
standard regular prices, cache meters and reasoning/API differences. The new
prices are regular rates, not the preceding generation's promotion.

All three support tools in Responses. Native Chat Completions supports tools
only with explicit `none` reasoning for Sol and Luna, and does not support tools
for 6.1 Sol. A model-level `tools: true` is therefore not a promise about every
API interface. Native endpoint records describe Responses; qualifications retain
the Chat Completions restrictions.

[Vercel discovery](https://ai-gateway.vercel.sh/v1/models) preserves the native
long-context boundary of 272001 input tokens, while
[OpenRouter discovery](https://openrouter.ai/api/v1/models) reports its override
at 272000. Provider bindings preserve that difference. Cache writes and reads
are separate meters; 6.1 Sol's cached-input rate is half Sol's.

OpenAI's [vision guide](https://developers.openai.com/api/docs/guides/images-vision)
confirms image formats but does not name these three models in its multiplier
and detail-sizing tables. Their image-input capability is recorded, but no
image-tokenization formula is copied from Astra or GPT-5.6.

## Gemini Nano Banana 2.1 (2026-10-13)

The [native model specification](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/nano-banana-2-1)
records October 6 availability, 14 reference images, 1K/2K/4K outputs and the
image-token table. Unlike Nano Banana 2, 512px output is not offered.
[Google pricing](https://ai.google.dev/gemini-api/docs/pricing) separates input,
text/thinking output, image output and search grounding.

[fal's editing page](https://fal.ai/models/google/nano-banana-2.1/edit) publishes
token rates for both generation and editing. Its small-prompt image examples are
not flat charges: prompt and input tokens repeat for each generated image,
thinking adds text-output tokens, and search results add input tokens. The
[generation schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=google/nano-banana-2.1)
and [editing schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=google/nano-banana-2.1/edit)
retain exact controls. fal lists `seed`, while native Google Cloud declares it
unsupported; no deterministic behavior or parameter portability is inferred.

[Vercel discovery](https://ai-gateway.vercel.sh/v1/models) lists resolution-based
output-image price examples and text-token rates. No image-token rate is inferred
from Google's price. [OpenRouter discovery](https://openrouter.ai/api/v1/models)
publishes separate image-output token pricing and different context/output
limits, which remain provider-specific. None of the four new cards claims Grida
availability before the public service offers them. No paid inference was used
to establish these facts.

## Grida provider discovery — 2026-10-14

Authenticated [Grida model discovery](https://gateway.grida.ai/v1/models),
[operation schemas](https://gateway.grida.ai/schemas/operations.json) and the
[public API reference](https://gateway.grida.ai/llms.txt) were checked together.
They confirm Grida bindings for GPT-6 Sol, GPT-6 Luna, GPT-6.1 Sol and Gemini Nano
Banana 2.1. The three text bindings are text-only on Grida; native image-input
capabilities remain recorded separately. Nano Banana 2.1 exposes generation and
reference editing through distinct schema-linked operations.

Grida discovery also publishes separate cache-write price components for
GPT-5.6 Sol/Terra/Luna and GPT-6 Astra, and regular token schedules for Gemini
3.7 Flash and 3.8 Flash. These replace the earlier Grida price qualifications.
All prices here are the advertised USD schedule, with exact billing meters and
input-length bands; no inference cost is reconstructed from an example output.
This verifies public discovery and contract metadata, not exhaustive inference
behavior. Other providers' records, model release dates and intrinsic facts are
unchanged.

## GPT-6 Luna Decisions

`openai/gpt-6-luna-decisions` is a decision offering, separate from
`openai/gpt-6-luna` text generation. OpenAI's
[changelog](https://developers.openai.com/api/docs/changelog) dates the public beta
of `gpt-6-luna` through `/v1/decisions` to 2026-10-06; this is a
`provider_endpoint` release, not a second underlying model launch.

The [native guide](https://developers.openai.com/api/docs/guides/decisions)
establishes predicate/choice/score semantics and input-only pricing at $0.10/M.
It explicitly excludes cache-read, cache-write and output charges while retaining
regional premiums and long-context input multipliers. The linked
[Standard pricing table](https://developers.openai.com/api/docs/pricing) gives
GPT-6 Luna's doubled input rate above 272000 tokens. No chat cache/output rates,
tools, generation limits or reasoning parameters are copied into the decision
card. Probability estimates are not application-specific calibration guarantees;
thresholds require the consumer's own labeled examples.

The native image documents conflict: the
[API reference](https://developers.openai.com/api/reference/resources/decisions/methods/create)
accepts both inline and hosted HTTP(S) images, while the guide accepts only inline
images. Both agree on inline images, user-message input and no file IDs. The
binding leaves `image_input_forms` unrecorded and retains this qualification
instead of claiming a resolved complete transport contract. The exact reference
establishes typed boolean/string choices and 2–255 choices; score-level limits
are omitted where the native reference does not establish them.

[Vercel's compatible endpoint](https://vercel.com/docs/ai-gateway/sdks-and-apis/openai-decisions)
requires inline images, accepts 1–255 choices and 2–10 score levels, and rejects
boolean/string spelling collisions. Refused questions retain their positions and
are normally input-billed. Its public
[endpoint discovery](https://ai-gateway.vercel.sh/v1/models/openai/gpt-6-luna-decisions/endpoints)
records a 1050000-token context, $0.10/M input, zero completion cost and no implicit
caching, but no decision-specific long-context bands. Generic text-only and
reasoning metadata conflict with the exact Decisions contract; the latter defines
serving capabilities. Native price bands are not substituted for missing provider
bands.

[OpenRouter's model page](https://openrouter.ai/openai/gpt-6-luna-decisions)
records $0.10/M input, zero output/cache-read rates, 1050000 context tokens and up
to 200 questions. Its [alpha interface](https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-request)
uses `state`, named question objects, `criteria` and `noul`, rather than OpenAI's
wire envelope. Its [multimodal guide](https://openrouter.ai/docs/guides/community/multimodal-decisions)
establishes data URLs in top-level state-array image parts, no fetched remote
URLs and 128 images for this exact model. Cache-write prices and long-context
bands are omitted without independent decision-specific evidence. A binding does
not establish native OpenAI SDK compatibility.

Grida's [model discovery](https://gateway.grida.ai/v1/models),
[Decisions schema](https://gateway.grida.ai/schemas/decisions.json) and
[public API reference](https://gateway.grida.ai/llms.txt) establish its separate
`openai/gpt-6-luna-decisions` offering. It accepts the native question-array
envelope with predicate, choice and score questions, string or user-message
input, and inline PNG/JPEG/WebP images. Its subset allows 32 questions, eight
images, 2–255 choices and 2–10 score levels; it rejects boolean/string spelling
collisions and preserves per-question refusals. Published pricing is input-only
USD 0.10 per million tokens, with no output or cache charges. The binding records
that public contract without borrowing another provider's limits or price bands.
Model release provenance, intrinsic facts and other providers' bindings are
unchanged.

## Video endpoint and provider qualifications (2026-10-15)

### Seedance 2.5 and Grok Imagine Video 1.5 text variants

The existing image variants and their published service contracts are retained.
The fal text variants are separate exact endpoints with their own parameters and
published billing facts: [Seedance 2.5](https://fal.ai/models/bytedance/seedance-2.5/text-to-video/api)
and [Grok 1.5](https://fal.ai/models/xai/grok-imagine-video/v1.5/text-to-video/api).

Seedance's [detailed text page](https://fal.ai/models/bytedance/seedance-2.5/text-to-video)
defines output tokens as width × height × duration × 24 / 1024. At 480p and 720p,
the rate is USD 0.0214 per 1,000 output tokens. Its per-second examples are
approximations rather than a billing meter, and its summary calls the 1080p
token rate approximate. The exact-priced component is therefore limited to the
two resolutions whose rate is stated without qualification. The OpenAPI schema
includes 1080p even though the detailed page's older input table lists only
480p and 720p; endpoint parameters follow the exact OpenAPI schema. Defaults
and adaptive output options are not inferred as fixed billable output sizes.

Grok text generation has no input-image charge. Its independently sourced
output-second rates are USD 0.08 at 480p, 0.14 at 720p and 0.25 at 1080p on
the [text endpoint page](https://fal.ai/models/xai/grok-imagine-video/v1.5/text-to-video).
The existing image endpoint's image surcharge is not copied to text generation.

### MiniMax H3 and fal H3 Max

MiniMax H3's model release is grounded in the [July 31 vendor announcement](https://www.minimax.io/blog/minimax-h3).
H3 Max is a distinct fal post-trained variant, grounded in fal's
[August 27 announcement](https://blog.fal.ai/introducing-h3-max-by-fal/).
The `minimax/h3-max` namespace on fal is its exact serving endpoint namespace,
not evidence that the variant's developer is MiniMax. The public catalogue
identity is `fal/h3-max`, with fal as its native reference.

MiniMax [native API contracts](https://platform.minimax.io/docs/api-reference/video-generation-v2-create)
support H3 at 4–15 seconds, 768P/2K and H3 Max at 5–15 seconds, 480P/768P.
Their [native pricing](https://platform.minimax.io/docs/pricing/overview)
is independent of fal's prices. Native reference video and extra image charges
are explicitly qualified rather than treated as included output pricing.

The exact fal [H3 text](https://fal.ai/models/minimax/h3/text-to-video/api)
and [image](https://fal.ai/models/minimax/h3/image-to-video/api) schemas instead
accept integer 5–15-second durations and 480P/768P/2K/4K. The first and last
images are optional independently, and the output canvas follows the supplied
frame. The actual frame endpoint is `minimax/h3/image-to-video`.

fal's [H3 Max text schema](https://fal.ai/models/minimax/h3-max/text-to-video/api)
accepts fractional duration 0.92–15 seconds and warns that outputs can run
about 0.7 seconds longer. This warning does not establish an exact output
duration maximum, charged-duration rounding rule or requested-duration meter.
Its prompt expansion values are examples, not a schema enum. The regular
fal rates are explicitly stated on the [model page](https://fal.ai/models/minimax/h3-max/text-to-video):
USD 0.05/0.08/0.16 per output second at 480P/768P/1080P. Temporary discounted
rates are excluded from the catalogue.

The [official H3 repository](https://github.com/MiniMax-AI/MiniMax-H3)
and [weight repository](https://huggingface.co/MiniMaxAI/MiniMax-H3) are retained
as distribution facts. Their [Community License](https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/LICENSE)
has specific use and territorial restrictions; public download availability
does not imply unrestricted use or grant hosted API rights.

### FLUX 3 Video

The [BFL August 4 announcement](https://bfl.ai/blog/flux-3-video) establishes
the first broad release of FLUX 3 Video, independently of later FLUX 3 Image
and Action variants. The native call ID remains `flux-3-video`; modes are
request parameters, not invented separate native endpoint IDs.

[BFL pricing](https://docs.bfl.ai/quick_start/pricing) records output-second
prices by mode and resolution, with native 2K/4K rates distinct from the
[OpenRouter discovery SKUs](https://openrouter.ai/api/v1/videos/models).
Both records retain their provider's facts rather than flattening them into
one supposedly universal price. fal's [text](https://fal.ai/models/blackforestlabs/flux-3/text-to-video)
and [image](https://fal.ai/models/blackforestlabs/flux-3/image-to-video) routes
serve only 720p/1080p, priced at USD 0.17/0.29 per output second.

[Vercel discovery](https://ai-gateway.vercel.sh/v1/models) lists `bfl/flux-3-video`
with capability metadata but an empty pricing object. The binding is recorded
without inventing a unit or price. Vercel's supported resolution spellings,
`hd` and `fhd`, retain their original form.

### Gemini Omni 1.1 Flash

The stable model's release comes from Google's [August 27 announcement](https://blog.google/innovation-and-ai/technology/developers-tools/build-with-gemini-omni-1-1-flash/).
The [native model page](https://ai.google.dev/gemini-api/docs/models/gemini-omni-flash)
and [standard pricing](https://ai.google.dev/gemini-api/docs/pricing)
identify `gemini-omni-1.1-flash` and token billing: USD 1.50/9.00/17.50 per
million input/text-output/video-output tokens. Google's 5,792 video-output
tokens per second at 720p are not a formula for every resolution.

The exact versioned fal [text](https://fal.ai/models/google/gemini-omni-flash/v1.1/text-to-video)
and [image](https://fal.ai/models/google/gemini-omni-flash/v1.1/image-to-video)
endpoints use output-second pricing instead: USD 0.03/0.10/0.15/0.30 at
360p/720p/1080p/4k. Their schemas accept integer durations 3–10 seconds.
The stable variant is absent from OpenRouter video discovery and Vercel model
discovery; Vercel's separately listed preview is not represented as stable 1.1.

## Image endpoint qualifications (2026-10-15)

[Muse Image](https://fal.ai/models/meta/muse-image/text-to-image/api) uses ratios
at its fixed approximate pixel count; a ratio is not an exact size contract.
[Qwen Image 3.0](https://fal.ai/models/alibaba/qwen-image-3/text-to-image/api)
is the Standard model, distinct from Pro. Native pricing is in CNY and is not
converted to USD here. fal's regular 1K/2K rates do not document the precise
custom-size price breakpoint; no breakpoint is inferred.
[Ideogram 4.5 generation](https://fal.ai/models/ideogram/v4.5/api) and
[editing](https://fal.ai/models/ideogram/v4.5/edit/api) have distinct dimension
and source-image contracts. The exact launch day remains unknown, using
undated provider-endpoint provenance; native price parity is not inferred.
[Reve 2.1's fal tutorial](https://fal.ai/learn/tools/how-to-use-reve-2-1)
establishes a regular USD 0.25/generated-image price, but the exact endpoint
request/result schemas are unavailable in the public OpenAPI feed. Endpoint
identities are recorded without inventing edit fields or a result envelope.
Missing prices remain unknown, never zero. Current provider coverage follows
exact discovery identities, not similar predecessor names.
