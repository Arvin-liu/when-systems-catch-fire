"""N1 FunctionSpec Parser — validates and parses FunctionSpec JSON.

v0.2: adapted from v0.1 with standard imports, no exec/compile.
"""
import json, hashlib, re

FUNCTION_ID_RE = re.compile(r'^FN-\d{8}-\d{4}$')
SEMVER_RE = re.compile(r'^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$')

class FunctionSpecParseError(Exception):
    pass

class N1FunctionSpecParser:
    VERSION = "0.2.0"

    SUPPORTED_DOMAIN = "symbolic"

    def parse(self, spec_json: str) -> dict:
        """Parse JSON string into validated FunctionSpec dict."""
        try:
            spec = json.loads(spec_json)
        except json.JSONDecodeError as e:
            raise FunctionSpecParseError(f"Invalid JSON: {e}")

        self._validate(spec)
        spec['spec_hash'] = self._compute_hash(spec)
        return spec

    def _validate(self, spec: dict):
        required = ['function_id', 'spec_version', 'name', 'domain', 'inputs',
                    'outputs', 'preconditions', 'postconditions', 'effects_declared',
                    'created_at']
        for field in required:
            if field not in spec:
                raise FunctionSpecParseError(f"Missing required field: {field}")

        if not FUNCTION_ID_RE.match(spec['function_id']):
            raise FunctionSpecParseError(
                f"Invalid function_id '{spec['function_id']}' (expected FN-YYYYMMDD-NNNN)")

        if not SEMVER_RE.match(spec.get('spec_version', '')):
            raise FunctionSpecParseError(
                f"Invalid spec_version '{spec.get('spec_version')}' (expected MAJOR.MINOR.PATCH)")

        if spec['domain'] != self.SUPPORTED_DOMAIN:
            raise FunctionSpecParseError(
                f"Domain '{spec['domain']}' not supported in v0.2 (symbolic only)")

        if not isinstance(spec['inputs'], dict) or len(spec['inputs']) == 0:
            raise FunctionSpecParseError("inputs must be non-empty object")
        for k, v in spec['inputs'].items():
            if not isinstance(v, str):
                raise FunctionSpecParseError(f"input '{k}' type must be string")

        if not isinstance(spec['outputs'], dict) or len(spec['outputs']) == 0:
            raise FunctionSpecParseError("outputs must be non-empty object")
        for k, v in spec['outputs'].items():
            if not isinstance(v, str):
                raise FunctionSpecParseError(f"output '{k}' type must be string")

        for ptype, pname in [('preconditions', 'precondition'), ('postconditions', 'postcondition')]:
            conds = spec.get(ptype, [])
            if not isinstance(conds, list):
                raise FunctionSpecParseError(f"{ptype} must be an array")
            for i, cond in enumerate(conds):
                if not isinstance(cond, dict):
                    raise FunctionSpecParseError(f"{pname}[{i}] must be an object")
                expr = cond.get('expression', '')
                if not expr or not isinstance(expr, str):
                    raise FunctionSpecParseError(
                        f"{pname}[{i}].expression must be a non-empty string")

        effects = spec.get('effects_declared', [])
        if not isinstance(effects, list) or len(effects) == 0:
            raise FunctionSpecParseError("effects_declared must be non-empty array")

    def _compute_hash(self, spec: dict):
        raw = json.dumps({
            k: spec[k] for k in sorted(spec.keys())
            if k in ('function_id', 'spec_version', 'name', 'domain', 'inputs',
                     'outputs', 'preconditions', 'postconditions', 'effects_declared')
        }, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()
