#!/usr/bin/env python3
"""Create one condition-blind evaluator packet from an immutable transfer response."""
from __future__ import annotations
import argparse, json, re, subprocess, sys
from pathlib import Path

REPO=Path(__file__).resolve().parents[5]
SUBTREE=REPO/"ignition/reports/evaluations/ignition-227-cognitive-evolution-component-isolation-r0"
PATTERNS=[
 re.compile(r"\b(?:M0_ONLY|M0_PLUS_E1|REFERENCE_M1|M0\s*\+\s*E1)\b",re.I),
 re.compile(r"\b(?:CE-)?F\d{2}-E[01]-[A-Z0-9_-]+\b",re.I),
 re.compile(r"\b(?:M0|E1|M1)\b",re.I),
 re.compile(r"\b(?:OBS|VAL|CAL)-\d{2,}\b",re.I),
 re.compile(r"\b(?:RL-\d{3}|REF-\d{2}|REV-\d{2}|POLICY[-_][A-Z0-9_-]+)\b",re.I),
 re.compile(r"\bTask22[0-9]\b",re.I),
 re.compile(r"(?i)\b(?:m0\.md|revision-evidence-e1\.md|policy-schema\.json|response-schema\.json)\b")
]
REPLACEMENT="[neutralized-reference]"

def redact_text(value:str)->tuple[str,int]:
    count=0
    for pattern in PATTERNS:
        value,n=pattern.subn(REPLACEMENT,value);count+=n
    return value,count

def validate(path:Path):
    proc=subprocess.run([sys.executable,str(SUBTREE/"tools/validate_transfer_response.py"),str(path)],cwd=REPO,text=True,capture_output=True)
    if proc.returncode!=0:return None
    return json.loads(path.read_text(encoding="utf-8"))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--opaque-response-id",required=True)
    ap.add_argument("input",type=Path)
    ap.add_argument("output",type=Path)
    args=ap.parse_args()
    raw=validate(args.input)
    if raw is None:
        packet={"opaque_response_id":args.opaque_response_id,"valid_response":False,"responses":None,"sanitizer_version":"TASK227-TRANSFER-BLIND-V1"}
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(packet,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print("TASK227_BLIND_PACKET=INVALID_RESPONSE_SENTINEL")
        return
    cleaned={};count=0
    for case,row in raw["responses"].items():
        cleaned[case]={}
        for key,value in row.items():
            if isinstance(value,str):
                value,n=redact_text(value);count+=n
            elif isinstance(value,list):
                values=[]
                for item in value:
                    if isinstance(item,str):
                        item,n=redact_text(item);count+=n
                    values.append(item)
                value=values
            cleaned[case][key]=value
    packet={"opaque_response_id":args.opaque_response_id,"valid_response":True,"responses":cleaned,"sanitizer_version":"TASK227-TRANSFER-BLIND-V1"}
    serialized=json.dumps(packet,ensure_ascii=False)
    if any(pattern.search(serialized) for pattern in PATTERNS):
        raise SystemExit("TASK227_BLIND_SANITIZATION_FAILED: residual condition/source token")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(packet,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("TASK227_BLIND_PACKET=PASS")
    print("RESIDUAL_CONDITION_OR_SOURCE_TOKENS=0")

if __name__=="__main__":main()
