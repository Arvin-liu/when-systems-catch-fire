#!/usr/bin/env python3
"""Deterministic, standard-library-only packet builder."""

import argparse
import hashlib
import json
import math
import os
import sys
import tempfile


class BuildError(Exception):
    pass


def require(condition, diagnostic):
    if not condition:
        raise BuildError(diagnostic)


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise BuildError("invalid command-line arguments")


def decode_utf8(data):
    text = data.decode("utf-8", errors="strict")
    require(text.encode("utf-8", errors="strict") == data,
            "UTF-8 round-trip failure")
    return text


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def reject_constant(value):
    raise BuildError("nonfinite JSON number")


def check_json_values(value):
    if isinstance(value, str):
        value.encode("utf-8", errors="strict")
    elif isinstance(value, float):
        require(math.isfinite(value), "nonfinite JSON number")
    elif isinstance(value, list):
        for item in value:
            check_json_values(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            key.encode("utf-8", errors="strict")
            check_json_values(item)


def parse_json(data):
    value = json.loads(
        decode_utf8(data),
        object_pairs_hook=unique_object,
        parse_constant=reject_constant,
    )
    check_json_values(value)
    return value


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def frozen_schema():
    def string(nonempty=False):
        result = {"type": "string"}
        if nonempty:
            result["minLength"] = 1
        return result

    def strings(unique=False):
        result = {"type": "array", "items": string()}
        if unique:
            result["uniqueItems"] = True
        return result

    def obj(required, properties):
        return {
            "type": "object",
            "additionalProperties": False,
            "required": required,
            "properties": properties,
        }

    nullable_string = {"type": ["string", "null"]}
    fields = [
        "case_id", "primary_action", "additional_actions",
        "reported_values", "preserved_baseline_action_ids",
        "fallback", "scope", "rationale",
    ]
    properties = {
        "case_id": {"enum": ["A", "B", "C"]},
        "primary_action": string(True),
        "additional_actions": strings(),
        "reported_values": {
            "type": "array",
            "items": {"$ref": "#/$defs/reported_value"},
        },
        "preserved_baseline_action_ids": strings(True),
        "fallback": nullable_string,
        "scope": string(),
        "rationale": string(),
    }
    with_trace = dict(properties)
    with_trace["route_trace"] = {"$ref": "#/$defs/route_trace"}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "task229-successor-output-r0",
        "title": "Task229 successor response envelope R0",
        "type": "object",
        "additionalProperties": False,
        "required": ["schema_version", "responses"],
        "properties": {
            "schema_version": {"const": "task229-successor-output-r0"},
            "responses": {
                "type": "array",
                "minItems": 3,
                "maxItems": 3,
                "items": {"$ref": "#/$defs/case_response"},
            },
        },
        "$defs": {
            "reported_value": obj(
                ["name", "value", "unit"],
                {"name": string(True), "value": {}, "unit": nullable_string},
            ),
            "route_trace": obj(
                [
                    "policy_id", "route_type", "selected_rule_id",
                    "selected_action_id", "input_ids",
                    "preserved_baseline_action_ids",
                ],
                {
                    "policy_id": string(True),
                    "route_type": {"enum": ["selector", "fallback", "stop"]},
                    "selected_rule_id": nullable_string,
                    "selected_action_id": nullable_string,
                    "input_ids": strings(True),
                    "preserved_baseline_action_ids": strings(True),
                },
            ),
            "case_response": {
                "oneOf": [
                    obj(fields, properties),
                    obj(fields + ["route_trace"], with_trace),
                ],
            },
        },
    }


def canonical_bytes(value):
    return (
        json.dumps(
            value, ensure_ascii=False, sort_keys=True,
            separators=(",", ":"), allow_nan=False,
        ) + "\n"
    ).encode("utf-8", errors="strict")


