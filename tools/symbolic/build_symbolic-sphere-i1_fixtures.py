#!/usr/bin/env python3
"""Build the SYMBOLIC-SPHERE-I1 repair-r1 pilot and attack fixtures."""
import argparse
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PILOT = ROOT / "data/symbolic/pilot-symbolic-sphere-i1.json"
FIXTURES = ROOT / "data/symbolic/fixtures"
EVIDENCE_COMMIT = "2d5afb3f1dbbc61d5d35d0c733da13af977a6ffb"
EVIDENCE_PATH = "data/symbolic/symbolic-evidence-object-registry.json"
Q39_REPAIR_HEAD = "99ab601a48dd45972b238e468bc8e3002d648c98"


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True)


def repository_binding():
    line = git("ls-tree", EVIDENCE_COMMIT, "--", EVIDENCE_PATH).stdout.decode().strip()
    metadata, path = line.split("\t", 1)
    _, object_type, blob_sha = metadata.split()
    if path != EVIDENCE_PATH or object_type != "blob":
        raise RuntimeError("symbolic evidence registry is not a Git blob")
    content = git("cat-file", "blob", blob_sha).stdout
    return blob_sha, "sha256:" + hashlib.sha256(content).hexdigest()


def reference(reference_id, object_id, role, blob_sha, sha256):
    return {
        "reference_id": reference_id,
        "repository_relative_path": EVIDENCE_PATH,
        "commit_sha": EVIDENCE_COMMIT,
        "blob_sha": blob_sha,
        "sha256": sha256,
        "record_type": "SYMBOLIC_EVIDENCE_OBJECT",
        "declared_role": role,
        "object_id": object_id,
    }


def community_record():
    positions = [
        ("council", "ref.community.actor.council", "Official stewardship and scheduling"),
        ("players", "ref.community.actor.players", "Belonging through repeated use"),
        ("neighbours", "ref.community.actor.neighbours", "Unequal noise and access costs"),
    ]
    return {
        "record_id": "analysis.community_field",
        "record_type": "COMMUNITY_FOOTBALL_FIELD",
        "symbolic_object_ref": "ref.community.material_object",
        "actor_positions": [
            {
                "position_id": f"community.position.{name}",
                "actor_ref": actor_ref,
                "stance": stance,
                "evidence_refs": ["ref.community.meaning_evidence"],
            }
            for name, actor_ref, stance in positions
        ],
        "meaning_projections": [
            {
                "projection_id": f"community.meaning.{name}",
                "actor_position_id": f"community.position.{name}",
                "symbolic_object_ref": "ref.community.material_object",
                "statement": statement,
                "evidence_refs": ["ref.community.meaning_evidence"],
            }
            for name, statement in (
                ("council", "The field represents managed community provision."),
                ("players", "The field represents belonging and shared play."),
                ("neighbours", "The field represents costs imposed without equal voice."),
            )
        ],
        "power_modalities": [
            {
                "modality": "ACCESS_CONTROL",
                "actor_position_id": "community.position.council",
                "statement": "The council controls the booking window.",
                "evidence_refs": ["ref.community.power_evidence"],
            },
            {
                "modality": "NAMING_AUTHORITY",
                "actor_position_id": "community.position.council",
                "statement": "The council supplies the official community label, which does not establish truth.",
                "evidence_refs": ["ref.community.power_evidence"],
            },
            {
                "modality": "POPULARITY",
                "actor_position_id": "community.position.players",
                "statement": "Frequent use indicates popularity, not truth or legitimacy.",
                "evidence_refs": ["ref.community.power_evidence"],
            },
        ],
        "front_face": {
            "face_id": "community.face.front",
            "statement": "A shared field visibly supports community play.",
            "actor_position_ids": ["community.position.council", "community.position.players"],
            "evidence_refs": ["ref.community.face_evidence"],
        },
        "suppressed_face": {
            "face_id": "community.face.suppressed",
            "statement": "The same schedule can hide unequal noise and access costs.",
            "actor_position_ids": ["community.position.neighbours"],
            "evidence_refs": ["ref.community.face_evidence"],
        },
        "benefit_cost_distribution": {
            "beneficiaries": [
                {
                    "actor_position_id": "community.position.players",
                    "effect": "Receives scheduled access and a public belonging narrative.",
                    "evidence_refs": ["ref.community.distribution_evidence"],
                }
            ],
            "cost_bearers": [
                {
                    "actor_position_id": "community.position.neighbours",
                    "effect": "Bears bounded noise and reduced quiet-time access.",
                    "evidence_refs": ["ref.community.distribution_evidence"],
                }
            ],
            "evidence_refs": ["ref.community.distribution_evidence"],
        },
        "counter_readings": [
            {
                "counter_reading_id": "community.counter.unequal_access",
                "target_projection_id": "community.meaning.players",
                "statement": "Belonging for frequent users can coexist with exclusion and shifted costs.",
                "evidence_refs": ["ref.community.counter_reading_evidence"],
            }
        ],
        "material_evidence_constraint": {
            "status": "SATISFIED",
            "material_evidence_refs": ["ref.community.material_evidence"],
            "unmet_requirements": [],
            "downgrade_claim_ceiling": "INSUFFICIENT_MATERIAL_EVIDENCE",
        },
    }


