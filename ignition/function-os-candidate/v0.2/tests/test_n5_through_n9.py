"""Tests: N5 Interpreter → N6 Trace → N7 Validator → N8 Router → N9 Registry."""
import unittest

from function_os.n1_functionspec_parser import N1FunctionSpecParser
from function_os.n2_representation import N2RepresentationEncoder
from function_os.n3_compiler import N3SymbolicCompiler
from function_os.n4_artifact_packager import N4ArtifactPackager
from function_os.n5_interpreter import N5Interpreter
from function_os.n6_execution_trace import N6TraceCapture, N6TraceArchiver, N6TraceQuerier
from function_os.n7_validator import N7Validator, N7Feedback
from function_os.n8_composer_router import N8ComposerRouter
from function_os.n9_registry import N9RegistryStore, N9RegistryUpdater, N9RegistryValidator

SPEC = """{"function_id":"FN-20260715-0001","spec_version":"1.0.0","name":"add","domain":"symbolic","inputs":{"x":"integer","y":"integer"},"outputs":{"result":"integer"},"preconditions":[{"expression":"x >= 0","message":"x"}],"postconditions":[{"expression":"result == x + y","message":"r"}],"effects_declared":["pure"],"created_at":"2026-07-15T00:00:00Z"}"""

def build_pipeline():
    parser = N1FunctionSpecParser()
    encoder = N2RepresentationEncoder()
    compiler = N3SymbolicCompiler()
    packager = N4ArtifactPackager()
    spec = parser.parse(SPEC)
    rep = encoder.encode(spec)
    compiled = compiler.compile(spec, rep)
    artifact = packager.package(compiled, spec, rep)
    return parser, spec, encoder, rep, compiler, compiled, packager, artifact

class TestN5Interpreter(unittest.TestCase):
    def setUp(self):
        _, self.spec, _, self.rep, _, self.compiled, _, self.artifact = build_pipeline()
        self.interpreter = N5Interpreter()

    def test_ok(self):
        r = self.interpreter.execute(self.artifact, {'x': 3, 'y': 7})
        self.assertEqual(r['status'], 'OK')
        self.assertEqual(r['outputs'], {'result': 10})

    def test_precondition_fail(self):
        r = self.interpreter.execute(self.artifact, {'x': -1, 'y': 2})
        self.assertEqual(r['status'], 'PRECONDITION_FAILED')

    def test_missing_input(self):
        r = self.interpreter.execute(self.artifact, {'x': 3})
        self.assertEqual(r['status'], 'TYPE_ERROR')

    def test_type_mismatch(self):
        r = self.interpreter.execute(self.artifact, {'x': 'abc', 'y': 2})
        self.assertEqual(r['status'], 'TYPE_ERROR')


class TestN6Trace(unittest.TestCase):
    def setUp(self):
        _, self.spec, _, _, _, _, _, self.artifact = build_pipeline()
        self.interpreter = N5Interpreter()
        self.capture = N6TraceCapture()
        self.archiver = N6TraceArchiver()
        self.querier = N6TraceQuerier(self.archiver)

    def test_capture_ok(self):
        r = self.interpreter.execute(self.artifact, {'x': 3, 'y': 7})
        trace = self.capture.capture(r, self.spec)
        self.assertEqual(trace['status'], 'OK')
        self.assertIn('trace_hash', trace)

    def test_capture_failed(self):
        r = self.interpreter.execute(self.artifact, {'x': -1, 'y': 2})
        trace = self.capture.capture(r, self.spec)
        self.assertEqual(trace['status'], 'FAILED')

    def test_archive_querier(self):
        r1 = self.interpreter.execute(self.artifact, {'x': 3, 'y': 7})
        r2 = self.interpreter.execute(self.artifact, {'x': -1, 'y': 2})
        self.archiver.archive(self.capture.capture(r1, self.spec))
        self.archiver.archive(self.capture.capture(r2, self.spec))
        s = self.querier.summary()
        self.assertEqual(s['total'], 2)
        self.assertEqual(s['ok'], 1)
        self.assertEqual(s['failed'], 1)


