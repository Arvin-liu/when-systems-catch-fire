"""N1 Semantic Checker — validates FunctionSpec semantics.

v0.2: adapted, detects undefined refs, unsafe expressions, version 0.0.0.
"""
import re
from function_os.n1_safe_expression_dsl import SafeExpressionDSL

SEMVER_RE = re.compile(r'^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$')

class N1SemanticChecker:
    VERSION = "0.2.1-candidate"

    def __init__(self):
        self.dsl = SafeExpressionDSL()

    def check(self, spec: dict) -> list:
        issues = []

        # Check version not 0.0.0
        if spec.get('spec_version') == '0.0.0' or not SEMVER_RE.match(spec.get('spec_version', '')):
            issues.append({"severity": "ERROR", "field": "spec_version",
                           "issue": "spec_version cannot be 0.0.0"})

        # Check preconditions don't reference undefined variables
        known_vars = set(spec.get('inputs', {}).keys())
        for i, pc in enumerate(spec.get('preconditions', [])):
            expr = pc.get('expression', '')
            refs = self._extract_refs(expr)
            undefined = refs - known_vars
            if undefined:
                issues.append({"severity": "ERROR", "field": f"preconditions[{i}]",
                               "issue": f"Undefined references: {undefined}",
                               "expression": expr})

        # Check postconditions
        output_vars = set(spec.get('outputs', {}).keys())
        all_known = known_vars | output_vars
        for i, pc in enumerate(spec.get('postconditions', [])):
            expr = pc.get('expression', '')
            refs = self._extract_refs(expr)
            undefined = refs - all_known
            if undefined:
                issues.append({"severity": "ERROR", "field": f"postconditions[{i}]",
                               "issue": f"Undefined references: {undefined}",
                               "expression": expr})

        # Check domain
        if spec.get('domain') != 'symbolic':
            issues.append({"severity": "ERROR", "field": "domain",
                           "issue": "Only symbolic domain supported in v0.2"})

        return issues

    def _extract_refs(self, expr: str) -> set:
        """Extract variable names from expression. Simple regex-based approach."""
        if not expr:
            return set()
        import re as _re
        # Match word-like tokens that aren't numbers or operators
        tokens = _re.findall(r'[a-zA-Z_]\w*', expr)
        keywords = {'True', 'False', 'None', 'and', 'or', 'not', 'if', 'else'}
        return set(tokens) - keywords