def school_record():
    positions = [
        ("school", "ref.school.actor.school", "Safety and administrative consistency"),
        ("students", "ref.school.actor.students", "Classification and loss of agency"),
        ("families", "ref.school.actor.families", "Oversight and correction burden"),
    ]
    return {
        "record_id": "analysis.school_policy",
        "record_type": "SCHOOL_DATA_POLICY",
        "symbolic_object_ref": "ref.school.material_object",
        "actor_positions": [
            {
                "position_id": f"school.position.{name}",
                "actor_ref": actor_ref,
                "stance": stance,
                "evidence_refs": ["ref.school.meaning_evidence"],
            }
            for name, actor_ref, stance in positions
        ],
        "meaning_projections": [
            {
                "projection_id": f"school.meaning.{name}",
                "actor_position_id": f"school.position.{name}",
                "symbolic_object_ref": "ref.school.material_object",
                "statement": statement,
                "evidence_refs": ["ref.school.meaning_evidence"],
            }
            for name, statement in (
                ("school", "The policy represents safety and consistent administration."),
                ("students", "The policy represents classification and reduced agency."),
                ("families", "The policy represents oversight coupled to correction work."),
            )
        ],
        "power_modalities": [
            {
                "modality": "INSTITUTIONAL_AUTHORITY",
                "actor_position_id": "school.position.school",
                "statement": "The school can adopt the policy, but institutional adoption does not make classifications factual.",
                "evidence_refs": ["ref.school.power_evidence"],
            },
            {
                "modality": "NAMING_AUTHORITY",
                "actor_position_id": "school.position.school",
                "statement": "The official safety label does not establish truth.",
                "evidence_refs": ["ref.school.power_evidence"],
            },
            {
                "modality": "OWNERSHIP",
                "actor_position_id": "school.position.school",
                "statement": "Administrative custody is recorded without treating ownership as truth.",
                "evidence_refs": ["ref.school.power_evidence"],
            },
        ],
        "front_face": {
            "face_id": "school.face.front",
            "statement": "The policy visibly promises safety and consistency.",
            "actor_position_ids": ["school.position.school"],
            "evidence_refs": ["ref.school.face_evidence"],
        },
        "suppressed_face": {
            "face_id": "school.face.suppressed",
            "statement": "The same policy can hide classification errors and correction costs.",
            "actor_position_ids": ["school.position.students", "school.position.families"],
            "evidence_refs": ["ref.school.face_evidence"],
        },
        "benefit_cost_distribution": {
            "beneficiaries": [
                {
                    "actor_position_id": "school.position.school",
                    "effect": "Receives a standardized administration and safety narrative.",
                    "evidence_refs": ["ref.school.distribution_evidence"],
                }
            ],
            "cost_bearers": [
                {
                    "actor_position_id": "school.position.students",
                    "effect": "Bears classification and access consequences.",
                    "evidence_refs": ["ref.school.distribution_evidence"],
                },
                {
                    "actor_position_id": "school.position.families",
                    "effect": "Bears notice review and correction work.",
                    "evidence_refs": ["ref.school.distribution_evidence"],
                },
            ],
            "evidence_refs": ["ref.school.distribution_evidence"],
        },
        "counter_readings": [
            {
                "counter_reading_id": "school.counter.proportionality",
                "target_projection_id": "school.meaning.school",
                "statement": "A safety label alone does not establish proportionality, accuracy, or truth.",
                "evidence_refs": ["ref.school.counter_reading_evidence"],
            }
        ],
        "material_evidence_constraint": {
            "status": "SATISFIED",
            "material_evidence_refs": ["ref.school.material_evidence"],
            "unmet_requirements": [],
            "downgrade_claim_ceiling": "INSUFFICIENT_MATERIAL_EVIDENCE",
        },
    }