def metadata_keys():
    keys = {
        "route_trace",
        "provenance", "provenance_id", "provenance_ids",
        "provenance_metadata",
        "builder", "builder_id", "builder_ids",
        "builder_name", "builder_names", "builder_version",
        "builder_metadata",
        "tool", "tools", "tool_id", "tool_ids",
        "tool_name", "tool_names", "tool_version", "tool_metadata",
        "file_path", "file_paths", "filepath", "filepaths",
        "source_locator", "source_locators", "source_path", "source_paths",
        "repository_path", "repository_paths",
        "repository_file_path", "repository_file_paths",
    }
    for family in ("artifact", "session", "policy", "lineage", "bundle"):
        keys.update({
            family, family + "_id", family + "_ids",
            family + "_name", family + "_names",
        })
    keys.update({
        "condition", "condition_id", "condition_ids",
        "condition_name", "condition_names",
        "artifact_bundle_id", "artifact_bundle_ids",
        "design_session_id", "design_session_ids",
        "runtime_session_id", "runtime_session_ids",
        "runtime_thread_id", "runtime_thread_ids",
        "runtime_thread_or_session_id", "runtime_thread_or_session_ids",
    })
    return frozenset(keys)


METADATA_KEYS = metadata_keys()


def remove_metadata(value):
    if isinstance(value, dict):
        return {
            key: remove_metadata(item)
            for key, item in value.items()
            if key.lower().replace("-", "_") not in METADATA_KEYS
        }
    if isinstance(value, list):
        return [remove_metadata(item) for item in value]
    return value


def is_type(value, name):
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "null": value is None,
    }.get(name, False)


def schema_valid(value, schema, root):
    if "$ref" in schema:
        reference = schema["$ref"]
        if not reference.startswith("#/$defs/"):
            return False
        name = reference[len("#/$defs/"):]
        return schema_valid(value, root["$defs"][name], root)

    if "oneOf" in schema:
        return sum(
            schema_valid(value, branch, root)
            for branch in schema["oneOf"]
        ) == 1

    if "const" in schema:
        if canonical_bytes(value) != canonical_bytes(schema["const"]):
            return False

    if "enum" in schema:
        if not any(
            canonical_bytes(value) == canonical_bytes(item)
            for item in schema["enum"]
        ):
            return False

    if "type" in schema:
        types = schema["type"]
        if isinstance(types, str):
            types = [types]
        if not any(is_type(value, name) for name in types):
            return False

    if isinstance(value, dict):
        properties = schema.get("properties", {})
        if any(key not in value for key in schema.get("required", [])):
            return False
        if schema.get("additionalProperties") is False:
            if any(key not in properties for key in value):
                return False
        for key, item in value.items():
            if key in properties:
                if not schema_valid(item, properties[key], root):
                    return False

    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            return False
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            return False
        if schema.get("uniqueItems"):
            # All uniqueItems arrays in the frozen schema contain strings.
            for index, item in enumerate(value):
                if any(item == previous for previous in value[:index]):
                    return False
        if "items" in schema:
            if not all(schema_valid(item, schema["items"], root)
                       for item in value):
                return False

    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            return False
    return True


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


def check_packet_tree(value, tokens):
    if isinstance(value, dict):
        for key, item in value.items():
            require(
                key.lower().replace("-", "_") not in METADATA_KEYS,
                "metadata remains in packet",
            )
            require(not any(token in key for token in tokens),
                    "deny token remains in packet")
            check_packet_tree(item, tokens)
    elif isinstance(value, list):
        for item in value:
            check_packet_tree(item, tokens)
    elif isinstance(value, str):
        require(not any(token in value for token in tokens),
                "deny token remains in packet")


def protect_inputs(output, inputs):
    destination = os.path.realpath(output)
    for path in inputs:
        require(destination != os.path.realpath(path),
                "output aliases an input")
        if os.path.exists(output):
            require(not os.path.samefile(output, path),
                    "output aliases an input")


def write_atomic(path, data):
    directory = os.path.dirname(os.path.abspath(path))
    temporary = None
    descriptor = None
    try:
        descriptor, temporary = tempfile.mkstemp(
            prefix=".packet-", suffix=".tmp", dir=directory,
        )
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = None
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary is not None:
            try:
                os.unlink(temporary)
            except OSError:
                pass


