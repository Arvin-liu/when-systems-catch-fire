"""N8 ComposerRouter — canonical composition/routing between functions.

v0.2: correctly assigned to N8 (was wrongfully N7 in v0.1).
Takes task description + registry candidates → execution plan.
"""
import json
from typing import Dict, Any, List

class N8ComposerRouter:
    VERSION = "0.2.0"

    def plan(self, task: dict, candidates: list) -> dict:
        """Generate execution plan from task + candidate functions."""
        required = task.get('required_functions', [])
        available = {c.get('function_id', ''): c for c in candidates}

        plan = {"task_id": task.get('task_id', 'TASK-0000'),
                "status": "OK",
                "plan_type": "sequential",  # v0.2: sequential only
                "steps": [],
                "errors": []}

        for i, req in enumerate(required):
            fn_id = req.get('function_id', '')
            candidate = available.get(fn_id)

            # Fallback: look up by payload.function_id (for artifacts)
            if candidate is None:
                for v in available.values():
                    if v.get('payload', {}).get('function_id') == fn_id:
                        candidate = v
                        break

            if candidate is None:
                plan['errors'].append({
                    "step": i,
                    "issue": "FUNCTION_NOT_FOUND",
                    "function_id": fn_id
                })
                plan['steps'].append({
                    "step_index": i, "function_id": fn_id,
                    "status": "SKIPPED", "reason": "not in registry"
                })
                continue

            plan['steps'].append({
                "step_index": i,
                "function_id": fn_id,
                "status": "PLANNED",
                "artifact_id": candidate.get('artifact_id', ''),
                "inputs_from": req.get('inputs_from', 'task_input'),
                "on_failure": req.get('on_failure', 'ABORT')
            })

        if plan['errors']:
            plan['status'] = 'PARTIAL'

        return plan

    def compose_sequential(self, plans: list) -> dict:
        """Compose multiple execution plans into a single sequential plan."""
        all_steps = []
        all_errors = []
        for p in plans:
            all_steps.extend(p.get('steps', []))
            all_errors.extend(p.get('errors', []))

        return {
            "composition_id": "CP-0001",
            "plan_count": len(plans),
            "status": "OK" if not all_errors else "PARTIAL",
            "steps": all_steps,
            "errors": all_errors
        }

    @property
    def capabilities(self) -> dict:
        return {
            "sequential_composition": True,
            "conditional_routing": True,
            "failure_propagation": True,
            "deferred_composition": False,
            "excluded": ["weight-space algebra", "automatic function discovery"]
        }