def pilot_bundle():
    blob_sha, sha256 = repository_binding()
    objects = [
        ("ref.community.material_object", "community_field.material_object", "MATERIAL_OBJECT"),
        ("ref.community.actor.council", "community_field.actor.council", "ACTOR"),
        ("ref.community.actor.players", "community_field.actor.players", "ACTOR"),
        ("ref.community.actor.neighbours", "community_field.actor.neighbours", "ACTOR"),
        ("ref.community.material_evidence", "community_field.material_evidence", "MATERIAL_EVIDENCE"),
        ("ref.community.meaning_evidence", "community_field.meaning_evidence", "MEANING_EVIDENCE"),
        ("ref.community.power_evidence", "community_field.power_evidence", "POWER_EVIDENCE"),
        ("ref.community.face_evidence", "community_field.face_evidence", "FACE_EVIDENCE"),
        ("ref.community.distribution_evidence", "community_field.distribution_evidence", "DISTRIBUTION_EVIDENCE"),
        ("ref.community.counter_reading_evidence", "community_field.counter_reading_evidence", "COUNTER_READING_EVIDENCE"),
        ("ref.school.material_object", "school_policy.material_object", "MATERIAL_OBJECT"),
        ("ref.school.actor.school", "school_policy.actor.school", "ACTOR"),
        ("ref.school.actor.students", "school_policy.actor.students", "ACTOR"),
        ("ref.school.actor.families", "school_policy.actor.families", "ACTOR"),
        ("ref.school.material_evidence", "school_policy.material_evidence", "MATERIAL_EVIDENCE"),
        ("ref.school.meaning_evidence", "school_policy.meaning_evidence", "MEANING_EVIDENCE"),
        ("ref.school.power_evidence", "school_policy.power_evidence", "POWER_EVIDENCE"),
        ("ref.school.face_evidence", "school_policy.face_evidence", "FACE_EVIDENCE"),
        ("ref.school.distribution_evidence", "school_policy.distribution_evidence", "DISTRIBUTION_EVIDENCE"),
        ("ref.school.counter_reading_evidence", "school_policy.counter_reading_evidence", "COUNTER_READING_EVIDENCE"),
    ]
    return {
        "contract_version": "1.1.0",
        "task_id": "SYMBOLIC-SPHERE-I1",
        "capability_id": "symbolic_power_perspective",
        "parent_binding": {"task_id": "121Q39-REPAIR-R1", "exact_head": Q39_REPAIR_HEAD},
        "reference_records": [
            reference(reference_id, object_id, role, blob_sha, sha256)
            for reference_id, object_id, role in objects
        ],
        "records": [community_record(), school_record()],
        "conclusion": {
            "analysis_status": "BOUNDED_INTERPRETATION",
            "statement": (
                "Repository-bound material objects, explicit actor positions, corresponding meaning projections, "
                "allowed power modalities, distinct faces, visible benefit/cost distribution, and independently "
                "evidenced counter-readings support a bounded symbolic interpretation only."
            ),
            "claim_ceiling": "BOUNDED_SYMBOLIC_INTERPRETATION",
            "truth_status": "NOT_ESTABLISHED",
            "causal_status": "NOT_ESTABLISHED",
            "external_action_performed": False,
        },
    }


