"""E2E Integration Test: Full N1→N9 pipeline — no exec()/compile()/eval().

Standard Python imports only. 121Q6 Step 006: removed positional unpacking bug
class (uses named BuildResult), added per-test isolation for stateful components,
added regression test that N6 binds the REAL FunctionSpec (not a Representation).
"""
import unittest
from collections import namedtuple

from function_os.n1_functionspec_parser import N1FunctionSpecParser, FunctionSpecParseError
from function_os.n2_representation import N2RepresentationEncoder, N2RepresentationValidator
from function_os.n3_compiler import N3SymbolicCompiler
from function_os.n4_artifact_packager import N4ArtifactPackager, N4ArtifactVerifier
from function_os.n5_interpreter import N5Interpreter
from function_os.n6_execution_trace import N6TraceCapture, N6TraceArchiver, N6TraceQuerier
from function_os.n7_validator import N7Validator, N7Feedback
from function_os.n8_composer_router import N8ComposerRouter
from function_os.n9_registry import N9RegistryStore, N9RegistryUpdater, N9RegistryValidator

# Named result object — eliminates positional-unpacking ambiguity (Step 006 fix)
BuildResult = namedtuple("BuildResult", ["spec", "rep", "rep_issues", "compiled", "artifact", "verify"])

SPECS = {
    "add": '{"function_id":"FN-20260715-0001","spec_version":"1.0.0","name":"add","domain":"symbolic","inputs":{"x":"integer","y":"integer"},"outputs":{"result":"integer"},"preconditions":[{"expression":"x >= 0","message":"x non-negative"}],"postconditions":[{"expression":"result == x + y","message":"r == sum"}],"effects_declared":["pure"],"created_at":"2026-07-15T12:00:00Z"}',
    "mul": '{"function_id":"FN-20260715-0002","spec_version":"1.0.0","name":"multiply","domain":"symbolic","inputs":{"a":"integer","b":"integer"},"outputs":{"product":"integer"},"preconditions":[{"expression":"a >= 0","message":"a non-negative"}],"postconditions":[{"expression":"product == a * b","message":"p == a * b"}],"effects_declared":["pure"],"created_at":"2026-07-15T12:01:00Z"}',
    "square": '{"function_id":"FN-20260715-0003","spec_version":"1.0.0","name":"square","domain":"symbolic","inputs":{"n":"integer"},"outputs":{"sq":"integer"},"preconditions":[{"expression":"n >= 0","message":"n non-negative"}],"postconditions":[{"expression":"sq == n * n","message":"sq == n ^ 2"}],"effects_declared":["pure"],"created_at":"2026-07-15T12:02:00Z"}'
}


