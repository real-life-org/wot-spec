#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
CONFORMANCE = ROOT / "CONFORMANCE.md"
MANIFEST = ROOT / "conformance" / "manifest.json"
SCHEMAS = ROOT / "schemas"
VALID_EXAMPLES = SCHEMAS / "examples" / "valid"
INVALID_EXAMPLES = SCHEMAS / "examples" / "invalid"

MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
HTML_ANCHOR_RE = re.compile(r"<a\s+(?:[^>]*?\s+)?(?:id|name)=[\"']([^\"']+)[\"']", re.IGNORECASE)
INFO_MARKER_RE = re.compile(r"\b(?:TODO|FIXME|TBD|Offene|offene|Klaer|Klär)\b|wot-spec#\d+")

# Baseline for pre-existing normative spec anchor drift found when this
# offline harness was introduced. This slice may not edit normative spec
# files, so these links remain informational until a separate spec cleanup
# PR fixes them deliberately.
KNOWN_ANCHOR_DRIFT = {
    ("03-wot-sync/003-transport-und-broker.md", 117, "#device-liste"),
    ("05-hmc-extensions/H03-gossip.md", 36, "../03-wot-sync/003-transport-und-broker.md#message-envelope-didcomm-kompatibel"),
}


class CheckState:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.info: list[str] = []

    def fail(self, message: str) -> None:
        self.errors.append(message)

    def note(self, message: str) -> None:
        self.info.append(message)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def load_json(path: Path, state: CheckState):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        state.fail(f"invalid JSON: {rel(path)}:{exc.lineno}:{exc.colno}: {exc.msg}")
    except OSError as exc:
        state.fail(f"cannot read JSON: {rel(path)}: {exc}")
    return None


def iter_json_files() -> list[Path]:
    ignored_parts = {".git", "node_modules"}
    return sorted(
        path
        for path in ROOT.rglob("*.json")
        if not ignored_parts.intersection(path.relative_to(ROOT).parts)
    )


def slugify_heading(heading: str) -> str:
    heading = re.sub(r"<[^>]+>", "", heading)
    heading = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", heading)
    heading = heading.replace("`", "")
    chars = []
    for char in heading.strip().lower():
        if char.isalnum() or char in {" ", "-"}:
            chars.append(char)
    slug = "".join("-" if char.isspace() else char for char in chars).strip("-")
    return slug


def markdown_anchors(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    anchors: set[str] = set()
    seen: dict[str, int] = {}
    for line in text.splitlines():
        for explicit in HTML_ANCHOR_RE.findall(line):
            anchors.add(explicit)
        match = HEADING_RE.match(line)
        if not match:
            continue
        slug = slugify_heading(match.group(2))
        if not slug:
            continue
        count = seen.get(slug, 0)
        seen[slug] = count + 1
        anchors.add(slug if count == 0 else f"{slug}-{count}")
    return anchors


def is_external_link(target: str) -> bool:
    return bool(re.match(r"^[a-z][a-z0-9+.-]*:", target)) or target.startswith("#") is False and target.startswith("//")


def split_local_link(target: str) -> tuple[str, str | None]:
    path_part, _, anchor = target.partition("#")
    path_part = unquote(path_part.split("?", 1)[0])
    return path_part, unquote(anchor) if anchor else None


def validate_markdown_links(paths: list[Path], state: CheckState) -> None:
    anchor_cache: dict[Path, set[str]] = {}
    for source in paths:
        text = source.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), start=1):
            for target in MARKDOWN_LINK_RE.findall(line):
                if is_external_link(target):
                    continue
                path_part, anchor = split_local_link(target)
                target_path = (source.parent / path_part).resolve() if path_part else source
                try:
                    target_path.relative_to(ROOT)
                except ValueError:
                    state.fail(f"local markdown link escapes repository: {rel(source)}:{line_number}: {target}")
                    continue
                if not target_path.exists():
                    state.fail(f"broken local markdown link: {rel(source)}:{line_number}: {target}")
                    continue
                if anchor and target_path.suffix == ".md":
                    anchors = anchor_cache.setdefault(target_path, markdown_anchors(target_path))
                    if anchor not in anchors:
                        key = (rel(source), line_number, target)
                        if key in KNOWN_ANCHOR_DRIFT:
                            state.note(f"known anchor drift: {rel(source)}:{line_number}: {target}")
                            continue
                        state.fail(f"broken local markdown anchor: {rel(source)}:{line_number}: {target}")


