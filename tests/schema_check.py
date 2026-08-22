"""A minimal, dependency-free JSON Schema (Draft 2020-12 subset) checker.

This project has no external dependencies (no pyproject.toml/requirements —
CI runs pure stdlib `python -m unittest discover`). Testing schemas/*.json
directly still matters: the schema is what an editor and a future author
actually see, and the erratum v2 shape is intricate enough (oneOf branches,
if/then conditionals, cross-file $ref) that a typo in it should fail a test,
not wait to be noticed by a human reading JSON.

Supports exactly the keywords schemas/*.json actually use: type, enum,
const, required, properties, additionalProperties (bool or schema),
propertyNames, minProperties, items, minItems, uniqueItems, pattern,
minLength, minimum, maximum, oneOf, allOf, if/then/else, and $ref
(same-document `#/$defs/...` and cross-file `other.schema.json#/$defs/...`).
This is not a general-purpose validator — it does not implement every
Draft 2020-12 keyword, only the ones exercised here.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = REPO_ROOT / "schemas"

_TYPE_MAP = {
    "object": dict,
    "array": list,
    "string": str,
    "boolean": bool,
    "null": type(None),
}


def _matches_type(instance: Any, type_name: str) -> bool:
    if type_name == "integer":
        return isinstance(instance, int) and not isinstance(instance, bool)
    if type_name == "number":
        return isinstance(instance, (int, float)) and not isinstance(instance, bool)
    py_type = _TYPE_MAP[type_name]
    if type_name == "boolean":
        return isinstance(instance, bool)
    return isinstance(instance, py_type)


def _check_type(instance: Any, type_spec) -> bool:
    if isinstance(type_spec, list):
        return any(_matches_type(instance, t) for t in type_spec)
    return _matches_type(instance, type_spec)


def _has_duplicates(items: list) -> bool:
    seen: list = []
    for item in items:
        if item in seen:
            return True
        seen.append(item)
    return False


class Registry:
    """Loads every schemas/*.json file, keyed by filename, for $ref resolution."""

    def __init__(self, schemas_dir: Path = SCHEMAS_DIR):
        self.docs: dict[str, dict] = {}
        for path in schemas_dir.glob("*.json"):
            self.docs[path.name] = json.loads(path.read_text(encoding="utf-8"))

    def root(self, filename: str = "erratum.schema.json") -> dict:
        return self.docs[filename]

    def resolve(self, ref: str, current_doc: dict) -> tuple[dict, dict]:
        """Return (target_schema, doc_it_lives_in) for a $ref string."""
        if ref.startswith("#"):
            doc = current_doc
            pointer = ref[1:]
        else:
            file_part, _, pointer = ref.partition("#")
            doc = self.docs[file_part]
        node = doc
        for part in pointer.strip("/").split("/"):
            if part == "":
                continue
            part = part.replace("~1", "/").replace("~0", "~")
            node = node[part]
        return node, doc


def validate(
    schema: dict,
    instance: Any,
    registry: Registry,
    doc: dict,
    path: str = "$",
) -> list[str]:
    """Return a list of human-readable error strings; empty means valid."""
    errors: list[str] = []

    if "$ref" in schema:
        target, target_doc = registry.resolve(schema["$ref"], doc)
        return validate(target, instance, registry, target_doc, path)

    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: expected const {schema['const']!r}, got {instance!r}")

    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: {instance!r} not in enum {schema['enum']}")

    if "type" in schema and not _check_type(instance, schema["type"]):
        errors.append(f"{path}: expected type {schema['type']}, got {type(instance).__name__}")

    if isinstance(instance, str):
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            errors.append(f"{path}: {instance!r} does not match pattern {schema['pattern']!r}")
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append(f"{path}: shorter than minLength {schema['minLength']}")

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path}: {instance} below minimum {schema['minimum']}")
        if "maximum" in schema and instance > schema["maximum"]:
            errors.append(f"{path}: {instance} above maximum {schema['maximum']}")

    if isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                errors.append(f"{path}: missing required property {key!r}")
        properties = schema.get("properties", {})
        for key, value in instance.items():
            if key in properties:
                errors.extend(validate(properties[key], value, registry, doc, f"{path}.{key}"))
        additional = schema.get("additionalProperties", True)
        extra_keys = [k for k in instance if k not in properties]
        if additional is False:
            if extra_keys:
                errors.append(f"{path}: additional properties not allowed: {extra_keys}")
        elif isinstance(additional, dict):
            for key in extra_keys:
                errors.extend(validate(additional, instance[key], registry, doc, f"{path}.{key}"))
        if "propertyNames" in schema:
            for key in instance:
                errors.extend(validate(schema["propertyNames"], key, registry, doc, f"{path}.<key:{key}>"))
        if "minProperties" in schema and len(instance) < schema["minProperties"]:
            errors.append(f"{path}: fewer than minProperties {schema['minProperties']}")

    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            errors.append(f"{path}: fewer than minItems {schema['minItems']}")
        if schema.get("uniqueItems") and _has_duplicates(instance):
            errors.append(f"{path}: items are not unique")
        if "items" in schema:
            for i, item in enumerate(instance):
                errors.extend(validate(schema["items"], item, registry, doc, f"{path}[{i}]"))

    if "oneOf" in schema:
        branch_results = [
            validate(sub, instance, registry, doc, f"{path}(oneOf[{i}])")
            for i, sub in enumerate(schema["oneOf"])
        ]
        matches = [i for i, errs in enumerate(branch_results) if not errs]
        if len(matches) != 1:
            detail = "; ".join(
                f"branch {i}: {branch_results[i][:2]}"
                for i in range(len(branch_results))
            )
            errors.append(
                f"{path}: expected exactly 1 oneOf branch to match, got {len(matches)} ({detail})"
            )

    for sub in schema.get("allOf", []):
        errors.extend(validate(sub, instance, registry, doc, path))

    if "if" in schema:
        if not validate(schema["if"], instance, registry, doc, path):
            if "then" in schema:
                errors.extend(validate(schema["then"], instance, registry, doc, path))
        elif "else" in schema:
            errors.extend(validate(schema["else"], instance, registry, doc, path))

    return errors


def validate_erratum(instance: dict, registry: Registry | None = None) -> list[str]:
    """Validate one erratum record against schemas/erratum.schema.json."""
    registry = registry or Registry()
    root = registry.root("erratum.schema.json")
    return validate(root, instance, registry, root)
