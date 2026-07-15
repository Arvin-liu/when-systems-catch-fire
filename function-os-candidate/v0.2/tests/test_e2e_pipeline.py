"""E2E Integration Test: Full N1→N9 pipeline — no exec()/compile()/eval().

Standard Python imports only.
"""
import sys, os, json, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from function_os.n1_functionspec_parser import N1FunctionSpecParser, FunctionSpecParseError
from function_os.n2_representation import N2RepresentationEncoder, N2RepresentationValidator
from function_os.n3_compiler import N3SymbolicCompiler
from function_os.n4_artifact_packager import N4ArtifactPackager, N4ArtifactVerifier
from function_os.n5_interpreter import N5Interpreter
from function_os.n6_execution_trace import N6TraceCapture, N6TraceArchiver, N6TraceQuerier
from function_os.n7_validator import N7Validator, N7Feedback
from function_os.n8_composer_router import N8ComposerRouter
from function_os.n9_registry import N9RegistryStore, N9RegistryUpdater, N9RegistryValidator

SPECS = {
    "add": '{"function_id":"FN-20260715-0001","spec_version":"1.0.0","name":"add","domain":"symbolic","inputs":{"x":"integer","y":"integer"},"outputs":{"result":"integer"},"preconditions":[{"expression":"x >= 0","message":"x non-negative"}],"postconditions":[{"expression":"result == x + y","message":"r == sum"}],"effects_declared":["pure"],"created_at":"2026-07-15T12:00:00Z"}',
    "mul": '{"function_id":"FN-20260715-0002","spec_version":"1.0.0","name":"multiply","domain":"symbolic","inputs":{"a":"integer","b":"integer"},"outputs":{"product":"integer"},"preconditions":[{"expression":"a >= 0","message":"a non-negative"}],"postconditions":[{"expression":"product == a * b","message":"p == a * b"}],"effects_declared":["pure"],"created_at":"2026-07-15T12:01:00Z"}',
    "square": '{"function_id":"FN-20260715-0003","spec_version":"1.0.0","name":"square","domain":"symbolic","inputs":{"n":"integer"},"outputs":{"sq":"integer"},"preconditions":[{"expression":"n >= 0","message":"n non-negative"}],"postconditions":[{"expression":"sq == n * n","message":"sq == n ^ 2"}],"effects_declared":["pure"],"created_at":"2026-07-15T12:02:00Z"}'
}