def attack_fixtures(pilot):
    fixtures = {}

    def add(name, mutation):
        bundle = copy.deepcopy(pilot)
        mutation(bundle)
        fixtures[name] = bundle

    fixtures["01-valid-exit00.json"] = copy.deepcopy(pilot)
    add("02-missing_required_record-exit02.json", lambda b: b.pop("conclusion"))
    add("03-unresolved_repository_reference-exit04.json", lambda b: b["reference_records"][0].update(repository_relative_path="../outside.json"))
    add("04-blob_mismatch-exit05.json", lambda b: b["reference_records"][0].update(blob_sha="1234567890abcdef1234567890abcdef12345678"))
    add("05-digest_mismatch-exit06.json", lambda b: b["reference_records"][0].update(sha256="sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"))
    add("06-unsupported_reference_record_type-exit07.json", lambda b: b["reference_records"][0].update(record_type="FREE_TEXT_ASSERTION"))
    add("07-declared_role_mismatch-exit08.json", lambda b: b["reference_records"][0].update(declared_role="ACTOR"))
    add("08-unsupported_record_type-exit09.json", lambda b: b["records"][0].update(record_type="UNSUPPORTED_SYMBOLIC_RECORD"))
    add("09-inconsistent_actor_position-exit10.json", lambda b: b["records"][0]["actor_positions"][0].update(actor_ref="ref.community.material_object"))
    add("10-inconsistent_meaning_projection-exit11.json", lambda b: b["records"][0]["meaning_projections"][0].update(actor_position_id="community.position.absent"))
    add("11-unsupported_power_modality-exit12.json", lambda b: b["records"][0]["power_modalities"][0].update(modality="UNBOUNDED_TRUTH_AUTHORITY"))
    add("12-invalid_face_distinction-exit13.json", lambda b: b["records"][0].update(suppressed_face=copy.deepcopy(b["records"][0]["front_face"])))
    add("13-incomplete_benefit_cost_distribution-exit14.json", lambda b: b["records"][0]["benefit_cost_distribution"]["cost_bearers"][0].update(actor_position_id="community.position.absent"))
    add("14-invalid_counter_reading-exit15.json", lambda b: b["records"][0]["counter_readings"][0].update(evidence_refs=["ref.community.meaning_evidence"]))

    def missing_material(b):
        b["records"][0]["material_evidence_constraint"].update(
            status="UNSATISFIED",
            material_evidence_refs=[],
            unmet_requirements=["material observation absent"],
        )
        b["conclusion"].update(
            analysis_status="DOWNGRADED",
            claim_ceiling="INSUFFICIENT_MATERIAL_EVIDENCE",
            truth_status="NOT_ESTABLISHED",
            causal_status="NOT_ESTABLISHED",
        )

    add("15-missing_material_evidence-exit16.json", missing_material)
    add("16-truth_upgrade_forbidden-exit17.json", lambda b: b["conclusion"].update(truth_status="ESTABLISHED_BY_NAMING_AUTHORITY", statement="Naming authority proves truth."))
    add("17-causal_overclaim-exit18.json", lambda b: b["conclusion"].update(causal_status="ESTABLISHED", statement="Symbolic analysis establishes complete causal proof."))
    add("18-placeholder_repository_reference-exit04.json", lambda b: b["reference_records"][0].update(commit_sha="0" * 40, blob_sha="0" * 40, sha256="sha256:" + "0" * 64))
    add("19-external_action_forbidden-exit19.json", lambda b: b["conclusion"].update(external_action_performed=True))
    add("20-invalid_symbolic_object-exit20.json", lambda b: b["records"][0].update(symbolic_object_ref="ref.community.actor.council"))
    return fixtures


def serialized(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    pilot = pilot_bundle()
    fixtures = attack_fixtures(pilot)
    outputs = {PILOT: serialized(pilot)}
    outputs.update({FIXTURES / name: serialized(value) for name, value in fixtures.items()})

    if args.check:
        stale = [str(path.relative_to(ROOT)) for path, text in outputs.items() if not path.is_file() or path.read_text() != text]
        unexpected = sorted(path.name for path in FIXTURES.glob("*.json") if path not in outputs)
        if stale or unexpected:
            print(json.dumps({"status": "STALE", "stale": stale, "unexpected": unexpected}, sort_keys=True))
            return 1
        print(json.dumps({"status": "PASS", "outputs": len(outputs)}, sort_keys=True))
        return 0

    FIXTURES.mkdir(parents=True, exist_ok=True)
    for path in FIXTURES.glob("*.json"):
        if path not in outputs:
            path.unlink()
    for path, text in outputs.items():
        path.write_text(text)
    print(json.dumps({"status": "BUILT", "outputs": len(outputs)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
