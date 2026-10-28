"""121Q6 Step 012: N6 ExecutionTrace robust tests."""
import unittest

from function_os.n1_functionspec_parser import N1FunctionSpecParser
from function_os.n2_representation import N2RepresentationEncoder
from function_os.n3_compiler import N3SymbolicCompiler
from function_os.n4_artifact_packager import N4ArtifactPackager
from function_os.n5_interpreter import N5Interpreter
from function_os.n6_execution_trace import N6TraceCapture, N6TraceArchiver, N6TraceQuerier

SPEC = '{"function_id":"FN-20260715-0001","spec_version":"1.0.0","name":"add","domain":"symbolic","inputs":{"x":"integer","y":"integer"},"outputs":{"result":"integer"},"preconditions":[{"expression":"x >= 0","message":"x"}],"postconditions":[{"expression":"result == x + y","message":"r"}],"effects_declared":["pure"],"created_at":"2026-07-15T12:00:00Z"}'


class Fixture(unittest.TestCase):
    def setUp(self):
        self.parser = N1FunctionSpecParser()
        self.enc = N2RepresentationEncoder()
        self.comp = N3SymbolicCompiler()
        self.pack = N4ArtifactPackager()
        self.interp = N5Interpreter()
        self.cap = N6TraceCapture()
        self.arch = N6TraceArchiver()
        self.q = N6TraceQuerier(self.arch)
        spec = self.parser.parse(SPEC)
        rep = self.enc.encode(spec)
        self.spec = spec
        self.artifact = self.pack.package(self.comp.compile(spec, rep), spec, rep)

    def _trace(self, inputs):
        r = self.interp.execute(self.artifact, inputs)
        return self.cap.capture(r, self.spec)


class TestN6Capture(Fixture):
    def test_capture_binds_spec(self):
        t = self._trace({'x': 3, 'y': 7})
        self.assertEqual(t['spec_id'], 'FN-20260715-0001')
        self.assertEqual(t['spec_id'], self.spec['function_id'])

    def test_trace_hash_deterministic(self):
        t1 = self._trace({'x': 3, 'y': 7})
        t2 = self._trace({'x': 3, 'y': 7})
        self.assertEqual(t1['trace_hash'], t2['trace_hash'])

    def test_status_mapping_ok(self):
        t = self._trace({'x': 3, 'y': 7})
        self.assertEqual(t['status'], 'OK')

    def test_status_mapping_failed(self):
        t = self._trace({'x': -1, 'y': 7})
        self.assertEqual(t['status'], 'FAILED')


class TestN6ArchiveQuery(Fixture):
    def test_archive_and_get(self):
        t = self._trace({'x': 3, 'y': 7})
        self.arch.archive(t)
        self.assertEqual(self.arch.get(t['trace_id'])['trace_hash'], t['trace_hash'])

    def test_list_by_artifact(self):
        t = self._trace({'x': 3, 'y': 7})
        self.arch.archive(t)
        self.assertEqual(len(self.arch.list_by_artifact(self.artifact['artifact_id'])), 1)

    def test_list_by_spec(self):
        t = self._trace({'x': 3, 'y': 7})
        self.arch.archive(t)
        self.assertEqual(len(self.arch.list_by_spec('FN-20260715-0001')), 1)

    def test_duplicate_archive_overwrites(self):
        t1 = self._trace({'x': 3, 'y': 7})
        t2 = self._trace({'x': 3, 'y': 7})
        # Simulate re-archiving same trace_id (overwrite keyed by trace_id)
        t2 = dict(t2)
        t2['trace_id'] = t1['trace_id']
        t2['captured_at'] = '2099-01-01T00:00:00Z'
        self.arch.archive(t1)
        self.arch.archive(t2)
        self.assertEqual(len(self.arch.list_by_spec('FN-20260715-0001')), 1)
        self.assertEqual(self.arch.get(t1['trace_id'])['captured_at'], '2099-01-01T00:00:00Z')

    def test_query_successes_failures(self):
        self.arch.archive(self._trace({'x': 3, 'y': 7}))    # OK
        self.arch.archive(self._trace({'x': -1, 'y': 7}))   # FAILED
        self.assertEqual(len(self.q.successes()), 1)
        self.assertEqual(len(self.q.failures()), 1)

    def test_query_summary(self):
        self.arch.archive(self._trace({'x': 3, 'y': 7}))
        s = self.q.summary()
        self.assertEqual(s['total'], 1)
        self.assertEqual(s['ok'], 1)

    def test_query_empty(self):
        s = self.q.summary()
        self.assertEqual(s['total'], 0)
        self.assertEqual(s['ok'], 0)


if __name__ == '__main__':
    unittest.main()
