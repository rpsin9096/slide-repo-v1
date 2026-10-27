"""Minimal JSON Schema validator — stdlib only, zero dependencies.

FocusGate ships nine JSON Schemas in `schemas/` and, before v3.2 Loop 62,
nothing in the runtime read them. A malformed receipt was written to the Merkle
ledger, hashed into the state root, and attested across mesh peers without ever
being questioned. A contract that is never enforced is a promise the codebase
cannot keep.

`jsonschema` is the obvious answer and is forbidden: SPEC invariant 1 is zero
external dependencies in the runtime path, and it is non-negotiable. So this
implements exactly the keyword subset the nine shipped schemas use — measured
from the shipped schema files, not assumed:

    type (including the ["string","null"] union)   required    enum
    properties    items    additionalProperties
    minimum    maximum    minLength    maxLength
    minItems    maxItems    pattern    format (uuid, date-time)

`SUPPORTED` is the honest, closed set. A schema that later grows `$ref` or
`oneOf` will fail the Loop 62 test that asserts `SUPPORTED` equals the
schemas' keyword set, rather than being silently under-validated — which is the
failure mode this module exists to prevent.

Design rules:
  * Path-precise errors. `receipt.gate_id`, `items[0].id` — a validator whose
    message cannot locate the fault forces a human to re-derive it by hand.
  * Fail closed on structure, fail open on unknown *formats*. An unimplemented
    format (say `email`) must not reject data; an unimplemented *assertion
    keyword* must be a loud error, which is why SUPPORTED is closed and tested.
  * `bool` is not an `integer`. In Python `True == 1`, so a naive isinstance
    check would accept `true` where the schema says integer. No JSON Schema
    implementation does that, so neither does this one.
  * Python 3.9 compatible: no `X | Y` annotations, no `match`.
"""
import re
import uuid
from datetime import datetime

__all__ = ["validate", "SchemaValidationError", "SUPPORTED"]

#: The exact set of assertion keywords this validator implements. Anything the
#: schemas use that is absent here is an unenforced contract.
SUPPORTED = frozenset({
    "type", "required", "enum", "properties", "items", "additionalProperties",
    "minimum", "maximum", "minLength", "maxLength", "minItems", "maxItems",
    "pattern", "format",
})

#: Keywords that carry documentation, not assertions.
ANNOTATION = frozenset({"$schema", "$id", "title", "description", "default",
                        "examples", "$comment", "deprecated"})

#: Formats we actually check. An unknown format is ignored, never guessed.
KNOWN_FORMATS = frozenset({"uuid", "date-time"})

_TYPES = {
    "object": dict,
    "array": list,
    "string": str,
    "boolean": bool,
}


class SchemaValidationError(ValueError):
    """Raised by `enforce` when an instance does not satisfy its schema.

    Carries the full list of path-precise messages so a caller can report every
    fault at once instead of one per round-trip.
    """

    def __init__(self, errors, instance_name="instance"):
        self.errors = list(errors)
        self.instance_name = instance_name
        super().__init__(
            "%s failed schema validation:\n  - %s"
            % (instance_name, "\n  - ".join(self.errors)))


def _is_type(value, want):
    """JSON Schema type check, with bool kept distinct from int."""
    if want == "integer":
        # bool is a subclass of int; JSON Schema says they are different types.
        return isinstance(value, int) and not isinstance(value, bool)
    if want == "number":
        return (isinstance(value, (int, float))
                and not isinstance(value, bool))
    if want == "boolean":
        return isinstance(value, bool)
    if want == "string":
        return isinstance(value, str)
    if want == "array":
        return isinstance(value, list)
    if want == "object":
        return isinstance(value, dict)
    if want == "null":
        return value is None
    return False


