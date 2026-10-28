"""N1 Static Semantic Checker — validates semantic consistency of FunctionSpec."""
import re
from typing import List, Dict, Set

SAFE_IDENTIFIER = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')

class N1SemanticChecker:
    def check(self, spec: dict) -> List[Dict]:
        """Returns list of semantic issues. Empty list = all checks pass."""
        issues = []
        issues.extend(self._check_unused_vars(spec))
        issues.extend(self._check_undefined_refs(spec))
        issues.extend(self._check_empty_conditions(spec))
        issues.extend(self._check_expression_safety(spec))
        issues.extend(self._check_example_consistency(spec))
        issues.extend(self._check_version_consistency(spec))
        issues.extend(self._check_dependency_references(spec))
        return issues

    def _get_all_vars(self, spec: dict) -> Set[str]:
        return set(spec.get('inputs', {}).keys()) | set(spec.get('outputs', {}).keys())

    def _extract_vars(self, expr: str) -> Set[str]:
        return set(re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', expr))

    def _check_unused_vars(self, spec: dict) -> List[Dict]:
        issues = []
        input_vars = set(spec.get('inputs', {}).keys())
        all_exprs = []
        for cond_type in ['preconditions', 'postconditions', 'invariants']:
            for c in spec.get(cond_type, []):
                all_exprs.append(c.get('expression', ''))
        used = set()
        for e in all_exprs:
            used |= self._extract_vars(e)
        for v in input_vars:
            if v not in used and v != 'self':
                issues.append({"severity": "WARNING", "field": f"inputs.{v}",
                    "issue": f"Input variable '{v}' not referenced in any condition"})
        return issues

    def _check_undefined_refs(self, spec: dict) -> List[Dict]:
        issues = []
        defined = self._get_all_vars(spec)
        # Add built-in constants
        defined |= {'true', 'false', 'null', 'pi', 'e'}
        for cond_type in ['preconditions', 'postconditions', 'invariants']:
            for i, c in enumerate(spec.get(cond_type, [])):
                refs = self._extract_vars(c.get('expression', ''))
                for ref in refs:
                    if not SAFE_IDENTIFIER.match(ref):
                        continue
                    # Skip numeric literals
                    if ref.isdigit():
                        continue
                    # Skip keywords
                    if ref in ('if', 'then', 'else', 'and', 'or', 'not', 'in', 'is', 'for', 'while'):
                        continue
                    if ref not in defined:
                        issues.append({"severity": "ERROR", "field": f"{cond_type}[{i}]",
                            "issue": f"Undefined reference '{ref}' in expression",
                            "expression": c.get('expression', '')})
        return issues

    def _check_empty_conditions(self, spec: dict) -> List[Dict]:
        issues = []
        for cond_type in ['preconditions', 'postconditions']:
            for i, c in enumerate(spec.get(cond_type, [])):
                expr = c.get('expression', '').strip()
                if not expr:
                    issues.append({"severity": "ERROR", "field": f"{cond_type}[{i}]",
                        "issue": "Empty condition expression"})
        return issues

    def _check_expression_safety(self, spec: dict) -> List[Dict]:
        """Flag potentially unsafe expressions."""
        issues = []
        unsafe_patterns = [
            (r'__', "Double underscore (may indicate internal access)"),
            (r'import\s', "Import statement"),
            (r'exec\s*\(', "exec() call"),
            (r'eval\s*\(', "eval() call"),
            (r'\.\s*\.\s*\.', "Ellipsis"),
            (r'open\s*\(', "open() call"),
            (r'os\.', "os module access"),
            (r'subprocess', "subprocess access"),
        ]
        for cond_type in ['preconditions', 'postconditions', 'invariants']:
            for i, c in enumerate(spec.get(cond_type, [])):
                expr = c.get('expression', '')
                for pattern, reason in unsafe_patterns:
                    if re.search(pattern, expr):
                        issues.append({"severity": "ERROR", "field": f"{cond_type}[{i}]",
                            "issue": f"Unsafe pattern: {reason}",
                            "match": pattern})
        return issues

    def _check_example_consistency(self, spec: dict) -> List[Dict]:
        issues = []
        inputs_schema = spec.get('inputs', {})
        outputs_schema = spec.get('outputs', {})
        for i, ex in enumerate(spec.get('examples', [])):
            ex_inputs = ex.get('inputs', {})
            ex_output = ex.get('expected_output', {})
            for vname in inputs_schema:
                if vname not in ex_inputs:
                    issues.append({"severity": "WARNING", "field": f"examples[{i}]",
                        "issue": f"Missing input '{vname}' in example"})
            for vname in ex_inputs:
                if vname not in inputs_schema:
                    issues.append({"severity": "WARNING", "field": f"examples[{i}]",
                        "issue": f"Extra input '{vname}' not in spec"})
            for vname in outputs_schema:
                if vname not in ex_output:
                    issues.append({"severity": "WARNING", "field": f"examples[{i}]",
                        "issue": f"Missing output '{vname}' in expected_output"})
        return issues

    def _check_version_consistency(self, spec: dict) -> List[Dict]:
        issues = []
        sv = spec.get('spec_version', '')
        if sv == '0.0.0':
            issues.append({"severity": "ERROR", "field": "spec_version",
                "issue": "spec_version cannot be 0.0.0"})
        return issues

    def _check_dependency_references(self, spec: dict) -> List[Dict]:
        issues = []
        deps = spec.get('dependencies', [])
        dep_ids = set()
        for d in deps:
            did = d.get('function_id', '')
            if not re.match(r'^FN-\d{8}-\d{4}$', did):
                issues.append({"severity": "ERROR", "field": "dependencies",
                    "issue": f"Invalid dependency function_id: '{did}'"})
            if did in dep_ids:
                issues.append({"severity": "WARNING", "field": "dependencies",
                    "issue": f"Duplicate dependency: {did}"})
            dep_ids.add(did)
        return issues
