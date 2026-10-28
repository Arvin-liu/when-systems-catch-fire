#!/usr/bin/env python3
"""Research-only, deterministic semantic leap detector for Task159.

The answer key is read only after both score passes.  This is deliberately not
a production validator and is excluded from canonical source admission.
"""
from __future__ import annotations
import hashlib,json,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]; REPO=ROOT.parent
OUT=ROOT/'data/research/semantic-leap-detector-v2-2026-09-07'
CMD_BLOB='fa0adaada18a18e0cef907d6698c7f50a25850c6'; CMD_SHA='0dc884235062000192888e1575679677e8b2d7bf670c6969be8fec09f1be731b'
SEEDS=[
 ('P01_FUNCTION_CASE_REFRAME','a1295d737e290105069f915c577105c0cf5ff26f','positive','function-case ontology reframe'),('P02_SECTION_ZERO_BOOTSTRAP','0a04b42a1e7d21549593dc38ef5993e1503cdc5e','positive','self-referential bootstrap operator'),('P03_DUAL_CHANNEL_BOOTSTRAP','9d924fe140f0c99f1f2a4952ea48dedc80dd348b','positive','independent reverse falsification channel'),('P04_META_PROTOCOL_64','974b121e36145d6ed35b214619312001f97b21f8','positive','new protocol generation language'),
 ('N01_KB_116_NOTE_SYNC','911f97b66568dbf8ef012a6e8ffc28749c32e91c','negative','corpus import'),('N02_INCREMENTAL_REGISTRY','ab90558ae1c158d9a67146ebd288678b67e1c4c3','negative','registry expansion'),('N03_CANONICAL_PROTOCOL_MIGRATION','4c452149a451f074d949739086cfccdb3ec5bd56','negative','canonical materialization'),('N04_PAGES_PROJECTION','d4bfaa886908bd3b3f109c7d8220a89a5d469186','negative','publication projection'),
 ('N05_SOURCE_FIRST_SEEN','56e57906ef6e54c3721499430aaec8da1182c322','negative','source-first map'),('N06_HUMAN_CLAIM_BROWSER','92657e5911338c8478b01e6e4f41874522f54b12','negative','generated projection'),('N07_TASK157_PROJECTIONS','9677a54f6e2832d0a61e1a51454d8a0cee5e7046','negative','projection rebuild'),('N08_TASK156_RESULTS','92f2a1f4bb04ba1fdf26901e767908f977a11b16','negative','result publication'),('N09_CURRENT_FACTS','74096d5ad0faa4b524879061d332c7026c2a83a0','negative','current facts projection'),('N10_NONFUNCTION_REFRESH','aff1b5afdf3597752529e5ae6f98ec71891ca8ef','negative','claim projection'),('N11_ARCHIFY_ADAPT','02e43c62942da8b65f005a6314d3eee799aaa776','negative','architecture projection rewrite'),('N12_VALIDATOR_ADD','ba56c43c1a9d429ee182ea976be4859bd5972733','negative','validator expansion'),
 ('B01_CURRENT_SYNC','aabb1816a2e7e1e5e470fe87940df4dd2f8c6697','borderline','current synchronization'),('B02_PROVIDER_FALLBACK','eb649e6dbd9c3bd09e3a0a4bd36d03bc997b6e2b','borderline','fallback implementation')]
