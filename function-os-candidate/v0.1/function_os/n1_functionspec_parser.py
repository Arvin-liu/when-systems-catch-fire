"""N1 FunctionSpec Parser — strict JSON parser with schema validation."""
import json, re, hashlib
from typing import Dict, List, Any

VALID_TYPES = {
    "integer", "float", "boolean", "string",
    "list<integer>", "list<float>", "list<boolean>", "list<string>",
    "map<string,integer>", "map<string,float>", "map<string,boolean>", "map<string,string>"
}
VALID_DOMAINS = {"symbolic", "neural_weight", "hybrid"}
VALID_EFFECTS = {"pure", "log", "registry_write"}

REQUIRED_TOP = ["function_id", "spec_version", "name", "inputs", "outputs",
                "preconditions", "postconditions", "effects_declared"]

class FunctionSpecParseError(Exception):
    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__("; ".join(errors))

class N1FunctionSpecParser:
    def parse(self, raw: str) -> Dict[str, Any]:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise FunctionSpecParseError([f"Invalid JSON: {e}"])
        
        errors = self._validate(data)
        if errors:
            raise FunctionSpecParseError(errors)
        
        data['spec_hash'] = self._compute_spec_hash(data)
        return data

    def parse_file(self, path: str) -> Dict[str, Any]:
        with open(path, 'r', encoding='utf-8') as f:
            return self.parse(f.read())

    def _validate(self, data: dict) -> List[str]:
        errors = []

        if not isinstance(data, dict):
            errors.append("Root must be a JSON object")
            return errors

        # Required top-level fields
        for fld in REQUIRED_TOP:
            if fld not in data:
                errors.append(f"Missing required field: {fld}")

        if errors:
            return errors

        # function_id
        fid = data.get('function_id', '')
        if not isinstance(fid, str) or not re.match(r'^FN-\d{8}-\d{4}$', fid):
            errors.append(f"Invalid function_id: '{fid}' (must match FN-YYYYMMDD-NNNN)")

        # spec_version
        sv = data.get('spec_version', '')
        if not isinstance(sv, str) or not re.match(r'^\d+\.\d+\.\d+$', sv):
            errors.append(f"Invalid spec_version: '{sv}' (must match MAJOR.MINOR.PATCH)")

        # name
        name = data.get('name', '')
        if not isinstance(name, str) or len(name) < 1 or len(name) > 128:
            errors.append(f"Invalid name: must be 1-128 characters")

        # domain
        domain = data.get('domain', '')
        if domain and domain not in VALID_DOMAINS:
            errors.append(f"Invalid domain: '{domain}'")
        if domain in ('neural_weight', 'hybrid'):
            errors.append(f"Domain '{domain}' not supported in v0.1 (symbolic only)")

        # inputs
        input_errs = self._validate_type_map(data.get('inputs', {}), "inputs")
        errors.extend(input_errs)

        # outputs
        output_errs = self._validate_type_map(data.get('outputs', {}), "outputs")
        errors.extend(output_errs)

        # preconditions
        errors.extend(self._validate_conditions(data.get('preconditions', []), "preconditions"))

        # postconditions
        errors.extend(self._validate_conditions(data.get('postconditions', []), "postconditions"))

        # invariants
        if 'invariants' in data:
            errors.extend(self._validate_conditions(data['invariants'], "invariants"))

        # effects_declared
        effects = data.get('effects_declared', [])
        if not isinstance(effects, list):
            errors.append("effects_declared must be an array")
        else:
            for ef in effects:
                if ef not in VALID_EFFECTS:
                    errors.append(f"Invalid effect: '{ef}'")

        # Unknown fields
        ALLOWED = set(REQUIRED_TOP) | {"description", "domain", "invariants", "examples",
                                         "source_asset_refs", "dependencies", "created_at", "spec_hash"}
        for key in data:
            if key not in ALLOWED:
                errors.append(f"Unknown field: '{key}'")

        return errors

    def _validate_type_map(self, tm: dict, label: str) -> List[str]:
        errors = []
        if not isinstance(tm, dict):
            errors.append(f"{label} must be an object")
            return errors
        for var_name, var_type in tm.items():
            if not isinstance(var_name, str) or not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', var_name):
                errors.append(f"Invalid variable name in {label}: '{var_name}'")
            if var_type not in VALID_TYPES:
                errors.append(f"Invalid type in {label}.{var_name}: '{var_type}'")
        return errors

    def _validate_conditions(self, conditions: list, label: str) -> List[str]:
        errors = []
        if not isinstance(conditions, list):
            errors.append(f"{label} must be an array")
            return errors
        for i, cond in enumerate(conditions):
            if not isinstance(cond, dict):
                errors.append(f"{label}[{i}] must be an object")
                continue
            if 'expression' not in cond or 'message' not in cond:
                errors.append(f"{label}[{i}] missing expression or message")
                continue
            expr = cond.get('expression', '')
            if not isinstance(expr, str) or len(expr) == 0:
                errors.append(f"{label}[{i}].expression must be a non-empty string")
            msg = cond.get('message', '')
            if not isinstance(msg, str) or len(msg) == 0:
                errors.append(f"{label}[{i}].message must be a non-empty string")
        return errors

    def _compute_spec_hash(self, data: dict) -> str:
        """SHA-256 of canonical JSON of immutable fields."""
        immutable = {k: data[k] for k in REQUIRED_TOP if k in data}
        if 'invariants' in data:
            immutable['invariants'] = data['invariants']
        canonical = json.dumps(immutable, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
        return hashlib.sha256(canonical.encode('utf-8')).hexdigest()