def validate_manifest(state: CheckState) -> dict:
    manifest = load_json(MANIFEST, state)
    if not isinstance(manifest, dict):
        state.fail("conformance/manifest.json must be a JSON object")
        return {}

    profiles = manifest.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        state.fail("conformance manifest must define profiles")
        return manifest

    conformance_text = CONFORMANCE.read_text(encoding="utf-8")
    profile_ids = set(profiles)
    for profile_id, profile in sorted(profiles.items()):
        if profile_id not in conformance_text:
            state.fail(f"manifest profile id absent from CONFORMANCE.md: {profile_id}")
        if not isinstance(profile, dict):
            state.fail(f"profile must be an object: {profile_id}")
            continue
        for required in require_list(profile.get("requires", []), f"requires for {profile_id}", state):
            if required not in profile_ids:
                state.fail(f"profile {profile_id} requires unknown profile {required}")
        for doc in require_list(profile.get("spec_documents", []), f"spec_documents for {profile_id}", state):
            require_file(doc, state)
        for schema in require_list(profile.get("schemas", []), f"schemas for {profile_id}", state):
            validate_schema_reference(schema, state)
        for vector_ref in require_list(profile.get("test_vectors", []), f"test_vectors for {profile_id}", state):
            validate_vector_reference(vector_ref, state)
        for check in require_list(profile.get("library_checks", []), f"library_checks for {profile_id}", state):
            validate_library_check(check, state)

    for validator in require_list(manifest.get("validators", []), "validators", state):
        if not isinstance(validator, dict) or not validator.get("name") or not validator.get("command"):
            state.fail("validators entries need name and command")

    return manifest


def require_list(value, label: str, state: CheckState) -> list:
    if not isinstance(value, list):
        state.fail(f"{label} must be a list")
        return []
    return value


def require_file(relative_path: str, state: CheckState) -> Path | None:
    if not isinstance(relative_path, str):
        state.fail(f"file reference must be a string: {relative_path!r}")
        return None
    path = ROOT / relative_path
    if not path.is_file():
        state.fail(f"missing local file: {relative_path}")
        return None
    return path


def validate_schema_reference(relative_path: str, state: CheckState) -> None:
    path = require_file(relative_path, state)
    if path is None:
        return
    if not path.name.endswith(".schema.json"):
        state.fail(f"schema reference must end with .schema.json: {relative_path}")
        return
    example_name = path.name.replace(".schema.json", ".json")
    for root in (VALID_EXAMPLES, INVALID_EXAMPLES):
        example = root / example_name
        if not example.is_file():
            state.fail(f"missing schema example for {relative_path}: {rel(example)}")


def validate_all_schema_examples(state: CheckState) -> None:
    for schema in sorted(SCHEMAS.glob("*.schema.json")):
        example_name = schema.name.replace(".schema.json", ".json")
        for root in (VALID_EXAMPLES, INVALID_EXAMPLES):
            example = root / example_name
            if not example.is_file():
                state.fail(f"missing schema example for {rel(schema)}: {rel(example)}")


def validate_vector_reference(vector_ref: object, state: CheckState) -> None:
    if not isinstance(vector_ref, dict):
        state.fail("test_vectors entries must be objects")
        return
    vector_file = vector_ref.get("file")
    vector_path = require_file(vector_file, state)
    sections = require_list(vector_ref.get("sections"), f"test vector sections for {vector_file}", state)
    if vector_path is None:
        return
    data = load_json(vector_path, state)
    if not isinstance(data, dict):
        state.fail(f"test vector file must be a JSON object: {vector_file}")
        return
    for section in sections:
        if section not in data:
            state.fail(f"missing test vector section {section!r} in {vector_file}")


def validate_library_check(check: object, state: CheckState) -> None:
    if not isinstance(check, dict):
        state.fail("library_checks entries must be objects")
        return
    vector_file = check.get("file")
    vector_path = require_file(vector_file, state)
    section = check.get("section")
    if vector_path is None:
        return
    data = load_json(vector_path, state)
    if not isinstance(data, dict):
        return
    if section not in data:
        state.fail(f"missing library check section {section!r} in {vector_file}")
        return
    require_list(check.get("libraries"), f"libraries for {section}", state)


def collect_markdown_refs(manifest: dict) -> list[Path]:
    paths = {CONFORMANCE, ROOT / "test-vectors" / "README.md"}
    paths.update(sorted((ROOT / "docs" / "automation").glob("*.md")))
    profiles = manifest.get("profiles") if isinstance(manifest, dict) else {}
    if isinstance(profiles, dict):
        for profile in profiles.values():
            if not isinstance(profile, dict):
                continue
            for doc in profile.get("spec_documents", []):
                if isinstance(doc, str):
                    path = ROOT / doc
                    if path.exists():
                        paths.add(path)
    return sorted(paths)


def report_info_markers(paths: list[Path], state: CheckState) -> None:
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if INFO_MARKER_RE.search(line):
                state.note(f"info marker: {rel(path)}:{line_number}: {line.strip()}")


def main() -> int:
    state = CheckState()

    for path in iter_json_files():
        load_json(path, state)

    manifest = validate_manifest(state)
    validate_all_schema_examples(state)

    markdown_paths = collect_markdown_refs(manifest)
    validate_markdown_links(markdown_paths, state)
    report_info_markers(markdown_paths, state)

    for message in state.info:
        print(message)

    if state.errors:
        for message in state.errors:
            print(f"ERROR: {message}", file=sys.stderr)
        return 1

    print(
        "spec consistency ok "
        f"({len(iter_json_files())} JSON files, {len(markdown_paths)} markdown refs)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
