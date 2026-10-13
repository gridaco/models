"""Validate the authored cards in `models/` and the catalogue contract in `catalogue/`.

Three layers:

1. Source: every card in `models/` sits at the path its lab and ID give it, names a
   known section, every lab directory has a `lab.toml`, and the generated
   `catalogue/models.json` and `catalogue/labs.json` are exactly what the source
   generates (`scripts/build.py`).
2. Structure: `catalogue/models.json` and `catalogue/labs.json` against their schemas in
   `catalogue/schemas/` (JSON Schema 2020-12, with format assertions on).
3. Invariants the schema cannot express: table keys equal card IDs, release
   dates are real calendar dates, facts carry no product policy, and provider
   bindings are keyed by their own provider.

Usage:
    uv run scripts/check.py

Exits 1 and prints one line per problem when the catalogue is invalid.
"""

from __future__ import annotations

import datetime
import json
import math
import sys
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

import build
import cards

ROOT = Path(__file__).resolve().parent.parent
MODELS_JSON = ROOT / "catalogue" / "models.json"
MODELS_SCHEMA = ROOT / "catalogue" / "schemas" / "models.schema.json"
LABS = ROOT / "catalogue" / "labs.json"
LABS_SCHEMA = ROOT / "catalogue" / "schemas" / "labs.schema.json"

# Top-level sections that are not tables of cards keyed by ID.
NON_TABLE_SECTIONS = {"three_d.rig_check.operation"}

# Listing and lifecycle decisions belong to the products that consume the
# catalogue, not to model facts.
POLICY_KEYS = ("listed", "listed_reason", "status", "legacy", "deprecated", "default")

# Families whose cards hold intrinsic facts plus per-provider bindings.
# A primary-provider choice on such a card is product policy.
MULTI_PROVIDER_SECTIONS = ("image.models", "video.models")

# Known violations carried over unchanged from the source data. Each entry is
# (section, card id, key). An exception that no longer matches the data is
# itself reported, so this list can only shrink.
KNOWN_EXCEPTIONS = {
    # Carried with the embedding card's storage contract; see catalogue/README.md.
    ("embedding.models", "google/gemini-embedding-2", "deprecated"),
}

# Lab directories without a lab.toml. Each is the ID namespace of a card that has no
# sourced `vendor` yet: its publisher on a provider, not the lab that made the model.
# An entry that no longer applies is reported, so this set can only shrink.
KNOWN_UNREGISTERED_LABS = {
    "851-labs",  # publisher of 851-labs/background-remover on Replicate
    "nightmareai",  # publisher of nightmareai/real-esrgan on Replicate
}