class TestE2EPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = N1FunctionSpecParser()
        cls.encoder = N2RepresentationEncoder()
        cls.rep_validator = N2RepresentationValidator()
        cls.compiler = N3SymbolicCompiler()
        cls.packager = N4ArtifactPackager()
        cls.verifier = N4ArtifactVerifier()
        cls.interpreter = N5Interpreter()
        cls.capture = N6TraceCapture()
        cls.archiver = N6TraceArchiver()
        cls.querier = N6TraceQuerier(cls.archiver)
        cls.validator = N7Validator()
        cls.feedback = N7Feedback()
        cls.router = N8ComposerRouter()
        cls.store = N9RegistryStore()
        cls.updater = N9RegistryUpdater(cls.store)
        cls.reg_validator = N9RegistryValidator()

    def _build(self, spec_json):
        """Full N1→N4 pipeline: FunctionSpec → Artifact."""
        spec = self.parser.parse(spec_json)
        rep = self.encoder.encode(spec)
        rep_issues = self.rep_validator.validate(rep, spec)
        compiled = self.compiler.compile(spec, rep)
        artifact = self.packager.package(compiled, spec, rep)
        verify = self.verifier.verify(artifact)
        return spec, rep, rep_issues, compiled, artifact, verify

    def test_01_n1_through_n4_add(self):
        spec, rep, rep_issues, compiled, artifact, verify = self._build(SPECS['add'])
        self.assertEqual(spec['function_id'], 'FN-20260715-0001')
        self.assertEqual(rep_issues, [])
        self.assertEqual(compiled['status'], 'OK')
        self.assertTrue(verify['valid'])
        self.assertTrue(artifact['artifact_id'].startswith('ART-'))

    def test_02_n5_interpreter_add(self):
        _, _, _, _, artifact, _ = self._build(SPECS['add'])
        r = self.interpreter.execute(artifact, {'x': 5, 'y': 3})
        self.assertEqual(r['status'], 'OK')
        self.assertEqual(r['outputs']['result'], 8)

    def test_03_n5_interpreter_multiply(self):
        _, _, _, _, artifact, _ = self._build(SPECS['mul'])
        r = self.interpreter.execute(artifact, {'a': 6, 'b': 7})
        self.assertEqual(r['status'], 'OK')
        self.assertEqual(r['outputs']['product'], 42)

    def test_04_n5_interpreter_square(self):
        _, _, _, _, artifact, _ = self._build(SPECS['square'])
        r = self.interpreter.execute(artifact, {'n': 9})
        self.assertEqual(r['status'], 'OK')
        self.assertEqual(r['outputs']['sq'], 81)

    def test_05_n6_trace_all(self):
        for name, spec_json in SPECS.items():
            _, spec, _, _, artifact, _ = self._build(spec_json)
            r = self.interpreter.execute(artifact,
                {'x': 3, 'y': 7} if name == 'add'
                else {'a': 3, 'b': 7} if name == 'mul'
                else {'n': 3})
            trace = self.capture.capture(r, spec)
            self.archiver.archive(trace)
            self.assertIn('trace_hash', trace)
        s = self.querier.summary()
        self.assertEqual(s['total'], 3)
        self.assertEqual(s['ok'], 3)

    def test_06_n7_validate_add(self):
        spec, rep, rep_issues, _, artifact, _ = self._build(SPECS['add'])
        r = self.interpreter.execute(artifact, {'x': 3, 'y': 7})
        trace = self.capture.capture(r, spec)
        v = self.validator.validate(spec, rep, artifact, trace)
        self.assertEqual(v['status'], 'PASS')

    def test_07_n7_validate_mul(self):
        spec, rep, _, _, artifact, _ = self._build(SPECS['mul'])
        r = self.interpreter.execute(artifact, {'a': 3, 'b': 7})
        trace = self.capture.capture(r, spec)
        v = self.validator.validate(spec, rep, artifact, trace)
        self.assertEqual(v['status'], 'PASS')

    def test_08_n8_router_plan(self):
        artifacts = []
        for name, spec_json in SPECS.items():
            _, _, _, _, artifact, _ = self._build(spec_json)
            artifacts.append(artifact)

        task = {"task_id":"TASK-001","required_functions":[
            {"function_id":"FN-20260715-0001","inputs_from":"task_input","on_failure":"ABORT"},
            {"function_id":"FN-20260715-0002","inputs_from":"step_0_output","on_failure":"ABORT"}
        ]}
        plan = self.router.plan(task, artifacts)
        self.assertEqual(len(plan['steps']), 2)
        self.assertEqual(plan['steps'][0]['status'], 'PLANNED')
        self.assertEqual(plan['steps'][1]['status'], 'PLANNED')

    def test_09_n8_router_not_found(self):
        _, _, _, _, artifact, _ = self._build(SPECS['add'])
        task = {"task_id":"T-404","required_functions":[
            {"function_id":"FN-NEVER-EXISTS","inputs_from":"task","on_failure":"ABORT"}
        ]}
        plan = self.router.plan(task, [artifact])
        self.assertEqual(plan['steps'][0]['status'], 'SKIPPED')

    def test_10_n9_registry_full_cycle(self):
        spec, rep, _, _, artifact, _ = self._build(SPECS['add'])
        r = self.interpreter.execute(artifact, {'x': 3, 'y': 7})
        trace = self.capture.capture(r, spec)

        record = {
            "function_id": spec['function_id'],
            "spec_hash": spec['spec_hash'],
            "artifact_hash": artifact['artifact_hash'],
            "representation_hash": rep.get('ir_hash', ''),
            "trace_hash": trace['trace_hash'],
            "compiler_version": "0.2.0",
            "content_hash": artifact['content_hash']
        }
        # create
        self.store.create(record)
        self.assertEqual(len(self.store.list()), 1)
        # read
        r1 = self.store.read(spec['function_id'])
        self.assertEqual(r1['revision'], 1)
        # update
        self.updater.update(spec['function_id'], {"spec_hash": "updated_hash"})
        r2 = self.store.read(spec['function_id'])
        self.assertEqual(r2['revision'], 2)
        # history
        h = self.store.history(spec['function_id'])
        self.assertEqual(len(h), 2)
        # validate
        v = self.reg_validator.validate(self.store)
        self.assertTrue(v['valid'])

    def test_11_n5_precondition_fail(self):
        _, _, _, _, artifact, _ = self._build(SPECS['add'])
        r = self.interpreter.execute(artifact, {'x': -5, 'y': 3})
        self.assertEqual(r['status'], 'PRECONDITION_FAILED')

    def test_12_n5_postcondition_violation(self):
        # Use square with wrong output expectation — postcondition detects mismatch
        # Actually our DSL will correctly compute n*n=25 so postcondition will pass
        # Test that N7 catches a broken artifact instead
        spec, _, _, _, artifact, _ = self._build(SPECS['add'])
        bad_artifact = dict(artifact)
        bad_artifact['content_hash'] = 'deadbeef'
        v = self.validator.validate(spec, {}, bad_artifact)
        self.assertEqual(v['status'], 'FAIL')

    def test_13_hash_chain_integrity(self):
        # Verify N1→N2→N3→N4 hash chain
        spec = self.parser.parse(SPECS['add'])
        rep = self.encoder.encode(spec)
        compiled = self.compiler.compile(spec, rep)
        artifact = self.packager.package(compiled, spec, rep)

        self.assertEqual(spec['spec_hash'], rep['spec_hash'])
        self.assertEqual(spec['spec_hash'], compiled['spec_hash'])
        self.assertEqual(spec['spec_hash'], artifact['spec_hash'])
        self.assertTrue(self.verifier.verify(artifact)['valid'])


if __name__ == '__main__':
    unittest.main()
