#!/usr/bin/env python3
"""Loop 62 — the validator itself, tested in the repo that ships it.

These live in the AUDITED repo, not in the v3.2 harness, for the same reason
Loop 61's coverage tests do: claim C08 measures which modules the baseline's own
test corpus exercises, so a v3.2 test cannot discharge it. `core/schema_validator.py`
is a new baseline module and C08 reported it untested until this file existed.

The complementary half — that all nine shipped schemas conform, and that the
Merkle write path refuses a malformed record — stays in
`focus-gate-v3.2/tests/test_loop62_schema_enforcement.py`, because those tests are
about the claim and the harness, not about the validator's internals.
"""
import json
import os
import re
import sys
import unittest
import uuid
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMAS = os.path.join(ROOT, "schemas")


def load_schema(name):
    with open(os.path.join(SCHEMAS, "%s.schema.json" % name), encoding="utf-8") as fh:
        return json.load(fh)


ALL_SCHEMAS = ["agent-brief", "context-delta", "domain-event", "handoff",
               "receipt", "receipt-bundle", "sft-record", "tombstone",
               "trajectory"]


def _load_validator():
    """Import the validator from THIS repo."""
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    return __import__("core.schema_validator", fromlist=["validate"])


class TestValidatorExists(unittest.TestCase):
    """RED: the module does not exist yet."""

    def test_the_validator_module_imports(self):
        v = _load_validator()
        self.assertTrue(hasattr(v, "validate"),
                        "core/schema_validator.py must expose validate()")

    def test_validate_reports_ok_for_a_valid_instance(self):
        v = _load_validator()
        ok, errs = v.validate({"a": 1}, {"type": "object",
                                         "properties": {"a": {"type": "integer"}}})
        self.assertTrue(ok, "a valid instance was rejected: %s" % (errs,))

    def test_validate_rejects_a_bad_instance_with_a_precise_path(self):
        v = _load_validator()
        ok, errs = v.validate({"gate_id": None},
                              {"type": "object",
                               "properties": {"gate_id": {"type": "string"}}})
        self.assertFalse(ok, "None was accepted where a string is required")
        self.assertTrue(errs, "a rejection must carry a message")
        self.assertRegex(errs[0], r"gate_id",
                         "the message must name the offending field, got %r"
                         % (errs[0],))

    def test_an_error_message_is_path_precise_not_just_top_level(self):
        v = _load_validator()
        ok, errs = v.validate(
            {"outer": {"inner": "wrong"}},
            {"type": "object", "properties": {
                "outer": {"type": "object", "properties": {
                    "inner": {"type": "integer"}}}}})
        self.assertFalse(ok)
        self.assertIn("outer.inner", errs[0],
                      "a nested failure must be reported by full path, got %r"
                      % (errs[0],))


# ---------------------------------------------------------------------------
class TestValidatorCoversExactlyTheKeywordsUsed(unittest.TestCase):
    """The validator must not silently ignore a keyword the schemas use."""

    ASSERTION_KEYWORDS = {"type", "required", "enum", "properties", "items",
                          "additionalProperties", "minimum", "maximum",
                          "minLength", "maxLength", "minItems", "maxItems",
                          "pattern", "format"}
    ANNOTATION_ONLY = {"$schema", "$id", "title", "description", "default",
                       "examples"}

    def test_every_assertion_keyword_in_the_schemas_is_known_to_the_validator(self):
        v = _load_validator()
        used = set()

        def walk(node):
            if isinstance(node, dict):
                for k, sub in node.items():
                    if k in self.ASSERTION_KEYWORDS:
                        used.add(k)
                    walk(sub)
            elif isinstance(node, list):
                for sub in node:
                    walk(sub)

        for name in ALL_SCHEMAS:
            walk(load_schema(name))
        unknown = used - v.SUPPORTED
        self.assertEqual(unknown, set(),
                         "schemas use keywords the validator does not check, so "
                         "they would be enforced only partially: %s" % sorted(unknown))

    def test_the_validator_advertises_exactly_what_it_checks(self):
        """A keyword in SUPPORTED but not in the schemas is dead code; a keyword
        in the schemas but not in SUPPORTED is a silent hole. Both are bugs."""
        v = _load_validator()
        used = set()

        def walk(node):
            if isinstance(node, dict):
                for k, sub in node.items():
                    if k in self.ASSERTION_KEYWORDS:
                        used.add(k)
                    walk(sub)
            elif isinstance(node, list):
                for sub in node:
                    walk(sub)

        for name in ALL_SCHEMAS:
            walk(load_schema(name))
        self.assertEqual(v.SUPPORTED, used,
                         "SUPPORTED and the schemas' keyword set have drifted")

    def test_no_schema_uses_a_keyword_outside_the_known_set(self):
        """If a future schema grows `$ref`/`oneOf`, that is a scope change for
        this loop, not something the validator may quietly skip."""
        for name in ALL_SCHEMAS:
            raw = json.dumps(load_schema(name))
            for kw in ("$ref", "oneOf", "anyOf", "allOf", "not", "dependencies"):
                self.assertNotIn('"%s"' % kw, raw,
                                 "%s uses %r, which this validator does not "
                                 "implement" % (name, kw))

    def test_annotation_keywords_are_not_treated_as_assertions(self):
        v = _load_validator()
        ok, errs = v.validate({"a": 1},
                              {"type": "object", "title": "T", "description": "d",
                               "$schema": "http://json-schema.org/draft-07/schema#",
                               "properties": {"a": {"type": "integer"}}})
        self.assertTrue(ok, errs)


