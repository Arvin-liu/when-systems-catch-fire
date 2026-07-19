#!/usr/bin/env python3
"""Deterministic Q32I planner built on the Q32 propagation primitives."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT))
from tools.operations.compute_change_propagation import load_json, normalize_repo_path, resolve_paths, traverse_fixpoint, derive_surfaces
from tools.operations.validate_incremental_execution import authority_fingerprint, compute_plan_hash
REGISTRY=ROOT/'data/operations/project-components.json'; TOPOLOGY=ROOT/'data/operations/change-propagation-topology.json'; SURFACES=ROOT/'data/operations/synchronization-surfaces.json'; PROFILES=ROOT/'data/operations/component-execution-profiles.json'
META={str(x) for x in [REGISTRY.relative_to(ROOT),TOPOLOGY.relative_to(ROOT),PROFILES.relative_to(ROOT),Path('data/operations/component-execution-profile-policies.json'),Path('tools/operations/generate_component_profiles.py'),Path('tools/operations/plan_incremental_execution.py'),Path('tools/operations/run_incremental_execution.py'),Path('tools/operations/validate_incremental_execution.py'),Path('schemas/operations/project-components.schema.json'),Path('schemas/operations/change-propagation-topology.schema.json'),Path('schemas/operations/component-execution-profile.schema.json'),Path('schemas/operations/incremental-execution-plan.schema.json'),Path('schemas/operations/non-impact-proof.schema.json')]}
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() and p.is_file() else None
def plan(request):
  components_doc,topology,surfaces,profiles=map(load_json,[REGISTRY,TOPOLOGY,SURFACES,PROFILES]); components={c['component_id']:c for c in components_doc['components']}
  raw=request['changed_paths']; normalized=[]; residue=[]
  for x in raw:
    try: normalized.append(normalize_repo_path(x))
    except ValueError as e: residue.append({'type':'invalid_path','path':x,'message':str(e)})
  seeds,path_residue=resolve_paths(normalized,components,components_doc.get('allowed_path_overlaps',[])); residue+=path_residue
  full=sorted(set(normalized)&META)
  if residue: full.append('unresolved_or_unknown_path')
  dims=set(request.get('changed_dimensions',['identity'])); classes=set(request.get('change_classifications',['EVIDENCE_UPDATE']))
  affected,typed,_,cycle=traverse_fixpoint(seeds,topology,dims,classes); residue+=cycle
  profile_by={p['component_id']:p for p in profiles['profiles']}; authority=authority_fingerprint(REGISTRY,TOPOLOGY,PROFILES)
  missing=sorted(set(components)-set(profile_by));
  if missing: full += ['missing_execution_profile']
  decisions=[]
  for cid in sorted(components):
    p=profile_by.get(cid,{})
    if full: decision='FULL_REBUILD_REQUIRED'; proof=None
    elif cid in affected: decision='REBUILD' if p.get('execution_kind')=='automatic' else 'REVALIDATE'; proof=None
    else:
      decision='NO_CHANGE_WITH_PROOF'; proof={'component_id':cid,'basis':'not in Q32 typed declared closure','unchanged_authoritative_input_fingerprints':[{'path':x,'sha256':digest(ROOT/x)} for x in components[cid]['path_patterns'] if digest(ROOT/x)],'unchanged_dependency_fingerprints':[],'traversed_declared_relations':[x['relation_id'] for x in typed],'excluded_declared_relations':[],'excluded_trigger_dimensions':sorted(dims),'proof_method':'Q32 typed closure exclusion plus registered fingerprint policy','plan_hash':'<bound-to-canonical-plan-hash>','authority_fingerprint':authority,'expiry_or_recheck_condition':'any profile, registry, topology, producer, validator, or input change','claim_ceiling':'non-impact proof is repository-scoped only'}
    decisions.append({'component_id':cid,'decision':decision,'non_impact_proof':proof})
  result={'schema_version':'1.0.0','request_identity':request.get('task_id','adhoc'),'authority_fingerprint':authority,'normalized_change_seeds':normalized,'q32_affected_component_closure':sorted(affected),'affected_synchronization_surfaces':derive_surfaces(surfaces,dims,classes),'component_decisions':decisions,'full_rebuild_reasons':sorted(set(full)),'unresolved_residue':residue,'execution_order':[x['component_id'] for x in decisions if x['decision']=='REBUILD'],'concurrency_constraints':['execute in deterministic listed order'], 'preconditions':['clean tree or isolated worktree for apply'], 'rollback_plan':'executor must restore complete repository byte, type, symlink, and mode state or emit a recovery package','claim_ceiling':'declared repository dependency planning only; not truth or causal proof'}
  for label in ('rebuild','revalidate','sync_metadata','no_change','full_rebuild'):
    target={'rebuild':'REBUILD','revalidate':'REVALIDATE','sync_metadata':'SYNC_METADATA','no_change':'NO_CHANGE_WITH_PROOF','full_rebuild':'FULL_REBUILD_REQUIRED'}[label]; result[label+'_components']=[x['component_id'] for x in decisions if x['decision']==target]
  result['plan_hash']=compute_plan_hash(result)
  for item in result['component_decisions']:
   if item['non_impact_proof'] is not None: item['non_impact_proof']['plan_hash']=result['plan_hash']
  return result
def main():
 p=argparse.ArgumentParser();p.add_argument('--request',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--summary',type=Path);p.add_argument('--check',action='store_true');a=p.parse_args(); payload=json.dumps(plan(load_json(a.request)),ensure_ascii=False,indent=2,sort_keys=True)+'\n';
 if a.check:
  if not a.output.is_file() or a.output.read_text()!=payload: raise SystemExit('stale plan')
 else: a.output.write_text(payload)
 if a.summary: a.summary.write_text('Incremental execution plan: '+json.loads(payload)['plan_hash']+'\n')
if __name__=='__main__': main()