def build(args):
    inputs = [
        args.response, args.case, args.criteria,
        args.deny_token_manifest, args.response_schema,
    ]
    protect_inputs(args.output, inputs)
    require(bool(args.response_id), "empty response ID")
    args.response_id.encode("utf-8", errors="strict")

    supplied_schema = parse_json(read_bytes(args.response_schema))
    schema = frozen_schema()
    require(canonical_bytes(supplied_schema) == canonical_bytes(schema),
            "response schema differs from frozen schema")

    manifest = parse_json(read_bytes(args.deny_token_manifest))
    require(isinstance(manifest, dict), "invalid deny-token manifest")
    tokens = manifest.get("literal_tokens")
    require(isinstance(tokens, list) and bool(tokens),
            "invalid deny-token list")
    require(all(isinstance(token, str) and bool(token) for token in tokens),
            "invalid deny token")
    tokens = sorted(set(tokens), key=lambda token: (-len(token), token))

    source = parse_json(read_bytes(args.response))
    cleaned = remove_metadata(source)
    require(schema_valid(cleaned, schema, schema),
            "response schema validation failed")

    responses = cleaned["responses"]
    case_ids = [response["case_id"] for response in responses]
    require(len(case_ids) == 3 and set(case_ids) == {"A", "B", "C"},
            "invalid or repeated case IDs")
    selected = [
        response for response in responses if response["case_id"] == args.case_id
    ]
    require(len(selected) == 1, "requested case is absent or repeated")
    response = redact(selected[0], tokens)

    case_bytes = read_bytes(args.case)
    criteria_bytes = read_bytes(args.criteria)
    case_text = decode_utf8(case_bytes)
    criteria_text = decode_utf8(criteria_bytes)

    packet = {
        "schema_version": "task229-r2-blind-packet-v1",
        "response_id": args.response_id,
        "case_id": args.case_id,
        "case_text": case_text,
        "case_sha256": hashlib.sha256(case_bytes).hexdigest(),
        "criteria_text": criteria_text,
        "criteria_sha256": hashlib.sha256(criteria_bytes).hexdigest(),
        "response": response,
    }

    check_packet_tree(packet, tokens)
    serialized = canonical_bytes(packet)
    serialized_text = decode_utf8(serialized)
    require(not any(token in serialized_text for token in tokens),
            "deny token remains in serialized packet")

    decoded = parse_json(serialized)
    for prefix, original in (("case", case_bytes), ("criteria", criteria_bytes)):
        restored = decoded[prefix + "_text"].encode("utf-8", errors="strict")
        require(restored == original, "packet byte preservation failed")
        require(
            hashlib.sha256(restored).hexdigest() == decoded[prefix + "_sha256"],
            "packet digest verification failed",
        )

    protect_inputs(args.output, inputs)
    write_atomic(args.output, serialized)


def main():
    parser = Parser(prog="builder.py", allow_abbrev=False)
    parser.add_argument("--response", required=True)
    parser.add_argument("--case-id", required=True, choices=("A", "B", "C"))
    parser.add_argument("--response-id", required=True)
    parser.add_argument("--case", required=True)
    parser.add_argument("--criteria", required=True)
    parser.add_argument("--deny-token-manifest", required=True)
    parser.add_argument("--response-schema", required=True)
    parser.add_argument("--output", required=True)
    try:
        build(parser.parse_args())
        return 0
    except BuildError as error:
        sys.stderr.write("builder: " + str(error) + "\n")
    except UnicodeError:
        sys.stderr.write("builder: invalid UTF-8\n")
    except (json.JSONDecodeError, ValueError, OverflowError):
        sys.stderr.write("builder: invalid JSON or numeric representation\n")
    except OSError:
        sys.stderr.write("builder: file operation failed\n")
    except (RecursionError, MemoryError):
        sys.stderr.write("builder: input exceeds processing limits\n")
    except Exception:
        sys.stderr.write("builder: processing failed\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