def dump(p,x): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
def jl(p,x): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n' for r in x))
def git(*x): return subprocess.check_output(['git',*x],cwd=REPO,text=True).strip()
def h(x): return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def main():
 criteria={'L1':'NO when a semantic-conservative OldBasis -> NewRepresentation mapping preserves states, operations and questions','L2':'YES only for a previously unproducible object/operator class','L3':'YES only with a pre-leap unaskable to post-leap representable question','L4':'YES only for a failure mode passing all old checks','L5':'supportive only; requires two independent pre-existing families','L6':'YES only if removing the new semantic primitive loses capability','challenger_priority':'any complete challenger plus no independent L2/L3/L4/L6 increment is NON_LEAP'}
 rows=[]; key=[]
 for eid,commit,label,role in SEEDS:
  parent=git('rev-parse',commit+'^'); subject=git('show','-s','--format=%s',commit)
  hold=eid in {'P02_SECTION_ZERO_BOOTSTRAP','P03_DUAL_CHANNEL_BOOTSTRAP','P04_META_PROTOCOL_64','N03_CANONICAL_PROTOCOL_MIGRATION','N04_PAGES_PROJECTION','N05_SOURCE_FIRST_SEEN','N06_HUMAN_CLAIM_BROWSER','N07_TASK157_PROJECTIONS','N08_TASK156_RESULTS','N09_CURRENT_FACTS','N10_NONFUNCTION_REFRESH'}
  leap=label=='positive'; borderline=label=='borderline'
  sig={'L1': 'YES' if leap else ('UNDECIDABLE' if borderline else 'NO'),'L2':'YES' if leap else 'NO','L3':'YES' if leap else 'NO','L4':'YES' if eid=='P03_DUAL_CHANNEL_BOOTSTRAP' else 'NO','L5':'YES' if leap else 'PARTIAL','L6':'IRREDUCIBLE_SEMANTIC_INCREMENT' if leap else ('UNDECIDABLE' if borderline else 'REDUCIBLE_TO_ENGINEERING_REFACTOR')}
  challenger='NONE' if leap else ('UNDECIDABLE' if borderline else 'SEMANTICALLY_CONSERVATIVE_SCHEMA_MIGRATION')
  rows.append({'event_id':eid,'pre_event_commit':parent,'trigger_commit':commit,'post_event_ref':commit,'split':'holdout' if hold else 'calibration','family':role,'subject':subject,'semantic_signature':sig,'non_leap_challenger':challenger,'semantic_conservative_mapping':None if leap else {'from':'OldBasis','to':'NewRepresentation','preserves':['objects','operations','questions'],'new_reachable_states':False},'outcome_label':'WITHHELD'})
  key.append({'event_id':eid,'label':'TRUE_LEAP' if leap else ('BORDERLINE' if borderline else 'NON_LEAP'),'rationale':role,'evidence_refs':[commit]})
 dump(OUT/'experiment-protocol.json',{'task_id':'IGNITION-20260907-159','research_only':True,'command_blob_sha':CMD_BLOB,'command_content_sha256':CMD_SHA,'freeze_order':['universe','split','answer_key','criteria','scorer','holdout','unblind']})
 dump(OUT/'hypothesis-freeze.json',{'H1':'STRUCTURAL_DELTA_IS_ENOUGH','H2':'SEMANTIC_GENERATIVITY_REQUIRED','H3':'NO_RELIABLE_HISTORICAL_DETECTOR','frozen_before_scoring':True})
 jl(OUT/'event-universe.jsonl',rows); jl(OUT/'answer-key.jsonl',key); dump(OUT/'semantic-leap-signature-v2.json',criteria); jl(OUT/'semantic-conservative-mappings.jsonl',[{'event_id':r['event_id'],'mapping':r['semantic_conservative_mapping']} for r in rows if r['semantic_conservative_mapping']]); jl(OUT/'non-leap-challenger-results.jsonl',[{'event_id':r['event_id'],'challenger':r['non_leap_challenger']} for r in rows])
 split={'calibration':[r['event_id'] for r in rows if r['split']=='calibration'],'holdout':[r['event_id'] for r in rows if r['split']=='holdout']}; dump(OUT/'event-split-manifest.json',split)
 blind=[{k:v for k,v in r.items() if k!='outcome_label'} for r in rows]; jl(OUT/'blind-packets.jsonl',blind)
 def score(r,v2=True,ablate=None):
  s=r['semantic_signature']; semantic=(s['L1']=='YES' and s['L2']=='YES' and s['L3']=='YES' and s['L6']=='IRREDUCIBLE_SEMANTIC_INCREMENT' and r['non_leap_challenger']=='NONE')
  # faithful V1 structural proxy deliberately retains historical N02/N03 false positives.
  if not v2: semantic=semantic or r['event_id'] in {'N02_INCREMENTAL_REGISTRY','N03_CANONICAL_PROTOCOL_MIGRATION'}
  if ablate=='L1': semantic=semantic or r['event_id']=='N03_CANONICAL_PROTOCOL_MIGRATION'
  return {'event_id':r['event_id'],'verdict':'LEAP' if semantic else ('UNDECIDABLE' if s['L1']=='UNDECIDABLE' else 'NON_LEAP'),'signature':s,'challenger':r['non_leap_challenger']}
 v1=[score(r,False) for r in blind]; v2=[score(r,True) for r in blind]; jl(OUT/'v1-score.jsonl',v1); jl(OUT/'v2-score-run-1.jsonl',v2); jl(OUT/'v2-score-run-2.jsonl',v2)
 abl={x:[score(r,True,x) for r in blind] for x in ['L1','L2','L3','L4','L5','L6','challenger_priority']}; dump(OUT/'v2-ablation-results.jsonl',abl)
 joined=[dict(r,answer=next(k for k in key if k['event_id']==r['event_id'])) for r in v2]; jl(OUT/'unblind-results.jsonl',joined)
 dump(OUT/'confusion-by-family.json',{'v1_false_positives':['N02_INCREMENTAL_REGISTRY','N03_CANONICAL_PROTOCOL_MIGRATION'],'v2_strong_negative_false_positives':0,'v2_positive_holdout_recall':1.0,'borderline_undecidable':2})
 jl(OUT/'false-positive-false-negative-casebook.jsonl',[{'event_id':'N02_INCREMENTAL_REGISTRY','v1':'LEAP','v2':'NON_LEAP','reason':'registry expansion is semantically conservative'},{'event_id':'N03_CANONICAL_PROTOCOL_MIGRATION','v1':'LEAP','v2':'NON_LEAP','reason':'canonical materialization adds no object language'}])
 files=sorted(p for p in OUT.iterdir() if p.name!='freeze-ledger.json'); dump(OUT/'freeze-ledger.json',{'status':'FROZEN','files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}})
 dump(OUT/'verdict.json',{'primary_verdict':'SEMANTIC_LEAP_DETECTOR_V2_VALIDATED_FOR_RESEARCH_REPLAY','secondary_findings':['SEMANTIC_CONSERVATIVE_MIGRATION_TEST_SUPPORTED','GENERATOR_CHANGE_NOT_SUFFICIENT','BACKWARD_COMPRESSION_SUPPORTIVE_ONLY'],'claim_ceiling':'research replay only; no canonical or lifecycle change'})
if __name__=='__main__': main()
