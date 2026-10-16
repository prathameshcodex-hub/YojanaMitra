#!/usr/bin/env python3
"""Offline quality audit for the SchemeSathi scheme catalogue."""

import json
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "backend" / "data" / "schemes.json"

REQUIRED_FIELDS = (
    "id",
    "name",
    "state",
    "level",
    "description",
    "benefits",
    "eligibility",
    "verification_status",
    "official_source_url",
)

def normalized(value):
    return " ".join(str(value or "").casefold().split())

def is_valid_https_url(value):
    if not isinstance(value, str):
        return False
    parsed = urlparse(value.strip())
    return parsed.scheme == "https" and bool(parsed.netloc)

def main():
    errors = []
    warnings = []

    if not DATA_FILE.exists():
        print(f"ERROR: Dataset not found: {DATA_FILE}")
        return 1

    try:
        schemes = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"ERROR: Invalid JSON: {exc}")
        return 1

    if not isinstance(schemes, list):
        print("ERROR: Dataset root must be a JSON list.")
        return 1

    ids = []
    names = []
    statuses = Counter()
    unsupported_count = 0
    no_rules_count = 0

    for index, scheme in enumerate(schemes, start=1):
        location = f"Record #{index}"

        if not isinstance(scheme, dict):
            errors.append(f"{location}: record is not an object")
            continue

        scheme_id = str(scheme.get("id") or "").strip()
        name = str(scheme.get("name") or "").strip()

        if scheme_id:
            ids.append(scheme_id)
        else:
            errors.append(f"{location}: missing scheme ID")

        if name:
            names.append(normalized(name))
        else:
            errors.append(f"{location}: missing scheme name")

        for field in REQUIRED_FIELDS:
            if field not in scheme or scheme[field] in (None, ""):
                errors.append(
                    f"{scheme_id or location}: missing required field '{field}'"
                )

        eligibility = scheme.get("eligibility")
        if not isinstance(eligibility, dict):
            errors.append(f"{scheme_id or location}: eligibility must be an object")
            eligibility = {}

        source_url = scheme.get("official_source_url")
        if source_url and not is_valid_https_url(source_url):
            errors.append(
                f"{scheme_id}: invalid official_source_url: {source_url}"
            )

        application_url = scheme.get("application_url")
        if application_url and not is_valid_https_url(application_url):
            warnings.append(
                f"{scheme_id}: review application_url: {application_url}"
            )

        status = str(scheme.get("verification_status") or "MISSING")
        statuses[status] += 1

        ignored = {"verification_required", "verification_note"}
        structured_rules = [
            key for key in eligibility
            if key not in ignored
        ]

        unsupported = scheme.get("individual_matching_supported") is False

        if unsupported:
            unsupported_count += 1
            if not str(scheme.get("matching_note") or "").strip():
                warnings.append(
                    f"{scheme_id}: unsupported matching lacks matching_note"
                )

        if not structured_rules:
            no_rules_count += 1
            if not unsupported:
                warnings.append(
                    f"{scheme_id}: no structured rules but matching is not disabled"
                )

        if status != "verified":
            # Pending records are allowed, but must not be represented
            # as officially verified.
            if status == "MISSING":
                warnings.append(f"{scheme_id}: missing verification status")

    duplicate_ids = [
        value for value, count in Counter(ids).items() if count > 1
    ]
    duplicate_names = [
        value for value, count in Counter(names).items() if count > 1
    ]

    if duplicate_ids:
        errors.append(f"Duplicate IDs: {duplicate_ids}")

    if duplicate_names:
        errors.append(f"Duplicate scheme names: {duplicate_names}")

    print("=== SCHEMESATHI DATASET AUDIT ===")
    print("Dataset:", DATA_FILE.relative_to(ROOT))
    print("Total records:", len(schemes))
    print("Unique IDs:", len(set(ids)))
    print("Duplicate IDs:", len(duplicate_ids))
    print("Duplicate names:", len(duplicate_names))
    print("Records without structured eligibility rules:", no_rules_count)
    print("Unsupported for individual matching:", unsupported_count)
    print("Verification-status distribution:", dict(statuses))
    print("Validation errors:", len(errors))
    print("Review warnings:", len(warnings))

    if errors:
        print("\nERRORS:")
        for item in errors[:30]:
            print("-", item)

    if warnings:
        print("\nWARNINGS (first 20):")
        for item in warnings[:20]:
            print("-", item)

    if errors:
        print("\nAUDIT RESULT: FAIL")
        return 1

    print("\nAUDIT RESULT: PASS")
    print("Note: PASS validates structure, not official scheme eligibility.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
