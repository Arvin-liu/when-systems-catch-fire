#!/usr/bin/env python3
"""Deterministic Q32I planner built on the Q32 propagation primitives."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT))
from tools.operations.compute_change_propagation import load_json, normalize_repo_path, resolve_paths, traverse_fixpoint, derive_surfaces
REGISTRY=ROOT/'data/operations/project-components.json'; TOPOLOGY=ROOT/'data/operations/change-propagation-topology.json'; SURFACES=ROOT/'data/operations/synchronization-surfaces.json'; PROFILES=ROOT/'data/operations/component-execution-profiles.json'
META={str(x) for x in [REGISTRY.relative_to(ROOT),TOPOLOGY.relative_to(ROOT),PROFILES.relative_to(ROOT),Path('tools/operations/plan_incremental_execution.py'),Path('tools/operations/run_incremental_execution.py'),Path('tools/operations/validate_incremental_execution.py'),Path('schemas/operations/component-execution-profile.schema.json'),Path('schemas/operations/incremental-execution-plan.schema.json'),Path('schemas/operations/non-impact-proof.schema.json')]}
def canon(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() and p.is_file() else None
def plan(request):
  components_doc,topology,surfaces,profiles=map(load_json,[REGISTRY,TOPOLOGY,SURFACES,PROFILES]); components={c['component_id']:c for c in components_doc['components']}
  raw=request['changed_paths']; normalized=[]; residue=[]
  for x in raw:
    try: normalized.append(normalize_repo_path(x))
    except ValueError as e: residue.append({'type':'invalid_path','path':x,'message':str(e)})
  seeds,path_residue=resolve_paths(normalized,components,components_doc.get('allowed_path_overlaps',[])); residue+=path_residue
  full=sorted(set(normalized)&META)
  dims=set(request.get('changed_dimensions',['identity'])); classes=set(request.get('change_classifications',['EVIDENCE_UPDATE']))
  affected,typed,_,cycle=traverse_fixpoint(seeds,topology,dims,classes); residue+=cycle
  profile_by={p['component_id']:p for p in profiles['profiles']}
  missing=sorted(set(components)-set(profile_by));
  if missing: full += ['missing_execution_profile']
  decisions=[]
  for cid in sorted(components):
    p=profile_by.get(cid,{})
    if full: decision='FULL_REBUILD_REQUIRED'; proof=None
    elif cid in affected: decision='REBUILD' if p.get('execution_kind')=='automatic' else 'REVALIDATE'; proof=None
    else:
      decision='NO_CHANGE_WITH_PROOF'; proof={'component_id':cid,'basis':'not in Q32 typed declared closure','unchanged_authoritative_input_fingerprints':[{'path':x,'sha256':digest(ROOT/x)} for x in components[cid]['path_patterns'] if digest(ROOT/x)],'claim_ceiling':'non-impact proof is repository-scoped only'}
    decisions.append({'component_id':cid,'decision':decision,'non_impact_proof':proof})
  result={'schema_version':'1.0.0','normalized_change_seeds':normalized,'q32_affected_component_closure':sorted(affected),'affected_synchronization_surfaces':derive_surfaces(surfaces,dims,classes),'component_decisions':decisions,'full_rebuild_reasons':sorted(set(full)),'unresolved_residue':residue,'execution_order':[x['component_id'] for x in decisions if x['decision']=='REBUILD'],'claim_ceiling':'declared repository dependency planning only; not truth or causal proof'}
  result['plan_hash']=hashlib.sha256(canon(result).encode()).hexdigest(); return result
def main():
 p=argparse.ArgumentParser();p.add_argument('--request',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.write_text(json.dumps(plan(load_json(a.request)),ensure_ascii=False,indent=2,sort_keys=True)+'\n')
if __name__=='__main__': main()