def load(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def schema_errors(facts: Any, schema: Any) -> Iterator[str]:
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(
        schema, format_checker=Draft202012Validator.FORMAT_CHECKER
    )
    for error in sorted(validator.iter_errors(facts), key=lambda e: list(e.absolute_path)):
        path = "/".join(str(p) for p in error.absolute_path) or "(root)"
        yield f"schema: {path}: {error.message}"


def is_calendar_date(value: str) -> bool:
    try:
        return datetime.date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


SOURCED_OBJECTS = (
    "distribution",
    "output_token_calculator",
    "vision_tokenization",
    "capabilities",
    "token_pricing",
    "published_pricing",
    "limits",
)


def fact_objects(facts: dict[str, Any]) -> Iterator[tuple[str, dict[str, Any]]]:
    """Visit cards, provider bindings, and endpoint variants without merging scopes."""
    for section, table in facts.items():
        if not isinstance(table, dict):
            continue
        entries = (
            [(section, table)] if section in NON_TABLE_SECTIONS else [
                (f"{section}/{key}", card) for key, card in table.items()
            ]
        )
        for where, card in entries:
            if not isinstance(card, dict):
                continue
            yield where, card
            endpoints = card.get("endpoints", [])
            if isinstance(endpoints, list):
                for index, endpoint in enumerate(endpoints):
                    if isinstance(endpoint, dict):
                        yield f"{where}/endpoints/{index}", endpoint
            providers = card.get("providers", {})
            if not isinstance(providers, dict):
                continue
            for name, binding in providers.items():
                if not isinstance(binding, dict):
                    continue
                binding_where = f"{where}/providers/{name}"
                yield binding_where, binding
                endpoints = binding.get("endpoints", [])
                if not isinstance(endpoints, list):
                    continue
                for index, endpoint in enumerate(endpoints):
                    if isinstance(endpoint, dict):
                        yield f"{binding_where}/endpoints/{index}", endpoint


def source_url_errors(value: Any, where: str) -> Iterator[str]:
    if not isinstance(value, str):
        return
    try:
        url = urlsplit(value)
        valid = (
            url.scheme == "https" and bool(url.hostname)
            and url.username is None and url.password is None
        )
        # Accessing port also catches malformed authorities.
        url.port
    except ValueError:
        valid = False
    if not valid:
        yield f"{where}: source_url must be an absolute HTTPS URL without credentials"


def numeric_range_errors(value: dict[str, Any], where: str) -> Iterator[str]:
    for lower, upper in [
        ("minimum", "maximum"), ("min_items", "max_items"),
        ("min_length", "max_length"), ("min_edge", "max_edge"),
        ("min_pixels", "max_pixels"), ("min", "max"),
    ]:
        lo, hi = value.get(lower), value.get(upper)
        if isinstance(lo, (int, float)) and isinstance(hi, (int, float)) and lo > hi:
            yield f"{where}: {lower} exceeds {upper}"
    for key, number in value.items():
        if isinstance(number, float) and not math.isfinite(number):
            yield f"{where}/{key}: number must be finite"


def calculator_errors(calculator: dict[str, Any], where: str) -> Iterator[str]:
    axes = calculator.get("quality_axes", {})
    axes = axes if isinstance(axes, dict) else {}
    seen = set()
    examples = calculator.get("examples", [])
    if not isinstance(examples, list):
        return
    for index, example in enumerate(examples):
        if not isinstance(example, dict):
            continue
        example_where = f"{where}/examples/{index}"
        yield from source_url_errors(example.get("source_url"), example_where)
        key = (example.get("width"), example.get("height"), example.get("quality"))
        # Invalid compound values are already schema errors; avoid hashing them.
        if not all(isinstance(part, (int, str)) for part in key):
            continue
        if key in seen:
            yield f"{example_where}: duplicate size/quality example"
        seen.add(key)
        if example.get("quality") not in axes:
            yield f"{example_where}: quality has no calculator axis"
        yield from numeric_range_errors(example, example_where)
        width, height, quality = key
        axis = axes.get(quality)
        offset, divisor = calculator.get("area_offset"), calculator.get("area_divisor")
        output_tokens = example.get("output_tokens")
        numbers = (width, height, axis, offset, divisor, output_tokens)
        if (
            all(isinstance(number, int) and not isinstance(number, bool) for number in numbers)
            and min(width, height, axis, divisor) > 0
        ):
            short_axis = round(Fraction(axis * min(width, height), max(width, height)))
            numerator = axis * short_axis * (offset + width * height)
            expected = -(-numerator // divisor)
            if output_tokens != expected:
                yield f"{example_where}: output_tokens {output_tokens} does not match calculator {expected}"


def token_pricing_errors(pricing: dict[str, Any], where: str) -> Iterator[str]:
    tiers = pricing.get("tiers", [])
    if not isinstance(tiers, list):
        return
    ranges: dict[str, list[tuple[int, int | None]]] = {}
    for index, tier in enumerate(tiers):
        if not isinstance(tier, dict):
            continue
        lo = tier.get("minimum_input_tokens")
        hi = tier.get("maximum_input_tokens")
        meter = tier.get("meter")
        if not isinstance(lo, int) or isinstance(lo, bool) or not isinstance(meter, str):
            continue
        if hi is not None and (not isinstance(hi, int) or isinstance(hi, bool)):
            continue
        if hi is not None and hi <= lo:
            yield f"{where}/tiers/{index}: exclusive maximum_input_tokens must exceed minimum_input_tokens"
        ranges.setdefault(meter, []).append((lo, hi))
    for meter, bands in ranges.items():
        bands.sort(key=lambda band: band[0])
        for (_, previous_maximum), (minimum, _) in zip(bands, bands[1:]):
            if previous_maximum is None or previous_maximum > minimum:
                yield f"{where}: overlapping input-token tiers for {meter}"


def distribution_errors(distribution: dict[str, Any], where: str) -> Iterator[str]:
    code = distribution.get("code")
    artifacts = []
    if isinstance(code, dict):
        code_where = f"{where}/code"
        yield from source_url_errors(code.get("repository_url"), f"{code_where}/repository_url")
        artifacts.append((code_where, code))
    weights = distribution.get("weights", [])
    seen_ids: set[str] = set()
    seen_urls: dict[str, list[str | None]] = {}
    if isinstance(weights, list):
        for index, weight in enumerate(weights):
            if not isinstance(weight, dict):
                continue
            weight_where = f"{where}/weights/{index}"
            artifacts.append((weight_where, weight))
            url, variant = weight.get("url"), weight.get("id")
            yield from source_url_errors(url, f"{weight_where}/url")
            if isinstance(variant, str):
                if variant in seen_ids:
                    yield f"{weight_where}: duplicate weight variant {variant!r}"
                seen_ids.add(variant)
            else:
                variant = None
            if isinstance(url, str):
                previous = seen_urls.setdefault(url, [])
                if previous and (variant is None or None in previous or variant in previous):
                    yield f"{weight_where}: duplicate weight URL without distinct variant IDs"
                previous.append(variant)
    for artifact_where, artifact in artifacts:
        license = artifact.get("license")
        if isinstance(license, dict):
            yield from source_url_errors(license.get("url"), f"{artifact_where}/license/url")


def published_pricing_errors(pricing: dict[str, Any], where: str) -> Iterator[str]:
    """Preserve exact public meter amounts without accepting malformed bands."""
    seen_ids = set()
    components = pricing.get("components", [])
    if not isinstance(components, list):
        return
    for index, component in enumerate(components):
        if not isinstance(component, dict):
            continue
        component_where = f"{where}/components/{index}"
        identifier = component.get("id")
        if isinstance(identifier, str):
            if identifier in seen_ids:
                yield f"{component_where}: duplicate price component id {identifier!r}"
            seen_ids.add(identifier)
        condition = component.get("when")
        if isinstance(condition, dict):
            try:
                json.dumps(condition, allow_nan=False)
                Draft202012Validator.check_schema(condition)
            except (SchemaError, TypeError, ValueError):
                yield f"{component_where}: when must be a valid JSON Schema predicate"
        rounding = component.get("quantity_rounding")
        if isinstance(rounding, dict):
            if rounding.get("mode") == "none" and rounding.get("increment") is not None:
                yield f"{component_where}: no rounding requires a null increment"
            if rounding.get("mode") == "ceil" and rounding.get("increment") is None:
                yield f"{component_where}: ceil rounding requires an increment"
        band = component.get("quantity_range")
        if isinstance(band, dict) and band.get("max") is not None:
            try:
                minimum, maximum = Decimal(band.get("min")), Decimal(band.get("max"))
            except (InvalidOperation, TypeError, ValueError):
                continue  # the schema reports malformed numbers
            if minimum.is_finite() and maximum.is_finite() and minimum >= maximum:
                yield f"{component_where}: exclusive range max must exceed min"


def provider_fact_errors(facts: dict[str, Any]) -> Iterator[str]:
    for section, table in facts.items():
        if not isinstance(table, dict):
            continue
        entries = [(section, table)] if section in NON_TABLE_SECTIONS else [
            (f"{section}/{key}", card) for key, card in table.items()
        ]
        for where, card in entries:
            if not isinstance(card, dict):
                continue
            providers = card.get("providers", {})
            providers = providers if isinstance(providers, dict) else {}
            for name, binding in providers.items():
                if not isinstance(binding, dict):
                    continue
                if binding.get("provider") != name:
                    yield f"{where}/providers/{name}: binding.provider is {binding.get('provider')!r}"
                if not binding.get("id"):
                    yield f"{where}/providers/{name}: binding has no id"
                if "source_url" in binding:
                    yield from source_url_errors(binding["source_url"], f"{where}/providers/{name}")
            direct = card.get("provider")
            reference = card.get("reference_provider")
            if isinstance(reference, str) and reference not in providers and reference != direct:
                yield f"{where}: reference_provider has no provider binding or direct provider"
            coverage = card.get("provider_coverage", {})
            if not isinstance(coverage, dict):
                continue
            for provider, record in coverage.items():
                if not isinstance(record, dict):
                    continue
                record_where = f"{where}/provider_coverage/{provider}"
                yield from source_url_errors(record.get("source_url"), record_where)
                listed = provider in providers or provider == direct
                disposition = record.get("disposition")
                if disposition == "listed" and not listed:
                    yield f"{record_where}: listed provider has no binding or direct provider"
                if isinstance(disposition, str) and disposition in {"not_listed", "excluded"} and listed:
                    yield f"{record_where}: absent or excluded provider still has a binding"


def published_fact_errors(facts: dict[str, Any]) -> Iterator[str]:
    for where, value in fact_objects(facts):
        for key in ("source_url", "request_schema_url", "result_schema_url"):
            if key in value:
                yield from source_url_errors(value[key], f"{where}/{key}")
        endpoints = value.get("endpoints", [])
        seen_endpoint_ids = set()
        if isinstance(endpoints, list):
            for endpoint in endpoints:
                endpoint_id = endpoint.get("id") if isinstance(endpoint, dict) else None
                if not isinstance(endpoint_id, str):
                    continue
                if endpoint_id in seen_endpoint_ids:
                    yield f"{where}: duplicate endpoint {endpoint_id!r}"
                seen_endpoint_ids.add(endpoint_id)
        for name in SOURCED_OBJECTS:
            sourced = value.get(name)
            if not isinstance(sourced, dict):
                continue
            sourced_where = f"{where}/{name}"
            yield from source_url_errors(sourced.get("source_url"), sourced_where)
            if "source_js_url" in sourced:
                yield from source_url_errors(sourced["source_js_url"], f"{sourced_where}/source_js_url")
            yield from numeric_range_errors(sourced, sourced_where)
            if name == "distribution":
                yield from distribution_errors(sourced, sourced_where)
            elif name == "output_token_calculator":
                yield from calculator_errors(sourced, sourced_where)
            elif name == "token_pricing":
                yield from token_pricing_errors(sourced, sourced_where)
            elif name == "published_pricing":
                yield from published_pricing_errors(sourced, sourced_where)
        if "parameters" in value or "image_constraints" in value:
            yield from source_url_errors(value.get("source_url"), where)
        parameters = value.get("parameters", {})
        if isinstance(parameters, dict):
            for name, parameter in parameters.items():
                if isinstance(parameter, dict):
                    parameter_where = f"{where}/parameters/{name}"
                    yield from numeric_range_errors(parameter, parameter_where)
                    if "source_url" in parameter:
                        yield from source_url_errors(parameter["source_url"], parameter_where)
        constraints = value.get("image_constraints")
        if isinstance(constraints, dict):
            yield from numeric_range_errors(constraints, f"{where}/image_constraints")
            if isinstance(constraints.get("aspect_ratio"), dict):
                yield from numeric_range_errors(
                    constraints["aspect_ratio"], f"{where}/image_constraints/aspect_ratio"
                )


def invariant_errors(facts: dict[str, Any]) -> Iterator[str]:
    used_exceptions: set[tuple[str, str, str]] = set()

    for section, table in facts.items():
        if section in NON_TABLE_SECTIONS or not isinstance(table, dict):
            continue
        for key, card in table.items():
            where = f"{section}/{key}"
            if not isinstance(card, dict):
                yield f"{where}: card is not an object"
                continue

            if card.get("id") != key:
                yield f"{where}: id {card.get('id')!r} does not match its table key"

            if section == "text.catalog" and not card.get("vendor"):
                yield f"{where}: text card requires a vendor lab"

            release = card.get("release")
            if isinstance(release, dict):
                date = release.get("date")
                if date is None:
                    if release.get("basis") != "provider_endpoint":
                        yield f"{where}: release.date is null but basis is not provider_endpoint"
                elif not (isinstance(date, str) and is_calendar_date(date)):
                    yield f"{where}: release.date {date!r} is not a YYYY-MM-DD calendar date"
                if not str(release.get("source_url", "")).startswith("https://"):
                    yield f"{where}: release.source_url is not https"
            else:
                yield f"{where}: missing release"

            for policy_key in POLICY_KEYS:
                if policy_key in card:
                    exception = (section, key, policy_key)
                    if exception in KNOWN_EXCEPTIONS:
                        used_exceptions.add(exception)
                    else:
                        yield f"{where}: carries product policy key {policy_key!r}"

            if section in MULTI_PROVIDER_SECTIONS:
                if "provider" in card:
                    yield f"{where}: selects a primary 'provider'; bindings carry no preference"
                providers = card.get("providers")
                if not isinstance(providers, dict) or not providers:
                    yield f"{where}: has no provider bindings"
                    continue

    yield from provider_fact_errors(facts)
    yield from published_fact_errors(facts)

    for exception in sorted(KNOWN_EXCEPTIONS - used_exceptions):
        yield f"stale known exception {exception}: remove it from KNOWN_EXCEPTIONS"


def check(facts: Any, schema: Any) -> list[str]:
    errors = list(schema_errors(facts, schema))
    if isinstance(facts, dict):
        errors.extend(invariant_errors(facts))
    return errors


def source_errors(committed: dict[Path, bytes] | None = None) -> list[str]:
    outputs, errors = build.build()
    errors += cards.lab_errors(
        cards.load_labs(build.MODELS), cards.load_cards(build.MODELS), KNOWN_UNREGISTERED_LABS
    )
    if not errors:
        for path in build.stale(outputs, committed):
            errors.append(f"{path.relative_to(ROOT)} is out of date: run uv run scripts/build.py")
        for path in build.orphans(outputs):
            errors.append(f"{path.relative_to(ROOT)} is not generated by any lab: run uv run scripts/build.py")
    return errors


def main() -> int:
    facts = load(MODELS_JSON)
    errors = source_errors() + check(facts, load(MODELS_SCHEMA))
    errors += [f"labs.json {error}" for error in schema_errors(load(LABS), load(LABS_SCHEMA))]
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        print(f"{len(errors)} problem(s)", file=sys.stderr)
        return 1
    count = sum(
        len(table)
        for section, table in facts.items()
        if section not in NON_TABLE_SECTIONS and isinstance(table, dict)
    )
    print(f"ok: {MODELS_JSON.relative_to(ROOT)} ({count} cards), {LABS.relative_to(ROOT)} ({len(load(LABS))} labs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
