import copy, importlib.util, json, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=json.loads((ROOT/"data/governance/epistemic-governance-relationships.json").read_text())
REPO=ROOT
sp=importlib.util.spec_from_file_location("validator",ROOT/"tools/validate_epistemic_governance_relationships.py")
v=importlib.util.module_from_spec(sp); sp.loader.exec_module(v)

class TestRelationships(unittest.TestCase):
    def check_bad(self, mutate, needle):
        d=copy.deepcopy(SPEC); mutate(d); errors=v.validate(d,REPO)
        self.assertTrue(any(needle in e for e in errors),errors)
    def test_valid(self): self.assertEqual([],v.validate(SPEC,REPO))
    def test_mechanism_m0_collision_is_not_copyable(self): self.check_bad(lambda d:d.update({"mathematical_maturity":"M0"}),"copied local state")
    def test_publication_to_truth_rejected(self): self.check_bad(lambda d:d["relationships"][0].update({"allowed_inference":"publication implies truth"}),"truth/causality upgrade")
    def test_review_to_e_rejected(self): self.check_bad(lambda d:d["relationships"][0].update({"allowed_inference":"review implies external evidence"}),"truth/causality upgrade")
    def test_owner_to_e_rejected(self): self.check_bad(lambda d:d["relationships"][0].update({"allowed_inference":"owner acceptance implies external evidence"}),"truth/causality upgrade")
    def test_repo_dependency_to_causality_rejected(self): self.check_bad(lambda d:d["relationships"][2].update({"allowed_inference":"repository dependency implies causality"}),"truth/causality upgrade")
    def test_copied_local_claim_rows_rejected(self): self.check_bad(lambda d:d.update({"claim_rows":[]}),"copied local state")
    def test_public_surface_requires_routes(self): self.check_bad(lambda d:d["relationships"][0].update({"ceiling_route":"NOT_APPLICABLE"}),"lacks ceiling/provenance")
    def test_language_cannot_be_l7(self): self.check_bad(lambda d:d["relationships"][1]["prohibited_inferences"].remove("language_creates_L7"),"prohibit L7")
    def test_historical_mapping_required(self): self.check_bad(lambda d:d.update({"relationships":[r for r in d["relationships"] if r["type"]!="publication.historical_mapping"]}),"historical mapping")
    def test_reciprocal_link_required(self): self.check_bad(lambda d:d["relationships"][4].update({"reciprocal_id":"missing"}),"broken reciprocal")

if __name__=="__main__": unittest.main()
