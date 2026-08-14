"""N5 Compile Error Feedback Loop — bridges compile/interpreter errors back to spec revision.

When N2 compile or N3 interpret fails, N5 produces structured feedback for spec revision.
"""
from typing import Dict, Any, List

class CompileFeedback:
    def __init__(self):
        self.errors: List[Dict] = []
        self.warnings: List[Dict] = []
        self.suggestions: List[Dict] = []

    def add_error(self, field: str, issue: str, current_value: Any = None,
                  suggestion: str = ""):
        self.errors.append({
            "severity": "error",
            "field": field,
            "issue": issue,
            "current_value": current_value,
            "suggestion": suggestion
        })

    def add_warning(self, field: str, issue: str, current_value: Any = None,
                    suggestion: str = ""):
        self.warnings.append({
            "severity": "warning",
            "field": field,
            "issue": issue,
            "current_value": current_value,
            "suggestion": suggestion
        })

    def add_suggestion(self, field: str, recommendation: str, rationale: str = ""):
        self.suggestions.append({
            "severity": "suggestion",
            "field": field,
            "recommendation": recommendation,
            "rationale": rationale
        })

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def get_revision_guide(self) -> dict:
        return {
            "must_fix": self.errors,
            "should_review": self.warnings,
            "could_improve": self.suggestions,
            "total_issues": len(self.errors) + len(self.warnings) + len(self.suggestions),
            "resolvable": len(self.suggestions) + len(self.errors) == 0
        }


class N5CompileFeedbackLoop:
    """Produces structured feedback from compile/interpret failures."""

    def analyze_compile_error(self, compile_result: dict, spec: dict) -> CompileFeedback:
        fb = CompileFeedback()
        if compile_result.get('ok'):
            return fb

        error = compile_result.get('error', 'UNKNOWN')
        details = compile_result.get('details', [])

        if error == 'COMPILE_ERROR':
            for d in details if isinstance(details, list) else [details]:
                d_str = str(d)
                if 'Domain' in d_str or 'domain' in d_str:
                    fb.add_error('domain', d_str, spec.get('domain'),
                                 "Change domain to 'symbolic'")
                elif 'outputs' in d_str or 'no outputs' in d_str.lower():
                    fb.add_error('outputs', d_str, spec.get('outputs'),
                                 "Define at least one output variable")
                elif 'dependency' in d_str.lower():
                    fb.add_error('dependencies', d_str,
                                 suggestion="Remove self-referential dependency")
                else:
                    fb.add_error('spec', d_str,
                                 suggestion="Review spec for validity")

        return fb

    def analyze_interpret_error(self, result: dict, compiled: dict) -> CompileFeedback:
        fb = CompileFeedback()
        if result.get('ok'):
            return fb

        error = result.get('error', 'UNKNOWN')
        details = result.get('details', '')

        if error == 'PRECONDITION_FAILED':
            expr = result.get('expression', '')
            if 'Missing input' in str(details):
                fb.add_error('inputs', details, compiled.get('input_schema'),
                             "Ensure all required inputs are provided")
            else:
                fb.add_error('preconditions', f"Precondition violated: {details}",
                             suggestion="Relax precondition or fix input values")

        elif error == 'COMPUTE_ERROR':
            fb.add_error('expressions', details,
                         suggestion="Check expression syntax and variable references")

        elif error == 'POSTCONDITION_FAILED':
            fb.add_error('postconditions', details,
                         suggestion="Fix postcondition expression or review computation logic")

        elif error == 'INVARIANT_FAILED':
            fb.add_error('invariants', details,
                         suggestion="Fix invariant or review execution logic")

        return fb

    def analyze_semantic_issues(self, issues: list, spec: dict) -> CompileFeedback:
        fb = CompileFeedback()
        for issue in issues:
            if issue.get('severity') == 'ERROR':
                fb.add_error(issue.get('field', ''), issue.get('issue', ''),
                             suggestion="Fix and re-validate")
            else:
                fb.add_warning(issue.get('field', ''), issue.get('issue', ''),
                               suggestion="Review if intentional")
        return fb