# ---------------------------------------------------------------------------
class TestEachKeywordIsEnforced(unittest.TestCase):
    """One test per keyword. A keyword that cannot fail is not a keyword."""

    def _one_bad(self, schema, instance):
        v = _load_validator()
        ok, errs = v.validate(instance, schema)
        self.assertFalse(ok, "%s should have rejected %r" % (schema, instance))
        return errs

    def test_type_string_rejects_an_integer(self):
        self._one_bad({"type": "string"}, 1)

    def test_type_integer_rejects_a_float_with_a_fraction(self):
        self._one_bad({"type": "integer"}, 1.5)

    def test_type_integer_accepts_a_bool_distinctly(self):
        # bool is a subclass of int in Python; a validator that treats True as 1
        # would accept {"type":"integer"} for True, which no JSON Schema does.
        v = _load_validator()
        ok, _ = v.validate(True, {"type": "integer"})
        self.assertFalse(ok, "a boolean was accepted as an integer")

    def test_type_number_accepts_an_integer(self):
        v = _load_validator()
        ok, errs = v.validate(3, {"type": "number"})
        self.assertTrue(ok, errs)

    def test_a_type_union_accepts_either_member(self):
        v = _load_validator()
        self.assertTrue(v.validate("s", {"type": ["string", "null"]})[0])
        self.assertTrue(v.validate(None, {"type": ["string", "null"]})[0])
        self._one_bad({"type": ["string", "null"]}, 3)

    def test_required_rejects_a_missing_field(self):
        self._one_bad({"type": "object", "required": ["a"]}, {"b": 1})

    def test_required_rejects_a_field_present_but_null(self):
        """A required key set to None is present, but null is not a valid value
        for a typed field. Both facts must hold."""
        self._one_bad({"type": "object", "required": ["a"],
                       "properties": {"a": {"type": "string"}}}, {"a": None})

    def test_enum_rejects_a_value_outside_the_set(self):
        self._one_bad({"type": "string", "enum": ["PASS", "FAIL"]}, "MAYBE")

    def test_enum_accepts_a_listed_value(self):
        v = _load_validator()
        self.assertTrue(v.validate("FAIL", {"type": "string",
                                            "enum": ["PASS", "FAIL"]})[0])

    def test_additional_properties_false_rejects_an_unknown_field(self):
        self._one_bad({"type": "object", "additionalProperties": False,
                       "properties": {"a": {"type": "string"}}}, {"a": "x", "b": 1})

    def test_additional_properties_true_allows_an_unknown_field(self):
        v = _load_validator()
        self.assertTrue(v.validate({"a": "x", "b": 1},
                                   {"type": "object", "additionalProperties": True,
                                    "properties": {"a": {"type": "string"}}})[0])

    def test_items_applies_to_every_array_element(self):
        self._one_bad({"type": "array", "items": {"type": "string"}},
                      ["ok", 2])

    def test_minimum_rejects_a_lower_number(self):
        self._one_bad({"type": "integer", "minimum": 1}, 0)

    def test_maximum_rejects_a_higher_number(self):
        self._one_bad({"type": "integer", "maximum": 10}, 11)

    def test_min_length_rejects_a_shorter_string(self):
        self._one_bad({"type": "string", "minLength": 3}, "ab")

    def test_max_length_rejects_a_longer_string(self):
        self._one_bad({"type": "string", "maxLength": 3}, "abcd")

    def test_min_items_rejects_a_shorter_array(self):
        self._one_bad({"type": "array", "minItems": 2,
                       "items": {"type": "string"}}, ["a"])

    def test_max_items_rejects_a_longer_array(self):
        self._one_bad({"type": "array", "maxItems": 1,
                       "items": {"type": "string"}}, ["a", "b"])

    def test_pattern_rejects_a_non_matching_string(self):
        self._one_bad({"type": "string", "pattern": "^[A-Z]+$"}, "abc")

    def test_format_uuid_rejects_a_non_uuid(self):
        self._one_bad({"type": "string", "format": "uuid"}, "not-a-uuid")

    def test_format_uuid_accepts_a_real_uuid(self):
        v = _load_validator()
        self.assertTrue(v.validate(str(uuid.uuid4()),
                                   {"type": "string", "format": "uuid"})[0])

    def test_format_date_time_rejects_a_non_timestamp(self):
        self._one_bad({"type": "string", "format": "date-time"}, "yesterday")

    def test_format_date_time_accepts_an_iso_timestamp(self):
        v = _load_validator()
        self.assertTrue(v.validate(datetime.now(timezone.utc).isoformat(),
                                   {"type": "string", "format": "date-time"})[0])

    def test_an_unknown_format_is_ignored_rather_than_guessed(self):
        """Silently enforcing an unimplemented format would reject valid data;
        silently ignoring a KNOWN one would pass invalid data. The first is the
        lesser evil, and it must be explicit."""
        v = _load_validator()
        ok, errs = v.validate("whatever", {"type": "string", "format": "email"})
        self.assertTrue(ok, "an unknown format must not reject: %s" % (errs,))