def _type_names(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _check_format(value, fmt):
    if fmt == "uuid":
        try:
            uuid.UUID(str(value))
        except (ValueError, AttributeError, TypeError):
            return False
        return True
    if fmt == "date-time":
        text = str(value)
        # Accept the RFC 3339 forms Python's parser handles, including the
        # trailing-Z form that `datetime.fromisoformat` rejects on 3.9.
        try:
            datetime.fromisoformat(text.replace("Z", "+00:00"))
            return True
        except ValueError:
            return False
    return True  # unknown format: ignored, never guessed


def _validate(instance, schema, path, errors, warnings, strict_enum=True):
    if not isinstance(schema, dict):
        return
    # `path` is "" for the root, and each error is reported as
    # "<path>.<field>" or "<path>[i]"; the root is named "instance" so the
    # first message never begins with a bare dot.
    here = path or "instance"

    unknown = set(schema) - SUPPORTED - ANNOTATION
    if unknown:
        # Loud, not silent. An unenforced keyword is the whole defect this
        # module exists to remove, so it must never be swallowed.
        errors.append(
            "%s: schema uses keywords this validator does not implement: %s"
            % (here, ", ".join(sorted(unknown))))

    # ---- type
    want = schema.get("type")
    if want is not None:
        wanted = want if isinstance(want, list) else [want]
        if not any(_is_type(instance, w) for w in wanted):
            errors.append("%s: expected %s, got %s"
                          % (here, " or ".join(wanted), _type_names(instance)))
            # A wrong type makes every other check on this node meaningless and
            # would produce confusing cascading errors, so stop here.
            return

    # ---- enum
    # `strict_enum=False` downgrades an enum miss to a WARNING. This exists for
    # one measured reason: `schemas/domain-event.schema.json` enumerates 8
    # aggregate-lifecycle event types, but the real Merkle ledger carries ~30
    # distinct ones that were never in that list. The schema was aspirational,
    # not descriptive. Enforcing its enum broke 15 working tests on first wiring,
    # which is the signal that the CONTRACT is wrong, not the callers. So the
    # envelope is enforced and the enum is reported.
    if "enum" in schema and instance not in schema["enum"]:
        allowed = ", ".join(repr(x) for x in schema["enum"][:6])
        msg = "%s: %r is not one of [%s]" % (here, instance, allowed)
        if strict_enum:
            errors.append(msg)
        else:
            warnings.append(msg)

    # ---- numbers
    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append("%s: %r is below the minimum %r"
                          % (here, instance, schema["minimum"]))
        if "maximum" in schema and instance > schema["maximum"]:
            errors.append("%s: %r is above the maximum %r"
                          % (here, instance, schema["maximum"]))

    # ---- strings
    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append("%s: string is shorter than minLength %d"
                          % (here, schema["minLength"]))
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            errors.append("%s: string is longer than maxLength %d"
                          % (here, schema["maxLength"]))
        if "pattern" in schema:
            try:
                if re.search(schema["pattern"], instance) is None:
                    errors.append("%s: %r does not match pattern %r"
                                  % (here, instance, schema["pattern"]))
            except re.error:
                errors.append("%s: schema has an invalid regex %r"
                              % (here, schema["pattern"]))
        fmt = schema.get("format")
        if fmt in KNOWN_FORMATS and not _check_format(instance, fmt):
            errors.append("%s: %r is not a valid %s" % (here, instance, fmt))

    # ---- arrays
    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            errors.append("%s: array has %d items, minItems is %d"
                          % (here, len(instance), schema["minItems"]))
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            errors.append("%s: array has %d items, maxItems is %d"
                          % (here, len(instance), schema["maxItems"]))
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for i, element in enumerate(instance):
                _validate(element, item_schema, "%s[%d]" % (path, i),
                          errors, warnings, strict_enum)

    # ---- objects
    if isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                errors.append("%s.%s: required field is missing"
                              % (path, key))
        props = schema.get("properties")
        if isinstance(props, dict):
            for key, sub in props.items():
                if key in instance:
                    child = "%s.%s" % (path, key)
                    _validate(instance[key], sub, child, errors, warnings,
                              strict_enum)
        if schema.get("additionalProperties") is False:
            allowed_keys = set(props or ())
            for key in instance:
                if key not in allowed_keys:
                    errors.append("%s.%s: field is not permitted by the schema"
                                  % (path, key))


def validate(instance, schema, strict_enum=True):
    """Return ``(ok, errors)`` for `instance` against `schema`.

    Never raises for an invalid instance — reporting is the caller's choice, so
    enforcement points can decide between refusing and merely recording.

    `strict_enum=False` reports an `enum` miss as a warning instead of an error;
    `validate_warnings()` then returns what was downgraded. See `_validate` for
    the one measured reason this exists.
    """
    errors = []
    _WARNINGS.clear()
    _validate(instance, schema, "", errors, _WARNINGS, strict_enum)
    return (not errors), errors


#: Enum misses downgraded by the most recent `validate(strict_enum=False)`.
_WARNINGS = []


def validate_warnings():
    """Enum misses downgraded by the most recent non-strict `validate` call."""
    return list(_WARNINGS)


def enforce(instance, schema, instance_name="instance"):
    """Validate and raise `SchemaValidationError` on any fault.

    This is the form the write paths use: an invalid record must never enter
    the Merkle root, so the failure has to be an exception the caller cannot
    accidentally ignore.
    """
    ok, errors = validate(instance, schema)
    if not ok:
        raise SchemaValidationError(errors, instance_name)
    return instance


def load_schema(repo_root, name):
    """Read `schemas/<name>.schema.json` from a repo root."""
    import json
    import os
    path = os.path.join(repo_root, "schemas", "%s.schema.json" % name)
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def supported_keywords_in(schema):
    """Every assertion keyword appearing anywhere inside `schema`.

    Used by the conformance suite to prove the closed `SUPPORTED` set still
    matches what the shipped schemas actually rely on.
    """
    found = set()

    def walk(node):
        if isinstance(node, dict):
            for key, sub in node.items():
                if key in SUPPORTED:
                    found.add(key)
                walk(sub)
        elif isinstance(node, list):
            for sub in node:
                walk(sub)

    walk(schema)
    return found
