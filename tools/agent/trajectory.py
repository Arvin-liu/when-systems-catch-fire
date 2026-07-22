#!/usr/bin/env python3
"""Q35 append-only action trajectory helpers.

Build and verify hash-linked, append-only trajectories. Correction/supersession is
expressed by appending new events, never by editing history. No blockchain or
external infrastructure required.
"""
import hashlib
import json


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def event_digest(payload, prev_digest):
    return "sha256:" + hashlib.sha256((canonical(payload) + "|" + prev_digest).encode()).hexdigest()


def build_event(seq, action_id, phase, actor, payload, prev_event, at, exact_head=None, artifact_digest=None, event_id=None):
    prev = "GENESIS" if prev_event is None else prev_event["event_digest"]
    ev = {
        "seq": seq,
        "event_id": event_id or f"ev-{seq:04d}",
        "action_id": action_id,
        "phase": phase,
        "actor": actor,
        "payload": payload,
        "prev_digest": prev,
        "at": at,
    }
    if exact_head:
        ev["exact_head"] = exact_head
    if artifact_digest:
        ev["artifact_digest"] = artifact_digest
    ev["event_digest"] = event_digest(payload, prev)
    return ev


def append_event(trajectory, action_id, phase, actor, payload, at, exact_head=None, artifact_digest=None):
    prev = trajectory[-1] if trajectory else None
    seq = len(trajectory)
    return build_event(seq, action_id, phase, actor, payload, prev, at, exact_head, artifact_digest)
