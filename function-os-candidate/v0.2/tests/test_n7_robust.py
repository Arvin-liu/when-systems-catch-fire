"""121Q6 Step 013: N7 Validator robust tests."""
import unittest, copy

from function_os.n1_functionspec_parser import N1FunctionSpecParser
from function_os.n2_representation import N2RepresentationEncoder
from function_os.n3_compiler import N3SymbolicCompiler
from function_os.n4_artifact_packager import N4ArtifactPackager
from function_os.n5_interpreter import N5Interpreter
from function_os.n6_execution_trace import N6TraceCapture
from function_os.n7_validator import N7Validator

SPEC = '{"function_id":"FN-20260715-0001","spec_version":"1.0.0","name":"add","domain":"symbolic","inputs":{"x":"integer","y":"integer"},"outputs":{"result":"integer"},"preconditions":[{"expression":"x >= 0","message":"x"}],"postconditions":[{"expression":"result == x + y","message":"r"}],"effects_declared":["pure"],"created_at":"2026-07-15T12:00:00Z"}'


class Fixture(unittest.TestCase):
    def setUp(self):
        self.parser = N1FunctionSpecParser()
        self.enc = N2RepresentationEncoder()
        self.comp = N3SymbolicCompiler()
        self.pack = N4ArtifactPackager()
        self.interp = N5Interpreter()
        self.cap = N6TraceCapture()
        self.val = N7Validator()
        spec = self.parser.parse(SPEC)
        rep = self.enc.encode(spec)
        compiled = self.comp.compile(spec, rep)
        self.spec, self.rep, self.artifact = spec, rep, self.pack.package(compiled, spec, rep)
        r = self.interp.execute(self.artifact, {'x': 3, 'y': 7})
        self.trace = self.cap.capture(r, spec)

    def _validate(self, **overrides):
        spec = overrides.get('spec', self.spec)
        rep = overrides.get('rep', self.rep)
        art = overrides.get('artifact', self.artifact)
        trace = overrides.get('trace', self.trace)
        return self.val.validate(spec, rep, art, trace)


class TestN7Positive(Fixture):
    def test_full_chain_pass(self):
        res = self._validate()
        self.assertEqual(res['status'], 'PASS')
        self.assertTrue(all(c['passed'] for c in res['checks']))
        self.assertEqual(res['validation_id'], 'VAL-FN-20260715-0001-1')


class TestN7Negative(Fixture):
    def test_spec_hash_tamper_fails(self):
        bad = dict(self.spec)
        bad['spec_hash'] = 'deadbeef' * 8
        res = self._validate(spec=bad)
        self.assertEqual(res['status'], 'FAIL')
        self.assertTrue(any(not c['passed'] and c['check'] == 'spec_to_artifact_hash' for c in res['checks']))

    def test_representation_hash_mismatch_fails(self):
        bad = copy.deepcopy(self.artifact)
        bad['representation_hash'] = 'deadbeef' * 8
        res = self._validate(artifact=bad)
        self.assertEqual(res['status'], 'FAIL')
        self.assertTrue(any(not c['passed'] and c['check'] == 'rep_to_artifact_hash' for c in res['checks']))

    def test_content_hash_tamper_fails(self):
        bad = copy.deepcopy(self.artifact)
        bad['content_hash'] = 'deadbeef' * 8
        res = self._validate(artifact=bad)
        self.assertEqual(res['status'], 'FAIL')
        self.assertTrue(any(not c['passed'] and c['check'] == 'artifact_content_integrity' for c in res['checks']))

    def test_input_mismatch_warning(self):
        bad = copy.deepcopy(self.artifact)
        bad['payload'] = dict(bad['payload'])
        bad['payload']['input_map'] = dict(bad['payload']['input_map'])
        bad['payload']['input_map']['z'] = 'integer'
        res = self._validate(artifact=bad)
        self.assertTrue(any(not c['passed'] and c['check'] == 'input_completeness' for c in res['checks']))

    def test_trace_artifact_inconsistency_warning(self):
        bad = copy.deepcopy(self.trace)
        bad['artifact_id'] = 'ART-FN-20990101-9999-1'
        res = self._validate(trace=bad)
        self.assertTrue(any(not c['passed'] and c['check'] == 'trace_artifact_consistency' for c in res['checks']))

    def test_trace_spec_inconsistency_warning(self):
        bad = copy.deepcopy(self.trace)
        bad['spec_id'] = 'FN-20990101-9999'
        res = self._validate(trace=bad)
        self.assertTrue(any(not c['passed'] and c['check'] == 'trace_spec_consistency' for c in res['checks']))

    def test_evidence_self_reference_warning(self):
        res = self._validate()
        res_with_ev = self.val.validate(self.spec, self.rep, self.artifact, self.trace,
                                        evidence=[{'source_id': 'FN-20260715-0001'}])
        self.assertTrue(any(not c['passed'] and 'evidence' in c['check'] for c in res_with_ev['checks']))


if __name__ == '__main__':
    unittest.main()