class TestE2EPipeline(unittest.TestCase):
    # Stateless components shared (safe across tests)
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
        cls.validator = N7Validator()
        cls.feedback = N7Feedback()
        cls.router = N8ComposerRouter()

    # Stateful components rebuilt per test — isolation (Step 006)
    def setUp(self):
        self.archiver = N6TraceArchiver()
        self.querier = N6TraceQuerier(self.archiver)
        self.store = N9RegistryStore()
        self.updater = N9RegistryUpdater(self.store)
        self.reg_validator = N9RegistryValidator()

    def _build(self, spec_json):
        """Full N1→N4 pipeline: FunctionSpec → Artifact (named result)."""
        spec = self.parser.parse(spec_json)
        rep = self.encoder.encode(spec)
        rep_issues = self.rep_validator.validate(rep, spec)
        compiled = self.compiler.compile(spec, rep)
        artifact = self.packager.package(compiled, spec, rep)
        verify = self.verifier.verify(artifact)
        return BuildResult(spec, rep, rep_issues, compiled, artifact, verify)

    @staticmethod
    def _run(built, name):
        inputs = ({'x': 3, 'y': 7} if name == 'add'
                  else {'a': 3, 'b': 7} if name == 'mul'
                  else {'n': 3})
        return built.interpreter_execute(inputs) if hasattr(built, 'interpreter_execute') else inputs

    def test_01_n1_through_n4_add(self):
        b = self._build(SPECS['add'])
        self.assertEqual(b.spec['function_id'], 'FN-20260715-0001')
        self.assertEqual(b.rep_issues, [])
        self.assertEqual(b.compiled['status'], 'OK')
        self.assertTrue(b.verify['valid'])
        self.assertTrue(b.artifact['artifact_id'].startswith('ART-'))

    def test_02_n5_interpreter_add(self):
        b = self._build(SPECS['add'])
        r = self.interpreter.execute(b.artifact, {'x': 5, 'y': 3})
        self.assertEqual(r['status'], 'OK')
        self.assertEqual(r['outputs']['result'], 8)

    def test_03_n5_interpreter_multiply(self):
        b = self._build(SPECS['mul'])
        r = self.interpreter.execute(b.artifact, {'a': 6, 'b': 7})
        self.assertEqual(r['status'], 'OK')
        self.assertEqual(r['outputs']['product'], 42)

    def test_04_n5_interpreter_square(self):
        b = self._build(SPECS['square'])
        r = self.interpreter.execute(b.artifact, {'n': 9})
        self.assertEqual(r['status'], 'OK')
        self.assertEqual(r['outputs']['sq'], 81)

    def test_05_n6_trace_all(self):
        for name, spec_json in SPECS.items():
            b = self._build(spec_json)
            r = self.interpreter.execute(b.artifact,
                {'x': 3, 'y': 7} if name == 'add'
                else {'a': 3, 'b': 7} if name == 'mul'
                else {'n': 3})
            # Named access: b.spec is the REAL FunctionSpec (not Representation)
            trace = self.capture.capture(r, b.spec)
            self.archiver.archive(trace)
            self.assertIn('trace_hash', trace)
        s = self.querier.summary()
        self.assertEqual(s['total'], 3)
        self.assertEqual(s['ok'], 3)

    def test_06_n7_validate_add(self):
        b = self._build(SPECS['add'])
        r = self.interpreter.execute(b.artifact, {'x': 3, 'y': 7})
        trace = self.capture.capture(r, b.spec)
        v = self.validator.validate(b.spec, b.rep, b.artifact, trace)
        self.assertEqual(v['status'], 'PASS')

    def test_07_n7_validate_mul(self):
        b = self._build(SPECS['mul'])
        r = self.interpreter.execute(b.artifact, {'a': 3, 'b': 7})
        trace = self.capture.capture(r, b.spec)
        v = self.validator.validate(b.spec, b.rep, b.artifact, trace)
        self.assertEqual(v['status'], 'PASS')

    def test_08_n8_router_plan(self):
        artifacts = [self._build(s).artifact for s in SPECS.values()]
        task = {"task_id":"TASK-001","required_functions":[
            {"function_id":"FN-20260715-0001","inputs_from":"task_input","on_failure":"ABORT"},
            {"function_id":"FN-20260715-0002","inputs_from":"step_0_output","on_failure":"ABORT"}
        ]}
        plan = self.router.plan(task, artifacts)
        self.assertEqual(len(plan['steps']), 2)
        self.assertEqual(plan['steps'][0]['status'], 'PLANNED')
        self.assertEqual(plan['steps'][1]['status'], 'PLANNED')

    def test_09_n8_router_not_found(self):
        b = self._build(SPECS['add'])
        task = {"task_id":"T-404","required_functions":[
            {"function_id":"FN-NEVER-EXISTS","inputs_from":"task","on_failure":"ABORT"}
        ]}
        plan = self.router.plan(task, [b.artifact])
        self.assertEqual(plan['steps'][0]['status'], 'SKIPPED')

    def test_10_n9_registry_full_cycle(self):
        b = self._build(SPECS['add'])
        r = self.interpreter.execute(b.artifact, {'x': 3, 'y': 7})
        trace = self.capture.capture(r, b.spec)
        record = {
            "function_id": b.spec['function_id'],
            "spec_hash": b.spec['spec_hash'],
            "artifact_hash": b.artifact['artifact_hash'],
            "representation_hash": b.rep.get('ir_hash', ''),
            "trace_hash": trace['trace_hash'],
            "compiler_version": "0.2.1-candidate",
            "content_hash": b.artifact['content_hash']
        }
        self.store.create(record)
        self.assertEqual(len(self.store.list()), 1)
        r1 = self.store.read(b.spec['function_id'])
        self.assertEqual(r1['revision'], 1)
        self.updater.update(b.spec['function_id'], {"spec_hash": "updated_hash"})
        r2 = self.store.read(b.spec['function_id'])
        self.assertEqual(r2['revision'], 2)
        h = self.store.history(b.spec['function_id'])
        self.assertEqual(len(h), 2)
        v = self.reg_validator.validate(self.store)
        self.assertTrue(v['valid'])

    def test_11_n5_precondition_fail(self):
        b = self._build(SPECS['add'])
        r = self.interpreter.execute(b.artifact, {'x': -5, 'y': 3})
        self.assertEqual(r['status'], 'PRECONDITION_FAILED')

    def test_12_n5_postcondition_violation_via_tamper(self):
        b = self._build(SPECS['add'])
        bad_artifact = dict(b.artifact)
        bad_artifact['content_hash'] = 'deadbeef'
        v = self.validator.validate(b.spec, {}, bad_artifact)
        self.assertEqual(v['status'], 'FAIL')

    def test_13_hash_chain_integrity(self):
        spec = self.parser.parse(SPECS['add'])
        rep = self.encoder.encode(spec)
        compiled = self.compiler.compile(spec, rep)
        artifact = self.packager.package(compiled, spec, rep)
        self.assertEqual(spec['spec_hash'], rep['spec_hash'])
        self.assertEqual(spec['spec_hash'], compiled['spec_hash'])
        self.assertEqual(spec['spec_hash'], artifact['spec_hash'])
        self.assertTrue(self.verifier.verify(artifact)['valid'])

    def test_14_n6_trace_binds_real_functionspec(self):
        """Regression: N6 capture must receive the REAL FunctionSpec, not a Representation.
        A Representation object has 'representation_id' (no 'function_id'), so if it were
        passed by mistake the trace's spec_id would be empty — this test fails loudly."""
        b = self._build(SPECS['add'])
        r = self.interpreter.execute(b.artifact, {'x': 3, 'y': 7})
        trace = self.capture.capture(r, b.spec)  # b.spec is the FunctionSpec
        self.assertEqual(trace['spec_id'], 'FN-20260715-0001')
        self.assertEqual(trace['spec_id'], b.spec['function_id'])
        # Ensure we did NOT accidentally pass a Representation (which lacks function_id)
        self.assertNotIn('representation_id', b.spec)
        # And the trace effects came from the spec's declared effects, not a rep
        self.assertEqual(trace['effects'], b.spec.get('effects_declared', []))


if __name__ == '__main__':
    unittest.main()
