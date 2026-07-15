"""N6 Execution Trace — capture/archive/query execution traces.

v0.2: correctly assigned to N6 (was wrongfully N8 in v0.1).
"""
import hashlib, json, time
from typing import Dict, Any, List, Optional

class N6TraceCapture:
    VERSION = "0.2.0"

    def capture(self, execution_result: dict, spec: dict) -> dict:
        """Capture execution result → structured trace."""
        events = self._extract_events(execution_result)
        states = self._extract_intermediate_states(execution_result)

        trace = {
            "trace_id": execution_result.get('trace_id', ''),
            "artifact_id": execution_result.get('artifact_id', ''),
            "spec_id": spec.get('function_id', ''),
            "inputs": execution_result.get('inputs', {}),
            "outputs": execution_result.get('outputs', {}),
            "status": self._map_status(execution_result.get('status', 'UNKNOWN')),
            "events": events,
            "intermediate_states": states,
            "timing_ms": execution_result.get('time_ms', 0.0),
            "effects": spec.get('effects_declared', []),
            "errors": execution_result.get('errors', []),
            "captured_at": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            "capture_version": self.VERSION
        }

        trace['trace_hash'] = self._compute_trace_hash(trace)
        return trace

    def _map_status(self, status: str) -> str:
        mapping = {"OK": "OK", "PRECONDITION_FAILED": "FAILED",
                   "POSTCONDITION_FAILED": "FAILED", "TYPE_ERROR": "ERROR",
                   "RUNTIME_ERROR": "ERROR", "UNKNOWN": "ERROR"}
        return mapping.get(status, "ERROR")

    def _extract_events(self, result: dict) -> list:
        events = []
        pre = result.get('precondition_result', {})
        for i, c in enumerate(pre.get('checks', [])):
            events.append({
                "phase": "precondition", "index": i,
                "passed": c.get('passed'), "expression": c.get('expression', '')
            })

        post = result.get('postcondition_result', {})
        for i, c in enumerate(post.get('checks', [])):
            events.append({
                "phase": "postcondition", "index": i,
                "passed": c.get('passed'), "expression": c.get('expression', '')
            })

        for err in result.get('errors', []):
            events.append({"phase": "error", "detail": err})

        return events

    def _extract_intermediate_states(self, result: dict) -> list:
        return [{"phase": "input", "data": result.get('inputs', {})},
                {"phase": "output", "data": result.get('outputs', {})}]

    def _compute_trace_hash(self, trace: dict) -> str:
        fields = ['trace_id', 'artifact_id', 'spec_id', 'status', 'timing_ms']
        raw = json.dumps({k: trace[k] for k in fields if k in trace},
                         sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()


class N6TraceArchiver:
    """Archive and retrieve traces."""

    def __init__(self):
        self._store = {}

    def archive(self, trace: dict):
        self._store[trace['trace_id']] = trace

    def get(self, trace_id: str) -> Optional[dict]:
        return self._store.get(trace_id)

    def list_by_artifact(self, artifact_id: str) -> list:
        return [t for t in self._store.values() if t['artifact_id'] == artifact_id]

    def list_by_spec(self, spec_id: str) -> list:
        return [t for t in self._store.values() if t['spec_id'] == spec_id]


class N6TraceQuerier:
    """Query traces by status, timing, artifacts."""

    def __init__(self, archiver: N6TraceArchiver):
        self.archiver = archiver

    def successes(self) -> list:
        return [t for t in self.archiver._store.values() if t['status'] == 'OK']

    def failures(self) -> list:
        return [t for t in self.archiver._store.values() if t['status'] in ('FAILED', 'ERROR')]

    def summary(self) -> dict:
        traces = list(self.archiver._store.values())
        return {
            "total": len(traces),
            "ok": sum(1 for t in traces if t['status'] == 'OK'),
            "failed": sum(1 for t in traces if t['status'] == 'FAILED'),
            "error": sum(1 for t in traces if t['status'] == 'ERROR'),
            "avg_timing_ms": sum(t.get('timing_ms', 0) for t in traces) / max(len(traces), 1)
        }


# Smoke
if __name__ == '__main__':
    import sys, os, json as _json
    sys.path.insert(0, os.path.dirname(__file__))
    from n1_functionspec_parser import N1FunctionSpecParser
    from n2_representation import N2RepresentationEncoder
    from n3_compiler import N3SymbolicCompiler
    from n4_artifact_packager import N4ArtifactPackager
    # Fix n5 import for smoke test
    import sys as _sys
    import n1_safe_expression_dsl as _n1dsl
    _fos = type(_sys)('function_os')
    _fos.n1_safe_expression_dsl = _n1dsl
    _sys.modules['function_os'] = _fos
    from n5_interpreter import N5Interpreter


    parser, encoder = N1FunctionSpecParser(), N2RepresentationEncoder()
    spec = parser.parse(_json.dumps({
        "function_id":"FN-20260715-0001","spec_version":"1.0.0","name":"add","domain":"symbolic",
        "inputs":{"x":"integer","y":"integer"},"outputs":{"result":"integer"},
        "preconditions":[{"expression":"x >= 0","message":"x"}],
        "postconditions":[{"expression":"result == x + y","message":"r"}],
        "effects_declared":["pure"],"created_at":"2026-07-15T12:00:00Z"
    }))
    compiler, packager, interpreter = N3SymbolicCompiler(), N4ArtifactPackager(), N5Interpreter()
    rep = encoder.encode(spec)
    artifact = packager.package(compiler.compile(spec, rep), spec, rep)

    capture = N6TraceCapture()
    archiver = N6TraceArchiver()
    querier = N6TraceQuerier(archiver)

    result = interpreter.execute(artifact, {"x": 3, "y": 7})
    trace = capture.capture(result, spec)
    archiver.archive(trace)

    print("Trace:", trace['trace_id'], "status:", trace['status'])
    print("Events:", len(trace['events']))
    print("Query summary:", querier.summary())
    print("N6: ALL OK")
