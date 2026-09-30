#!/usr/bin/env python3
"""Fail-closed, byte-preserving stdin dispatcher for non-scientific H1 canaries."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone

HEX64 = re.compile(r"^[0-9a-f]{64}$")

def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def write_new(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as f:
        f.write(data)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--expected-sha256", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--cli", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--effort", required=True)
    ap.add_argument("--workspace-parent", required=True)
    args = ap.parse_args()

    src = Path(args.prompt).resolve()
    out = Path(args.output_dir).resolve()
    workspace_parent = Path(args.workspace_parent).resolve()
    receipt_path = out / "dispatch-receipt.json"
    out.mkdir(parents=True, exist_ok=False)
    record = {
        "schema_version": "task229-h1-dispatch-receipt-v1",
        "started_at_utc": utc_now(),
        "source_path": str(src.resolve()),
        "expected_sha256": args.expected_sha256,
        "cli_requested_path": args.cli,
        "model_requested": args.model,
        "reasoning_effort_requested": args.effort,
        "shell": False,
        "stdin_transport": "subprocess.Popen.communicate(input=source_bytes)",
        "freshness": {"resume_subcommand": False, "ephemeral_flag": True},
        "prelaunch": {},
        "process": {},
        "capture": {},
        "status": "NOT_LAUNCHED"
    }
    try:
        if not HEX64.fullmatch(args.expected_sha256):
            raise ValueError("expected SHA-256 must be 64 lowercase hex characters")
        if not args.model.strip() or not args.effort.strip():
            raise ValueError("model and effort must be explicitly configured")
        if src.is_symlink() or not src.is_file():
            raise ValueError("prompt source must be an existing regular non-symlink file")
        source_bytes = src.read_bytes()
        source_hash = hashlib.sha256(source_bytes).hexdigest()
        record["prelaunch"].update({"source_byte_length":len(source_bytes),"source_sha256":source_hash})
        if source_hash != args.expected_sha256:
            raise ValueError("source SHA-256 did not match expected value")
        source_text = source_bytes.decode("utf-8", errors="strict")
        roundtrip = source_text.encode("utf-8", errors="strict")
        if roundtrip != source_bytes:
            raise ValueError("strict UTF-8 round-trip changed source bytes")
        outbound_bytes = roundtrip
        outbound_hash = hashlib.sha256(outbound_bytes).hexdigest()
        if outbound_hash != args.expected_sha256 or outbound_bytes != source_bytes:
            raise ValueError("outbound bytes/hash differ from source")
        cli = shutil.which(args.cli)
        if not cli:
            raise ValueError("CLI executable could not be resolved")
        workspace_parent.mkdir(parents=True, exist_ok=True)
        workspace = Path(tempfile.mkdtemp(prefix="task229-h1-fresh-", dir=str(workspace_parent))).resolve()
        if any(workspace.iterdir()):
            raise ValueError("fresh CLI workspace was not empty")
        run_started = utc_now()
        last_message = out / "last-message.txt"
        argv = [
            cli, "exec", "--ephemeral", "--ignore-user-config", "--ignore-rules", "--strict-config",
            "--model", args.model, "--config", f'model_reasoning_effort="{args.effort}"',
            "--sandbox", "read-only", "--cd", str(workspace), "--skip-git-repo-check",
            "--json", "--color", "never", "--output-last-message", str(last_message), "-"
        ]
        record["prelaunch"].update({
            "strict_utf8_decode": True,
            "utf8_roundtrip_equal": True,
            "outbound_byte_length": len(outbound_bytes),
            "outbound_sha256": outbound_hash,
            "outbound_equals_source": outbound_bytes == source_bytes,
            "cli_resolved_path": str(Path(cli).resolve()),
            "workspace_path": str(workspace),
            "workspace_empty_at_launch": True,
            "command_argv_no_prompt_content": True,
            "argv": argv
        })
        proc = subprocess.Popen(
            argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=str(workspace), shell=False, close_fds=True
        )
        record["process"].update({"pid":proc.pid,"launch_time_utc":run_started,"fresh_process":True})
        timed_out = False
        try:
            stdout, stderr = proc.communicate(input=outbound_bytes, timeout=240)
        except subprocess.TimeoutExpired:
            timed_out = True
            proc.kill()
            stdout, stderr = proc.communicate()
        ended = utc_now()
        write_new(out / "stdout.jsonl", stdout)
        write_new(out / "stderr.txt", stderr)
        last_data = last_message.read_bytes() if last_message.is_file() else None
        if last_data is not None:
            record["capture"]["last_message_file"] = last_message.name
            record["capture"]["last_message_sha256"] = hashlib.sha256(last_data).hexdigest()
        events=[]
        thread_ids=[]
        observed_models=[]
        observed_efforts=[]
        agent_messages=[]
        for line in stdout.decode("utf-8", errors="replace").splitlines():
            try:
                event=json.loads(line)
            except Exception:
                continue
            if isinstance(event,dict):
                et=event.get("type")
                if isinstance(et,str): events.append(et)
                for key in ("thread_id","session_id"):
                    value=event.get(key)
                    if isinstance(value,str): thread_ids.append(value)
                for key in ("model","model_slug"):
                    value=event.get(key)
                    if isinstance(value,str): observed_models.append(value)
                for key in ("reasoning_effort","effort"):
                    value=event.get(key)
                    if isinstance(value,str): observed_efforts.append(value)
                if event.get("type") == "item.completed":
                    item=event.get("item")
                    if isinstance(item,dict) and item.get("type") == "agent_message" and isinstance(item.get("text"),str):
                        agent_messages.append(item["text"])
        record["process"].update({"ended_at_utc":ended,"duration_observed":True,"return_code":proc.returncode,"timed_out":timed_out,"stdin_request_byte_length":len(outbound_bytes),"stdin_request_sha256":outbound_hash,"stdin_pipe_closed_by_communicate":True,"argv_uses_resume":False,"ephemeral_requested":True,"session_ids_observed":sorted(set(thread_ids))})
        record["capture"].update({"stdout_file":"stdout.jsonl","stdout_sha256":hashlib.sha256(stdout).hexdigest(),"stderr_file":"stderr.txt","stderr_sha256":hashlib.sha256(stderr).hexdigest(),"jsonl_event_types":events,"agent_message_count":len(agent_messages),"agent_message_sha256":[hashlib.sha256(m.encode("utf-8","strict")).hexdigest() for m in agent_messages],"observed_models":sorted(set(observed_models)),"observed_efforts":sorted(set(observed_efforts)),"last_message_captured":last_data is not None,"jsonl_final_message_captured":bool(agent_messages) and "turn.completed" in events})
        record["status"] = "COMPLETED" if proc.returncode == 0 and not timed_out and agent_messages and "turn.completed" in events else "CLI_RUN_FAILED_OR_CAPTURE_INCOMPLETE"
    except Exception as e:
        record["failure"] = {"type":type(e).__name__,"message":str(e)}
        record["status"] = "PRELAUNCH_OR_DISPATCH_FAILURE"
    record["finished_at_utc"] = utc_now()
    write_new(receipt_path, (json.dumps(record,ensure_ascii=False,indent=2)+"\n").encode("utf-8"))
    print(json.dumps({"status":record["status"],"receipt":str(receipt_path),"pid":record.get("process",{}).get("pid"),"return_code":record.get("process",{}).get("return_code"),"source_sha256":record.get("prelaunch",{}).get("source_sha256"),"outbound_sha256":record.get("prelaunch",{}).get("outbound_sha256"),"thread_ids":record.get("process",{}).get("session_ids_observed"),"last_message_captured":record.get("capture",{}).get("last_message_captured")},ensure_ascii=False))
    return 0 if record["status"] == "COMPLETED" else 2

if __name__ == "__main__":
    raise SystemExit(main())
