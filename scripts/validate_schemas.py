#!/usr/bin/env python3
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker, ValidationError


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
VALID = SCHEMAS / "examples" / "valid"
INVALID = SCHEMAS / "examples" / "invalid"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def schema_name_for_example(path: Path) -> str:
    return f"{path.stem}.schema.json"


def main() -> None:
    schemas = {}
    for path in sorted(SCHEMAS.glob("*.schema.json")):
        schema = load_json(path)
        Draft202012Validator.check_schema(schema)
        schemas[path.name] = schema
        print(f"schema ok: {path.relative_to(ROOT)}")

    missing = []
    for schema_name in schemas:
        example_name = schema_name.replace(".schema.json", ".json")
        if not (VALID / example_name).exists():
            missing.append(f"missing valid example: {example_name}")
        if not (INVALID / example_name).exists():
            missing.append(f"missing invalid example: {example_name}")
    if missing:
        raise SystemExit("\n".join(missing))

    for path in sorted(VALID.glob("*.json")):
        schema = schemas[schema_name_for_example(path)]
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(load_json(path))
        print(f"valid example ok: {path.relative_to(ROOT)}")

    for path in sorted(INVALID.glob("*.json")):
        schema = schemas[schema_name_for_example(path)]
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        try:
            validator.validate(load_json(path))
        except ValidationError:
            print(f"invalid example rejected: {path.relative_to(ROOT)}")
        else:
            raise SystemExit(f"invalid example unexpectedly accepted: {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