class TestN7Validator(unittest.TestCase):
    def setUp(self):
        _, self.spec, _, self.rep, _, _, _, self.artifact = build_pipeline()
        self.validator = N7Validator()
        self.interpreter = N5Interpreter()
        self.capture = N6TraceCapture()

    def test_validate_pass(self):
        r = self.interpreter.execute(self.artifact, {'x': 3, 'y': 7})
        trace = self.capture.capture(r, self.spec)
        v = self.validator.validate(self.spec, self.rep, self.artifact, trace)
        self.assertEqual(v['status'], 'PASS')

    def test_validate_fail_tampered(self):
        bad = dict(self.artifact)
        bad['content_hash'] = 'deadbeef'
        v = self.validator.validate(self.spec, self.rep, bad)
        self.assertIn('FAIL', v['status'])

    def test_feedback_suggests(self):
        r = self.interpreter.execute(self.artifact, {'x': 3, 'y': 7})
        trace = self.capture.capture(r, self.spec)
        v = self.validator.validate(self.spec, self.rep, self.artifact, trace)
        fb = N7Feedback()
        suggestions = fb.suggest(v, self.spec)
        self.assertEqual(len(suggestions), 0)


class TestN8Router(unittest.TestCase):
    def setUp(self):
        _, _, _, _, _, _, _, self.artifact = build_pipeline()
        self.router = N8ComposerRouter()

    def test_plan_found(self):
        task = {"task_id":"T-1","required_functions":[
            {"function_id":"FN-20260715-0001","inputs_from":"task","on_failure":"ABORT"}]}
        plan = self.router.plan(task, [self.artifact])
        self.assertEqual(plan['steps'][0]['status'], 'PLANNED')

    def test_plan_not_found(self):
        task = {"task_id":"T-2","required_functions":[
            {"function_id":"FN-NONEXIST","inputs_from":"task","on_failure":"ABORT"}]}
        plan = self.router.plan(task, [self.artifact])
        self.assertEqual(plan['steps'][0]['status'], 'SKIPPED')


class TestN9Registry(unittest.TestCase):
    def setUp(self):
        self.store = N9RegistryStore()
        self.updater = N9RegistryUpdater(self.store)
        self.validator = N9RegistryValidator()

    def _make_record(self):
        return {"function_id":"FN-20260715-0001","spec_hash":"abc","artifact_hash":"def",
                "representation_hash":"ghi","trace_hash":"jkl","compiler_version":"0.2.0",
                "content_hash":"abc"}

    def test_create_read(self):
        self.store.create(self._make_record())
        r = self.store.read('FN-20260715-0001')
        self.assertEqual(r['revision'], 1)

    def test_update_increment(self):
        self.store.create(self._make_record())
        self.updater.update('FN-20260715-0001', {"spec_hash":"new"})
        r = self.store.read('FN-20260715-0001')
        self.assertEqual(r['revision'], 2)

    def test_history(self):
        self.store.create(self._make_record())
        self.updater.update('FN-20260715-0001', {"spec_hash":"v2"})
        self.updater.update('FN-20260715-0001', {"spec_hash":"v3"})
        h = self.store.history('FN-20260715-0001')
        self.assertEqual(len(h), 3)

    def test_rollback(self):
        self.store.create(self._make_record())
        self.updater.update('FN-20260715-0001', {"spec_hash":"changed"})
        self.updater.rollback('FN-20260715-0001', 1)
        r = self.store.read('FN-20260715-0001')
        self.assertEqual(r['revision'], 3)
        self.assertEqual(r['spec_hash'], 'abc')

    def test_validate(self):
        self.store.create(self._make_record())
        result = self.validator.validate(self.store)
        self.assertTrue(result['valid'])

    def test_validate_duplicate_fails(self):
        self.store.create(self._make_record())

    def test_update_nonexistent(self):
        with self.assertRaises(ValueError):
            self.updater.update('NO-SUCH', {})

    def test_create_duplicate(self):
        self.store.create(self._make_record())
        with self.assertRaises(ValueError):
            self.store.create(self._make_record())


if __name__ == '__main__':
    unittest.main()