# ---------------------------------------------------------------------------
class TestNestedSchemas(unittest.TestCase):
    """`handoff.schema.json` nests a full receipt schema inside a property."""

    def test_a_nested_object_is_validated(self):
        v = _load_validator()
        schema = {"type": "object", "properties": {
            "receipt": {"type": "object",
                        "required": ["gate_id"],
                        "properties": {"gate_id": {"type": "string"}}}}}
        self.assertTrue(v.validate({"receipt": {"gate_id": "G1"}}, schema)[0])
        ok, errs = v.validate({"receipt": {"gate_id": 7}}, schema)
        self.assertFalse(ok)
        self.assertIn("receipt.gate_id", errs[0])

    def test_a_nested_array_of_objects_is_validated(self):
        v = _load_validator()
        schema = {"type": "object", "properties": {
            "items": {"type": "array", "items": {
                "type": "object", "required": ["id"],
                "properties": {"id": {"type": "string"}}}}}}
        self.assertTrue(v.validate({"items": [{"id": "a"}]}, schema)[0])
        ok, errs = v.validate({"items": [{"id": 1}]}, schema)
        self.assertFalse(ok)
        self.assertIn("items[0].id", errs[0])

    def test_error_paths_use_bracket_index_for_array_elements(self):
        v = _load_validator()
        schema = {"type": "array", "items": {"type": "object", "required": ["id"],
                                              "properties": {"id": {"type": "string"}}}}
        ok, errs = v.validate([{"id": "a"}, {"id": 2}], schema)
        self.assertFalse(ok)
        self.assertIn("[1].id", errs[0], "got %r" % (errs[0],))

    def test_a_top_level_array_reports_a_bare_index_path(self):
        v = _load_validator()
        ok, errs = v.validate([1, 2], {"type": "array",
                                       "items": {"type": "string"}})
        self.assertFalse(ok)
        self.assertIn("[0]", errs[0])


# ---------------------------------------------------------------------------


if __name__ == "__main__":
    unittest.main(verbosity=2)
