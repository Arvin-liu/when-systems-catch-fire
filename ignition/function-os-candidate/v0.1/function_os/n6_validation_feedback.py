"""N6 Validation Feedback — execution trace → structured feedback for spec revision.

Post-execution: compares expected vs actual, suggests spec improvements.
"""
from typing import Dict, Any, List, Optional

class N6ValidationFeedback:
    def produce(self, result: dict, compiled: dict, spec: Optional[dict] = None) -> dict:
        """Produce validation feedback from execution result."""
        feedback = {
            "execution_ok": result.get('ok', False),
            "issues": [],
            "suggestions": [],
            "coverage": {},
            "recommendation": "accept" if result.get('ok') else "revise"
        }

        trace = result.get('trace', {})
        events = trace.get('events', [])
        duration = trace.get('duration_ms', 0)

        # Collect event coverage
        event_types = {}
        for e in events:
            et = e.get('type', 'unknown')
            event_types[et] = event_types.get(et, 0) + 1

        feedback['coverage'] = {
            "total_events": len(events),
            "duration_ms": duration,
            "event_types": event_types,
            "stages_completed": self._stages_completed(event_types)
        }

        if not result.get('ok'):
            error = result.get('error', '')
            details = result.get('details', '')
            feedback['issues'].append({
                "type": error,
                "detail": str(details),
                "stage": self._identify_failed_stage(event_types)
            })

            # Suggest fixes
            if error == 'PRECONDITION_FAILED':
                feedback['suggestions'].append({
                    "field": "preconditions",
                    "action": "review or relax",
                    "detail": "Precondition too restrictive for given inputs"
                })
            elif error == 'POSTCONDITION_FAILED':
                feedback['suggestions'].append({
                    "field": "postconditions",
                    "action": "correct",
                    "detail": "Output does not satisfy postconditions"
                })
            elif error == 'COMPUTE_ERROR':
                feedback['suggestions'].append({
                    "field": "expressions",
                    "action": "fix",
                    "detail": "Computation expression failed"
                })

        # Check unused inputs
        compiled_inputs = compiled.get('input_schema', {})
        postconds = compiled.get('postconditions', [])
        preconds = compiled.get('preconditions', [])
        all_exprs = ' '.join(preconds + postconds)
        for inp in compiled_inputs:
            if inp not in all_exprs:
                feedback['suggestions'].append({
                    "field": f"inputs.{inp}",
                    "action": "review",
                    "detail": f"Input '{inp}' not referenced in any condition"
                })

        return feedback

    def _stages_completed(self, event_types: dict) -> list:
        stages = []
        mapping = {
            'EXECUTION_START': 'start',
            'VALIDATE_INPUTS': 'validate_inputs',
            'PRECONDITION_CHECK': 'preconditions',
            'COMPUTE_STEP': 'compute',
            'COMPUTE_RESULT': 'compute',
            'POSTCONDITION_CHECK': 'postconditions',
            'INVARIANT_CHECK': 'invariants',
            'OUTPUT_PRODUCED': 'output',
            'EXECUTION_END': 'end'
        }
        for et, stage in mapping.items():
            if et in event_types:
                stages.append(stage)
        return list(dict.fromkeys(stages))

    def _identify_failed_stage(self, event_types: dict) -> str:
        if 'VALIDATE_INPUTS' not in event_types:
            return 'input_validation'
        if 'PRECONDITION_CHECK' in event_types and 'COMPUTE_STEP' not in event_types:
            return 'precondition'
        if 'COMPUTE_STEP' in event_types and 'COMPUTE_RESULT' not in event_types:
            return 'compute'
        if 'COMPUTE_RESULT' in event_types and 'POSTCONDITION_CHECK' not in event_types:
            return 'postcondition'
        if 'POSTCONDITION_CHECK' in event_types and 'OUTPUT_PRODUCED' not in event_types:
            return 'postcondition'
        return 'unknown'
