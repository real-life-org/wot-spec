#!/usr/bin/env python3
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "conformance" / "manifest.json"
VALID_EXAMPLES = ROOT / "schemas" / "examples" / "valid"
INVALID_EXAMPLES = ROOT / "schemas" / "examples" / "invalid"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def require_existing(relative_path: str) -> Path:
    path = ROOT / relative_path
    if not path.exists():
        raise SystemExit(f"missing conformance artifact: {relative_path}")
    return path


def require_list(value, label: str) -> list:
    if not isinstance(value, list):
        raise SystemExit(f"{label} must be a list")
    return value


def validate_schema_reference(relative_path: str) -> None:
    path = require_existing(relative_path)
    if not path.name.endswith(".schema.json"):
        raise SystemExit(f"schema reference must end with .schema.json: {relative_path}")

    example_name = path.name.replace(".schema.json", ".json")
    for root in (VALID_EXAMPLES, INVALID_EXAMPLES):
        example = root / example_name
        if not example.exists():
            raise SystemExit(f"missing schema example for {relative_path}: {example.relative_to(ROOT)}")


def validate_vector_reference(vector_ref: dict) -> int:
    if not isinstance(vector_ref, dict):
        raise SystemExit("test_vectors entries must be objects")
    vector_file = vector_ref.get("file")
    sections = require_list(vector_ref.get("sections"), f"test vector sections for {vector_file}")
    data = load_json(require_existing(vector_file))

    for section in sections:
        if section not in data:
            raise SystemExit(f"missing test vector section {section!r} in {vector_file}")
    return len(sections)


def validate_library_check(check: dict) -> None:
    vector_file = check.get("file")
    section = check.get("section")
    expected_libraries = set(require_list(check.get("libraries"), f"libraries for {section}"))
    data = load_json(require_existing(vector_file))
    if section not in data:
        raise SystemExit(f"missing library check section {section!r} in {vector_file}")

    actual = {item.get("library") for item in data[section].get("validated_with", [])}
    missing = expected_libraries - actual
    if missing:
        raise SystemExit(f"missing DIDComm library validation in {vector_file}:{section}: {sorted(missing)}")


def main() -> None:
    manifest = load_json(MANIFEST)
    profiles = manifest.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        raise SystemExit("conformance manifest must define profiles")

    profile_names = set(profiles)
    for name, profile in sorted(profiles.items()):
        for required in require_list(profile.get("requires", []), f"requires for {name}"):
            if required not in profile_names:
                raise SystemExit(f"profile {name} requires unknown profile {required}")

        docs = require_list(profile.get("spec_documents", []), f"spec_documents for {name}")
        for doc in docs:
            require_existing(doc)

        schemas = require_list(profile.get("schemas", []), f"schemas for {name}")
        for schema in schemas:
            validate_schema_reference(schema)

        vector_sections = 0
        vectors = require_list(profile.get("test_vectors", []), f"test_vectors for {name}")
        for vector_ref in vectors:
            vector_sections += validate_vector_reference(vector_ref)

        for check in require_list(profile.get("library_checks", []), f"library_checks for {name}"):
            validate_library_check(check)

        print(
            f"profile ok: {name} "
            f"({len(docs)} docs, {len(schemas)} schemas, {vector_sections} vector sections)"
        )

    validators = require_list(manifest.get("validators", []), "validators")
    for validator in validators:
        if not validator.get("name") or not validator.get("command"):
            raise SystemExit("validators need name and command")
    print("conformance manifest ok")


if __name__ == "__main__":
    main()
