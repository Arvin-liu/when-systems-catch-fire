"""N8 Trace Archiver — serializes and persists execution traces."""
import json
from typing import Dict, Any


class N8TraceArchiver:
    def to_json(self, trace: dict) -> str:
        return json.dumps(trace, sort_keys=True, ensure_ascii=False, indent=2)

    def to_compact(self, trace: dict) -> str:
        return json.dumps(trace, sort_keys=True, ensure_ascii=False, separators=(',', ':'))

    def archive(self, trace: dict, output_path: str) -> Dict[str, Any]:
        content = self.to_json(trace)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return {"ok": True, "path": output_path, "size": len(content)}

    def load(self, path: str) -> Dict[str, Any]:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def summary(self, trace: dict) -> Dict[str, Any]:
        events = trace.get('events', [])
        types = {}
        for e in events:
            t = e.get('type', '?')
            types[t] = types.get(t, 0) + 1
        return {
            "total_events": len(events),
            "duration_ms": trace.get('duration_ms', 0),
            "event_types": types,
            "start_time": trace.get('start_time'),
            "end_time": trace.get('end_time')
        }
