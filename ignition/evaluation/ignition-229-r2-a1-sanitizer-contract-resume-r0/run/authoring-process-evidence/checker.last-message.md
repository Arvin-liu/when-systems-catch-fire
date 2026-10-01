```python
# checker.py
"""Independent, standard-library-only Task229 R2-A1 packet checker."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys


class CheckFailure(Exception):
    pass


def fail(code):
    raise CheckFailure(code)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def read_bytes(name):
    root = Path.cwd().resolve()
    path = Path(name).resolve()
    if not path.is_relative_to(root):
        fail("FAIL_INPUT_PATH")
    try:
        return path.read_bytes()
    except OSError:
        fail("FAIL_INPUT_READ")


def decode(data):
    try:
        text = data.decode("utf-8", errors="strict")
        if text.encode("utf-8", errors="strict") != data:
            fail("FAIL_UTF8_ROUNDTRIP")
        return text
    except UnicodeError:
        fail("FAIL_UTF8")


def object_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            fail("FAIL_DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def reject_constant(_):
    fail("FAIL_NONFINITE_JSON_NUMBER")


def check_unicode(value):
    if isinstance(value, str):
        try:
            value.encode("utf-8", errors="strict")
        except UnicodeError:
            fail("FAIL_UTF8")
    elif isinstance(value, float):
        if not math.isfinite(value):
            fail("FAIL_NONFINITE_JSON_NUMBER")
    elif isinstance(value, dict):
        for key, item in value.items():
            check_unicode(key)
            check_unicode(item)
    elif isinstance(value, list):
        for item in value:
            check_unicode(item)


def parse_json(data):
    try:
        value = json.loads(
            decode(data),
            object_pairs_hook=object_pairs,
            parse_constant=reject_constant,
        )
    except (ValueError, OverflowError):
        fail("FAIL_JSON")
    check_unicode(value)
    return value


def canonical_bytes(value):
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def canonical_key(key):
    return key.lower().replace("-", "_")


def load_contract(path):
    raw = read_bytes(path)
    contract = parse_json(raw)
    if not isinstance(contract, dict):
        fail("FAIL_CONTRACT")

    rules = contract.get("key_canonicalization")
    if rules != {
        "no_other_transforms": True,
        "operations_in_order": [
            "lowercase",
            "replace_hyphen_with_underscore",
        ],
        "scope": "object_keys_only",
    }:
        fail("FAIL_UNSUPPORTED_CANONICALIZATION")

    policy = contract.get("unlisted_key_policy")
    if not isinstance(policy, dict) or (
        policy.get("preserve_before_schema_validation") is not True
        or policy.get("schema_invalid_survivor") != "fail_closed"
    ):
        fail("FAIL_CONTRACT")

    arrays = []
    for field in (
        "whole_object_removal_canonical_keys",
        "exact_metadata_removal_canonical_keys",
    ):
        keys = contract.get(field)
        if (
            not isinstance(keys, list)
            or any(
                not isinstance(key, str)
                or not key
                or canonical_key(key) != key
                for key in keys
            )
            or len(keys) != len(set(keys))
        ):
            fail("FAIL_CONTRACT")
        arrays.append(keys)

    report = {
        "metadata_key_contract_sha256": sha256(raw),
        "key_canonicalization": rules,
        "whole_object_removal_canonical_keys": arrays[0],
        "exact_metadata_removal_canonical_keys": arrays[1],
    }
    return set(arrays[0]) | set(arrays[1]), report


def remove_keys(value, removal_keys):
    if isinstance(value, dict):
        return {
            key: remove_keys(item, removal_keys)
            for key, item in value.items()
            if canonical_key(key) not in removal_keys
        }
    if isinstance(value, list):
        return [remove_keys(item, removal_keys) for item in value]
    return value


def contains_removal_key(value, removal_keys):
    if isinstance(value, dict):
        return any(
            canonical_key(key) in removal_keys
            or contains_removal_key(item, removal_keys)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(contains_removal_key(item, removal_keys) for item in value)
    return False


def json_equal(left, right):
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left == right
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            json_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            json_equal(a, b) for a, b in zip(left, right)
        )
    return left == right


class SchemaFailure(Exception):
    def __init__(self, unknown=False):
        self.unknown = unknown


def schema_error(unknown=False):
    raise SchemaFailure(unknown)


def type_matches(value, name):
    predicates = {
        "object": lambda: isinstance(value, dict),
        "array": lambda: isinstance(value, list),
        "string": lambda: isinstance(value, str),
        "null": lambda: value is None,
        "boolean": lambda: type(value) is bool,
        "number": lambda: type(value) in (int, float),
        "integer": lambda: type(value) is int
        or (type(value) is float and value.is_integer()),
    }
    if name not in predicates:
        fail("FAIL_UNSUPPORTED_SCHEMA")
    return predicates[name]()


def validate(value, schema, root):
    """Validate the vocabulary used by the frozen schemas; fail on others."""
    if schema is True:
        return
    if schema is False:
        schema_error()
    if not isinstance(schema, dict):
        fail("FAIL_SCHEMA_DOCUMENT")

    supported = {
        "$schema", "$id", "$defs", "$ref", "title", "description",
        "type", "const", "enum", "oneOf", "properties", "required",
        "additionalProperties", "items", "minItems", "maxItems",
        "uniqueItems", "minLength",
    }
    if set(schema) - supported:
        fail("FAIL_UNSUPPORTED_SCHEMA")

    if "$ref" in schema:
        ref = schema["$ref"]
        if not isinstance(ref, str) or not ref.startswith("#/"):
            fail("FAIL_UNSUPPORTED_SCHEMA_REFERENCE")
        target = root
        try:
            for part in ref[2:].split("/"):
                target = target[part.replace("~1", "/").replace("~0", "~")]
        except (KeyError, TypeError):
            fail("FAIL_SCHEMA_DOCUMENT")
        validate(value, target, root)

    if "oneOf" in schema:
        branches = schema["oneOf"]
        if not isinstance(branches, list):
            fail("FAIL_SCHEMA_DOCUMENT")
        successes = 0
        errors = []
        for branch in branches:
            try:
                validate(value, branch, root)
                successes += 1
            except SchemaFailure as exc:
                errors.append(exc)
        if successes != 1:
            schema_error(
                successes == 0 and any(error.unknown for error in errors)
            )

    if "type" in schema:
        kinds = schema["type"]
        if isinstance(kinds, str):
            kinds = [kinds]
        if not isinstance(kinds, list):
            fail("FAIL_SCHEMA_DOCUMENT")
        if not any(type_matches(value, kind) for kind in kinds):
            schema_error()

    if "const" in schema and not json_equal(value, schema["const"]):
        schema_error()
    if "enum" in schema and not any(
        json_equal(value, item) for item in schema["enum"]
    ):
        schema_error()

    if isinstance(value, dict):
        properties = schema.get("properties", {})
        if not isinstance(properties, dict):
            fail("FAIL_SCHEMA_DOCUMENT")
        extras = set(value) - set(properties)
        additional = schema.get("additionalProperties", True)
        if extras and additional is False:
            schema_error(unknown=True)
        if any(key not in value for key in schema.get("required", [])):
            schema_error()
        for key, item in value.items():
            if key in properties:
                validate(item, properties[key], root)
            elif isinstance(additional, dict):
                validate(item, additional, root)

    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            schema_error()
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            schema_error()
        if schema.get("uniqueItems", False):
            for index, item in enumerate(value):
                if any(json_equal(item, earlier) for earlier in value[:index]):
                    schema_error()
        if "items" in schema:
            for item in value:
                validate(item, schema["items"], root)

    if isinstance(value, str) and len(value) < schema.get("minLength", 0):
        schema_error()


def load_tokens(path):
    manifest = parse_json(read_bytes(path))
    if not isinstance(manifest, dict):
        fail("FAIL_DENY_MANIFEST")
    tokens = manifest.get("literal_tokens")
    if not isinstance(tokens, list) or any(
        not isinstance(token, str) or not token for token in tokens
    ):
        fail("FAIL_DENY_MANIFEST")
    return sorted(set(tokens), key=lambda token: (-len(token), token))


def redact(value, tokens):
    if isinstance(value, str):
        for token in tokens:
            value = value.replace(token, "[REDACTED]")
        return value
    if isinstance(value, list):
        return [redact(item, tokens) for item in value]
    if isinstance(value, dict):
        return {key: redact(item, tokens) for key, item in value.items()}
    return value


def has_literal_token(value, tokens):
    if isinstance(value, str):
        return any(token in value for token in tokens)
    if isinstance(value, dict):
        return any(
            has_literal_token(key, tokens) or has_literal_token(item, tokens)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(has_literal_token(item, tokens) for item in value)
    return False


def verify(args):
    removal_keys, _ = load_contract(args.metadata_key_contract)
    envelope = parse_json(read_bytes(args.response))
    schema = parse_json(read_bytes(args.response_schema))
    tokens = load_tokens(args.deny_token_manifest)
    case_bytes = read_bytes(args.case)
    criteria_bytes = read_bytes(args.criteria)
    case_text = decode(case_bytes)
    criteria_text = decode(criteria_bytes)
    packet_bytes = read_bytes(args.packet)
    candidate = parse_json(packet_bytes)

    sanitized = remove_keys(envelope, removal_keys)
    try:
        validate(sanitized, schema, schema)
    except SchemaFailure as exc:
        if exc.unknown:
            fail("FAIL_SCHEMA_INVALID_SURVIVING_UNLISTED_KEY")
        fail("FAIL_SCHEMA_INVALID")

    if not isinstance(sanitized, dict):
        fail("FAIL_SCHEMA_INVALID")
    responses = sanitized.get("responses")
    if not isinstance(responses, list):
        fail("FAIL_SCHEMA_INVALID")
    matches = [
        response for response in responses
        if isinstance(response, dict) and response.get("case_id") == args.case_id
    ]
    if len(matches) != 1:
        fail("FAIL_CASE_SELECTION")
    if not args.response_id:
        fail("FAIL_RESPONSE_ID")

    expected = {
        "schema_version": "task229-r2-blind-packet-v1",
        "response_id": args.response_id,
        "case_id": args.case_id,
        "case_text": case_text,
        "case_sha256": sha256(case_bytes),
        "criteria_text": criteria_text,
        "criteria_sha256": sha256(criteria_bytes),
        "response": redact(matches[0], tokens),
    }
    if contains_removal_key(candidate, removal_keys):
        fail("FAIL_REMOVABLE_KEY_SURVIVES")
    if not json_equal(candidate, expected):
        fail("FAIL_PACKET_MISMATCH")

    expected_bytes = canonical_bytes(expected)
    if packet_bytes != expected_bytes:
        fail("FAIL_NONCANONICAL_PACKET")

    serialized = decode(packet_bytes)
    if (
        any(token in serialized for token in tokens)
        or has_literal_token(candidate, tokens)
    ):
        fail("FAIL_DENY_TOKEN_LEAK")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Independently verify a Task229 R2-A1 blind packet."
    )
    parser.add_argument("--contract-report", metavar="PATH")
    parser.add_argument("--response", metavar="PATH")
    parser.add_argument("--case-id", choices=("A", "B", "C"))
    parser.add_argument("--response-id")
    parser.add_argument("--case", metavar="PATH")
    parser.add_argument("--criteria", metavar="PATH")
    parser.add_argument("--deny-token-manifest", metavar="PATH")
    parser.add_argument("--response-schema", metavar="PATH")
    parser.add_argument("--metadata-key-contract", metavar="PATH")
    parser.add_argument("--packet", metavar="PATH")
    args = parser.parse_args(argv)

    verification_fields = (
        "response", "case_id", "response_id", "case", "criteria",
        "deny_token_manifest", "response_schema", "metadata_key_contract",
        "packet",
    )
    if args.contract_report is not None:
        if any(getattr(args, field) is not None for field in verification_fields):
            parser.error("--contract-report must be used alone")
    elif any(getattr(args, field) is None for field in verification_fields):
        parser.error("all verification options are required")

    try:
        if args.contract_report is not None:
            _, report = load_contract(args.contract_report)
            sys.stdout.buffer.write(canonical_bytes(report))
        else:
            verify(args)
            print("PASS")
        return 0
    except CheckFailure as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (
        OSError, UnicodeError, ValueError, TypeError, KeyError,
        OverflowError, RecursionError,
    ):
        print("FAIL_INVALID_INPUT", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
```