# Hi robots, welcome to Grida Models.

This repository is the single source of truth for Grida's AI model catalogue. It is a
hand-maintained, source-backed record of model identities, capabilities, limits, provider
bindings, and published prices.

**Mission**

- One authored copy of every model fact. Every other copy is a generated projection.
- Every fact carries a first-party source. A stale entry is a wrong answer.

> **This repository is public.** Push = publish: anything in a pushed branch is published,
> even if the commit is later deleted. See [Public repository rules](#public-repository-rules).

## Current state

[`models/`](./models/) is the authored source: one TOML card per model, grouped by lab.
[`catalogue/facts.json`](./catalogue/facts.json) is generated from it and is the contract
consumers read, at schema version 1. The catalogue was imported from
[gridaco/grida](https://github.com/gridaco/grida). How other projects will consume it is
undecided; don't add anything that assumes an answer.

## Project Structure

> **When entering an unfamiliar directory**, always check for `README.md` and `AGENTS.md` first.

| path                                 | notes                                                                |
| ------------------------------------ | -------------------------------------------------------------------- |
| [models/](./models/)                 | **The source.** One card per model: `models/<lab>/<model>/card.toml` |
| [catalogue/](./catalogue/)           | **The contract.** Generated JSON, JSON Schema, provenance notes      |
| [scripts/](./scripts/)               | Tooling: build and validation                                        |
| [tests/](./tests/)                   | Tests for the tooling                                                |
| [.agents/skills/](./.agents/skills/) | Agent skills. `.claude/skills` is a symlink to it                    |
| [README.md](./README.md)             | Public overview, principles, decisions                               |
| [AGENTS.md](./AGENTS.md)             | This file. `CLAUDE.md` is a symlink to it                            |

**Source vs. contract vs. tooling.** Facts are authored once, as cards in `models/`.
Everything a consumer reads lives in `catalogue/` and must be readable from any language:
plain JSON and JSON Schema, no generated code, no language-specific files.
`catalogue/facts.json` is generated from the cards; never edit it by hand. Tooling outside
both may use whichever language fits the job (Python today, TypeScript when it fits better),
and is never part of the contract.

Each lab directory in `models/` holds a `lab.toml` (display name, first-party homepage, and
the source of its logo) and the lab's official logo, generated into `catalogue/labs.json` and
`catalogue/logos/`. A logo comes from the lab's own brand kit, press kit, or website, never an
aggregator or a redrawing. A provider registry is still undecided (open decision 2).

## Open decisions

These are listed in the [README](./README.md#open-decisions). Treat them as quarantined:
nothing written here may depend on an answer that has not been decided. When a task forces
one of these questions, raise it with the user instead of answering it implicitly.

1. Distribution: how consumers pin and receive the catalogue.
2. Whether a provider registry (labels, logos, ID prefixes) lives here.

## Public repository rules

Some future consumers of this catalogue may be private. Never put any of the following in a
file, commit, branch name, or PR:

- the name, URL, path, file, PR, or tooling of a private repository or service;
- how a consumer routes requests (which provider for which model, fallback order);
- negotiated, wholesale, or account-specific prices; margins, markups, credit conversions;
- provider account details, contract or rights reviews;
- hostnames, account IDs, credential or environment variable names, budgets, roadmap.

Restate a need in neutral, public terms ("per-second video pricing keyed by resolution").
When in doubt, leave it out and ask.

Changing the catalogue's shape is a contract change. Land it on its own, keep it additive, and
justify it on its own merits: a field that only makes sense for one consumer's internals
doesn't belong in the contract.

## Rules

- **Source every fact.** Prices, limits, capabilities, and release dates cite a first-party
  page. [models.dev](https://models.dev) and similar aggregators are leads, never sources.
  See `$catalogue` and `$provenance`.
- **Never fabricate.** If a value cannot be verified, leave it out and say so. Do not
  estimate a price, round a limit, or infer a release day.
- **Published prices only.** No negotiated, wholesale, account-specific, or internal prices.
  No markup, credit conversion, or margin.
- **Preserve IDs exactly.** Model and provider IDs keep their exact spelling and casing.
  Authored field names are `lower_snake_case`.
- **Additive by default.** Add fields; do not rename or repurpose them. A breaking change
  needs a new schema version, decided with the user.
- **Facts are independent of products.** Being catalogued is not the same as being offered
  by a Grida product.

## Skills

Skills live in [`.agents/skills/`](./.agents/skills/). Each is a `SKILL.md` with `name` and
`description` frontmatter.

| skill                                                | use when                                                              |
| ---------------------------------------------------- | --------------------------------------------------------------------- |
| [`catalogue`](./.agents/skills/catalogue/SKILL.md)   | Adding, updating, deprecating, or removing a model, binding, or price |
| [`provenance`](./.agents/skills/provenance/SKILL.md) | Grounding a release date or recording a source qualification          |

## Testing & Development

Tooling runs with [uv](https://docs.astral.sh/uv/) (Python 3.12+).

```sh
uv sync                              # install tooling dependencies
uv run scripts/build.py              # regenerate catalogue/facts.json and labs.json from models/
uv run scripts/check.py              # validate the source, generated files, schemas + invariants
uv run pytest                        # test the checker
npx -y oxfmt@0.71.0                  # format Markdown, TOML, JSON, YAML
```

After editing a card, run `build.py` then `check.py`, and commit the card with the regenerated
`facts.json`. CI runs `check.py` (which fails if `facts.json` is out of date) and `pytest` on
every PR.

Formatting uses [oxfmt](https://oxc.rs/docs/guide/usage/formatter) through `npx`, with no
`package.json`; its settings are in `.oxfmtrc.json`, and the generated `facts.json` is
excluded. CI runs `npx -y oxfmt@0.71.0 --check`; keep the version here and in
`.github/workflows/check.yml` in sync.

When adding an invariant to `check.py`, add a test in `tests/` that proves it rejects the case
it exists for. A known violation goes in `KNOWN_EXCEPTIONS` with a reason, never in a skipped
section.

## Commits and PRs

- One concern per PR. A data change and a schema change are separate PRs.
- The PR description names the source for every changed fact.
- Write for a stranger who found the repository through search. No internal context.
