```python
# builder.py
"""Deterministic, contract-driven Task229 R2-A1 packet builder."""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import tempfile


class InvalidInput(Exception):
    pass


def require(condition, code):
    if not condition:
        raise InvalidInput(code)


def strict_text(raw):
    text = raw.decode("utf-8", errors="strict")
    require(text.encode("utf-8", errors="strict") == raw, "INVALID_UTF8")
    return text


def reject_constant(_):
    raise InvalidInput("INVALID_JSON_NUMBER")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def check_json_values(value):
    if isinstance(value, str):
        value.encode("utf-8", errors="strict")
    elif isinstance(value, float):
        require(math.isfinite(value), "INVALID_JSON_NUMBER")
    elif isinstance(value, list):
        for child in value:
            check_json_values(child)
    elif isinstance(value, dict):
        for key, child in value.items():
            key.encode("utf-8", errors="strict")
            check_json_values(child)


def parse_json(raw):
    value = json.loads(
        strict_text(raw),
        object_pairs_hook=unique_object,
        parse_constant=reject_constant,
    )
    check_json_values(value)
    return value


def read_json(path):
    raw = Path(path).read_bytes()
    return raw, parse_json(raw)


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
    ).encode("utf-8", errors="strict")


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical_key(key, operations):
    for operation in operations:
        if operation == "lowercase":
            key = key.lower()
        elif operation == "replace_hyphen_with_underscore":
            key = key.replace("-", "_")
        else:
            raise InvalidInput("UNSUPPORTED_CANONICALIZATION")
    return key


def load_contract(path):
    raw, contract = read_json(path)
    require(isinstance(contract, dict), "INVALID_CONTRACT")
    require(
        set(contract) == {
            "schema_version",
            "key_canonicalization",
            "whole_object_removal_canonical_keys",
            "exact_metadata_removal_canonical_keys",
            "unlisted_key_policy",
        },
        "INVALID_CONTRACT",
    )
    require(
        contract["schema_version"] == "task229-r2-a1-metadata-key-contract-v1",
        "INVALID_CONTRACT_VERSION",
    )
    rules = contract["key_canonicalization"]
    require(
        rules == {
            "scope": "object_keys_only",
            "no_other_transforms": True,
            "operations_in_order": [
                "lowercase",
                "replace_hyphen_with_underscore",
            ],
        },
        "UNSUPPORTED_CANONICALIZATION",
    )
    require(
        contract["unlisted_key_policy"] == {
            "preserve_before_schema_validation": True,
            "schema_invalid_survivor": "fail_closed",
            "schema_source": "original_frozen_response_schema.json",
        },
        "INVALID_CONTRACT",
    )
    operations = rules["operations_in_order"]
    for field in (
        "whole_object_removal_canonical_keys",
        "exact_metadata_removal_canonical_keys",
    ):
        keys = contract[field]
        require(isinstance(keys, list), "INVALID_CONTRACT")
        require(
            all(
                isinstance(key, str)
                and bool(key)
                and canonical_key(key, operations) == key
                for key in keys
            ),
            "INVALID_CONTRACT",
        )
        require(len(set(keys)) == len(keys), "INVALID_CONTRACT")
    return raw, contract


def sanitize(value, contract):
    operations = contract["key_canonicalization"]["operations_in_order"]
    whole = set(contract["whole_object_removal_canonical_keys"])
    metadata = set(contract["exact_metadata_removal_canonical_keys"])

    def walk(node):
        if isinstance(node, dict):
            result = {}
            for key, child in node.items():
                canonical = canonical_key(key, operations)
                if canonical in whole:
                    continue
                if canonical in metadata:
                    continue
                result[key] = walk(child)
            return result
        if isinstance(node, list):
            return [walk(child) for child in node]
        return node

    return walk(value)


def json_equal(left, right):
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left == right
    if type(left) is not type(right):
        return False
    if isinstance(left, list):
        return len(left) == len(right) and all(
            json_equal(a, b) for a, b in zip(left, right)
        )
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            json_equal(left[key], right[key]) for key in left
        )
    return left == right


def matches_type(value, name):
    predicates = {
        "object": lambda: isinstance(value, dict),
        "array": lambda: isinstance(value, list),
        "string": lambda: isinstance(value, str),
        "null": lambda: value is None,
        "boolean": lambda: type(value) is bool,
        "number": lambda: type(value) in (int, float),
        "integer": lambda: (
            type(value) is int
            or (type(value) is float and value.is_integer())
        ),
    }
    require(name in predicates, "UNSUPPORTED_SCHEMA")
    return predicates[name]()


def validate(value, schema, root):
    """Implement every validation keyword used by the frozen response schema."""
    if isinstance(schema, bool):
        require(schema, "SCHEMA_INVALID")
        return
    require(isinstance(schema, dict), "INVALID_SCHEMA")
    supported = {
        "$schema", "$id", "title", "$defs", "$ref", "type", "const", "enum",
        "oneOf", "additionalProperties", "required", "properties",
        "minItems", "maxItems", "items", "uniqueItems", "minLength",
    }
    require(set(schema) <= supported, "UNSUPPORTED_SCHEMA")

    if "$ref" in schema:
        reference = schema["$ref"]
        require(
            isinstance(reference, str) and reference.startswith("#/"),
            "UNSUPPORTED_SCHEMA_REFERENCE",
        )
        target = root
        for part in reference[2:].split("/"):
            part = part.replace("~1", "/").replace("~0", "~")
            require(
                isinstance(target, dict) and part in target,
                "INVALID_SCHEMA_REFERENCE",
            )
            target = target[part]
        validate(value, target, root)

    if "oneOf" in schema:
        branches = schema["oneOf"]
        require(isinstance(branches, list) and bool(branches), "INVALID_SCHEMA")
        count = 0
        for branch in branches:
            try:
                validate(value, branch, root)
            except InvalidInput as error:
                if str(error) != "SCHEMA_INVALID":
                    raise
            else:
                count += 1
        require(count == 1, "SCHEMA_INVALID")

    if "type" in schema:
        types = schema["type"]
        if isinstance(types, str):
            types = [types]
        require(
            isinstance(types, list)
            and bool(types)
            and all(isinstance(item, str) for item in types),
            "INVALID_SCHEMA",
        )
        require(any(matches_type(value, item) for item in types), "SCHEMA_INVALID")
    if "const" in schema:
        require(json_equal(value, schema["const"]), "SCHEMA_INVALID")
    if "enum" in schema:
        require(
            any(json_equal(value, item) for item in schema["enum"]),
            "SCHEMA_INVALID",
        )
    if isinstance(value, str) and "minLength" in schema:
        require(len(value) >= schema["minLength"], "SCHEMA_INVALID")
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        require(isinstance(properties, dict), "INVALID_SCHEMA")
        require(
            all(key in value for key in schema.get("required", [])),
            "SCHEMA_INVALID",
        )
        additional = schema.get("additionalProperties", True)
        for key, child in value.items():
            if key in properties:
                validate(child, properties[key], root)
            elif additional is False:
                raise InvalidInput("SCHEMA_INVALID")
            elif isinstance(additional, dict):
                validate(child, additional, root)
            else:
                require(additional is True, "INVALID_SCHEMA")
    if isinstance(value, list):
        if "minItems" in schema:
            require(len(value) >= schema["minItems"], "SCHEMA_INVALID")
        if "maxItems" in schema:
            require(len(value) <= schema["maxItems"], "SCHEMA_INVALID")
        if schema.get("uniqueItems", False):
            for index, child in enumerate(value):
                require(
                    not any(json_equal(child, prior) for prior in value[:index]),
                    "SCHEMA_INVALID",
                )
        if "items" in schema:
            for child in value:
                validate(child, schema["items"], root)


def load_tokens(path):
    _, manifest = read_json(path)
    require(isinstance(manifest, dict), "INVALID_DENY_MANIFEST")
    require(
        manifest.get("schema_version") == "ignition-229-r2-deny-token-manifest-v1",
        "INVALID_DENY_MANIFEST",
    )
    tokens = manifest.get("literal_tokens")
    require(
        isinstance(tokens, list)
        and all(isinstance(token, str) and bool(token) for token in tokens),
        "INVALID_DENY_MANIFEST",
    )
    return sorted(set(tokens), key=lambda token: (-len(token), token))


def redact(value, tokens):
    if isinstance(value, str):
        for token in tokens:
            value = value.replace(token, "[REDACTED]")
        return value
    if isinstance(value, list):
        return [redact(child, tokens) for child in value]
    if isinstance(value, dict):
        return {key: redact(child, tokens) for key, child in value.items()}
    return value


def build_packet(args, contract):
    _, envelope = read_json(args.response)
    _, schema = read_json(args.response_schema)
    tokens = load_tokens(args.deny_token_manifest)
    case_raw = Path(args.case).read_bytes()
    criteria_raw = Path(args.criteria).read_bytes()
    case_text = strict_text(case_raw)
    criteria_text = strict_text(criteria_raw)

    sanitized = sanitize(envelope, contract)
    validate(sanitized, schema, schema)
    require(isinstance(sanitized, dict), "SCHEMA_INVALID")
    responses = sanitized.get("responses")
    require(
        isinstance(responses, list)
        and len(responses) == 3
        and all(isinstance(response, dict) for response in responses),
        "SCHEMA_INVALID",
    )
    ids = [response.get("case_id") for response in responses]
    require(
        all(isinstance(case_id, str) for case_id in ids)
        and set(ids) == {"A", "B", "C"},
        "INVALID_CASE_IDS",
    )
    selected = [response for response in responses
                if response["case_id"] == args.case_id]
    require(len(selected) == 1, "INVALID_CASE_IDS")
    require(bool(args.response_id), "INVALID_RESPONSE_ID")

    packet = {
        "schema_version": "task229-r2-blind-packet-v1",
        "response_id": args.response_id,
        "case_id": args.case_id,
        "case_sha256": sha256(case_raw),
        "case_text": case_text,
        "criteria_sha256": sha256(criteria_raw),
        "criteria_text": criteria_text,
        "response": redact(selected[0], tokens),
    }
    serialized = canonical_bytes(packet)
    require(
        not any(token.encode("utf-8") in serialized for token in tokens),
        "DENY_TOKEN_LEAK",
    )
    return serialized


def write_atomic(path, raw, protected):
    destination = Path(path).resolve()
    require(destination not in protected, "OUTPUT_IS_INPUT")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=destination.parent,
            prefix=".packet-",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


class QuietParser(argparse.ArgumentParser):
    def error(self, message):
        raise InvalidInput("INVALID_ARGUMENTS")


def main(argv=None):
    parser = QuietParser(prog="builder.py")
    for flag in (
        "response", "response-id", "case", "criteria",
        "deny-token-manifest", "response-schema", "output",
    ):
        parser.add_argument("--" + flag)
    parser.add_argument("--case-id", choices=("A", "B", "C"))
    parser.add_argument(
        "--metadata-key-contract",
        default="metadata-key-contract.json",
    )
    parser.add_argument("--contract-report")
    try:
        args = parser.parse_args(argv)
        ordinary = (
            args.response, args.case_id, args.response_id, args.case,
            args.criteria, args.deny_token_manifest, args.response_schema,
            args.output,
        )
        if args.contract_report is not None:
            require(all(item is None for item in ordinary), "INVALID_ARGUMENTS")
        else:
            require(all(item is not None for item in ordinary), "INVALID_ARGUMENTS")

        raw, contract = load_contract(args.metadata_key_contract)
        protected = {Path(args.metadata_key_contract).resolve()}
        if args.contract_report is not None:
            report = {
                "metadata_key_contract_sha256": sha256(raw),
                "schema_version": contract["schema_version"],
                "key_canonicalization": contract["key_canonicalization"],
                "whole_object_removal_canonical_keys":
                    contract["whole_object_removal_canonical_keys"],
                "exact_metadata_removal_canonical_keys":
                    contract["exact_metadata_removal_canonical_keys"],
                "unlisted_key_policy": contract["unlisted_key_policy"],
            }
            output = args.contract_report
            serialized = canonical_bytes(report)
        else:
            protected.update(
                Path(path).resolve()
                for path in (
                    args.response, args.case, args.criteria,
                    args.deny_token_manifest, args.response_schema,
                )
            )
            output = args.output
            serialized = build_packet(args, contract)
        write_atomic(output, serialized, protected)
        return 0
    except InvalidInput as error:
        sys.stderr.write(str(error) + "\n")
    except (OSError, UnicodeError, ValueError, TypeError, KeyError,
            RecursionError, OverflowError):
        sys.stderr.write("INVALID_INPUT_OR_IO\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
```