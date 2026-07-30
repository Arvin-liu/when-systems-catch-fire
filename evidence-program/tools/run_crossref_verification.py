#!/usr/bin/env python3
"""Task 103 primary pilot runner: independent Crossref re-verification.

For every record in data/external-research/104-source-registry.jsonl that asserts
`crossref_verified: true`, independently re-query the public Crossref REST API and
record, per DOI:
  - resolution (HTTP 200 vs failure)
  - observed title / year
  - title & year match against the registry's recorded crossref_title / crossref_year
  - retraction signal
  - response SHA-256, retrieval timestamp, licence (Crossref metadata is CC0)

Network/non-200 outcomes are recorded explicitly (acquisition_status) and NEVER
silently substituted (relay §6). Output: a source-manifest.jsonl with one provenance
record per DOI, plus a machine summary printed to stdout.

Usage:
  python run_crossref_verification.py \
      --registry data/external-research/104-source-registry.jsonl \
      --out evidence-program/runs/IGNITION-EVIDENCE-PILOT-R1-CROSSREF-DOI-VERIFICATION/source-manifest.jsonl
"""
import argparse
import hashlib
import json
import re
import sys
import time
import urllib.parse
import urllib.request

CROSSREF_ENDPOINT = "https://api.crossref.org/works/"
USER_AGENT = "PointfireEvidencePilot/1.0 (mailto:49422864+Arvin-liu@users.noreply.github.com)"
LICENCE = "Crossref metadata CC0 (public-domain dedication); raw redistribution permitted by Crossref terms."
DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+$")


def bare_doi(raw):
    if not raw:
        return None
    s = raw.strip()
    m = DOI_RE.search(s)
    return m.group(0) if m else None


def norm(s):
    if not s:
        return ""
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


def extract_year(msg):
    for key in ("published", "published-print", "issued", "created"):
        v = msg.get(key)
        if isinstance(v, dict) and v.get("date-parts") and v["date-parts"][0]:
            return int(v["date-parts"][0][0])
    return None


def retraction_signal(msg):
    if msg.get("type") == "retraction":
        return "TYPE_RETRACTION"
    rel = msg.get("relation") or {}
    for k in rel.keys():
        if "retract" in k.lower():
            return "RELATION_RETRACTION"
    return "NONE"


def fetch(doi):
    url = CROSSREF_ENDPOINT + urllib.parse.quote(doi, safe="")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                if resp.status != 200:
                    return {"status": resp.status, "body": None, "http_ok": False}
                data = resp.read()
                return {"status": 200, "body": data, "http_ok": True}
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {"status": 404, "body": None, "http_ok": False}
            if e.code == 429:
                time.sleep(2 * (attempt + 1))
                continue
            return {"status": getattr(e, "code", -1), "body": None, "http_ok": False}
        except Exception as e:
            if attempt < 3:
                time.sleep(1.5 * (attempt + 1))
                continue
            return {"status": -1, "body": None, "http_ok": False, "error": str(e)}
    return {"status": 429, "body": None, "http_ok": False, "error": "persistent 429"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0, help="cap number of DOIs (0=all)")
    args = ap.parse_args()

    with open(args.registry, "r", encoding="utf-8") as fh:
        records = [json.loads(ln) for ln in fh if ln.strip()]

    # duplicate-DOI detection across the registry (metadata consistency check)
    doi_to_sids = {}
    for r in records:
        bd = bare_doi(r.get("doi"))
        if bd:
            doi_to_sids.setdefault(bd, []).append(r.get("source_id"))

    out_rows = []
    summary = {
        "total_records": len(records),
        "verified_records": 0,
        "resolved_ok": 0,
        "title_match": 0,
        "year_match": 0,
        "full_match": 0,
        "retraction_signals": 0,
        "resolution_failures": 0,
        "intra_registry_duplicate_dois": sum(1 for v in doi_to_sids.values() if len(v) > 1),
    }

    done = 0
    for r in records:
        if args.limit and done >= args.limit:
            break
        sid = r.get("source_id")
        claimed = r.get("crossref_verified", False)
        bd = bare_doi(r.get("doi"))
        row = {
            "source_id": sid,
            "canonical_identifier": bd,
            "registry_title": r.get("crossref_title"),
            "registry_year": r.get("crossref_year"),
            "registry_claimed_verified": claimed,
            "retrieval_timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "version_or_date": "Crossref REST API live query",
            "licence": LICENCE,
            "raw_redistribution_allowed": True,
        }
        if not bd:
            row.update({"acquisition_status": "PARSE_FAILED",
                        "response_sha256": None, "observed_title": None,
                        "observed_year": None, "title_match": None, "year_match": None,
                        "retraction_signal": None, "notes": "could not parse DOI from registry"})
            out_rows.append(row)
            summary["resolution_failures"] += 1
            done += 1
            continue

        res = fetch(bd)
        if not res["http_ok"]:
            row.update({"acquisition_status": "RESOLUTION_FAILED" if res["status"] in (404, -1) else "NETWORK_ERROR",
                        "response_sha256": None, "observed_title": None, "observed_year": None,
                        "title_match": None, "year_match": None, "retraction_signal": None,
                        "notes": f"Crossref HTTP {res.get('status')} {res.get('error','')}"})
            out_rows.append(row)
            summary["resolution_failures"] += 1
            done += 1
            continue

        body = res["body"]
        sha = hashlib.sha256(body).hexdigest()
        msg = json.loads(body)["message"]
        obs_title = (msg.get("title") or [None])[0]
        obs_year = extract_year(msg)
        retr = retraction_signal(msg)
        tmatch = norm(obs_title) == norm(r.get("crossref_title"))
        ymatch = (obs_year is not None and r.get("crossref_year") is not None and int(obs_year) == int(r.get("crossref_year")))
        dup = len(doi_to_sids.get(bd, [])) > 1
        row.update({
            "acquisition_status": "OK",
            "response_sha256": sha,
            "observed_title": obs_title,
            "observed_year": obs_year,
            "title_match": tmatch,
            "year_match": ymatch,
            "full_match": bool(tmatch and ymatch),
            "retraction_signal": retr,
            "intra_registry_duplicate": dup,
            "notes": "",
        })
        summary["resolved_ok"] += 1
        if claimed:
            summary["verified_records"] += 1
        if tmatch:
            summary["title_match"] += 1
        if ymatch:
            summary["year_match"] += 1
        if tmatch and ymatch:
            summary["full_match"] += 1
        if retr != "NONE":
            summary["retraction_signals"] += 1
        done += 1
        time.sleep(0.1)  # polite pool

    # primary metric: verification match rate among claimed-verified records
    claimed_n = sum(1 for r in records if r.get("crossref_verified"))
    summary["claimed_verified_records"] = claimed_n
    summary["verification_match_rate"] = round(summary["full_match"] / claimed_n, 4) if claimed_n else None
    summary["resolution_rate"] = round(summary["resolved_ok"] / len(records), 4)
    summary["title_match_rate"] = round(summary["title_match"] / claimed_n, 4) if claimed_n else None
    summary["year_match_rate"] = round(summary["year_match"] / claimed_n, 4) if claimed_n else None

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        for row in out_rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


if __name__ == "__main__":
    main()
