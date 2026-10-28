"""121Q6 Step 011: N5 Interpreter robust tests."""
import unittest, copy

from function_os.n1_functionspec_parser import N1FunctionSpecParser
from function_os.n2_representation import N2RepresentationEncoder
from function_os.n3_compiler import N3SymbolicCompiler
from function_os.n4_artifact_packager import N4ArtifactPackager
from function_os.n5_interpreter import N5Interpreter

SPEC_ADD = '{"function_id":"FN-20260715-0001","spec_version":"1.0.0","name":"add","domain":"symbolic","inputs":{"x":"integer","y":"integer"},"outputs":{"result":"integer"},"preconditions":[{"expression":"x >= 0","message":"x non-negative"}],"postconditions":[{"expression":"result == x + y","message":"r == sum"}],"effects_declared":["pure"],"created_at":"2026-07-15T12:00:00Z"}'

# postcondition #1 (used for expression extraction) computes x+y;
# postcondition #2 intentionally contradicts the computed value -> should FAIL
SPEC_BAD_POST = '{"function_id":"FN-20260715-0002","spec_version":"1.0.0","name":"add","domain":"symbolic","inputs":{"x":"integer","y":"integer"},"outputs":{"result":"integer"},"preconditions":[{"expression":"x >= 0","message":"x"}],"postconditions":[{"expression":"result == x + y","message":"extract"},{"expression":"result == x - y","message":"contradiction"}],"effects_declared":["pure"],"created_at":"2026-07-15T12:00:00Z"}'

# division by zero at runtime
SPEC_DIV0 = '{"function_id":"FN-20260715-0003","spec_version":"1.0.0","name":"div","domain":"symbolic","inputs":{"a":"integer","b":"integer"},"outputs":{"q":"integer"},"preconditions":[{"expression":"a >= 0","message":"a"}],"postconditions":[{"expression":"q == a / b","message":"q"}],"effects_declared":["pure"],"created_at":"2026-07-15T12:00:00Z"}'


class Fixture(unittest.TestCase):
    def setUp(self):
        self.parser = N1FunctionSpecParser()
        self.enc = N2RepresentationEncoder()
        self.comp = N3SymbolicCompiler()
        self.pack = N4ArtifactPackager()
        self.interp = N5Interpreter()

    def _artifact(self, spec_json):
        spec = self.parser.parse(spec_json)
        rep = self.enc.encode(spec)
        compiled = self.comp.compile(spec, rep)
        return self.pack.package(compiled, spec, rep)


class TestN5Positive(Fixture):
    def test_execute_ok(self):
        art = self._artifact(SPEC_ADD)
        r = self.interp.execute(art, {'x': 3, 'y': 7})
        self.assertEqual(r['status'], 'OK')
        self.assertEqual(r['outputs']['result'], 10)
        self.assertIn('execution_id', r)
        self.assertIn('trace_id', r)

    def test_deterministic_exec_id_format(self):
        art = self._artifact(SPEC_ADD)
        r1 = self.interp.execute(art, {'x': 1, 'y': 1})
        r2 = self.interp.execute(art, {'x': 2, 'y': 2})
        self.assertTrue(r1['execution_id'].startswith('EXE-FN-20260715-0001'))
        self.assertTrue(r2['execution_id'].startswith('EXE-FN-20260715-0001'))


class TestN5Negative(Fixture):
    def test_precondition_failed(self):
        art = self._artifact(SPEC_ADD)
        r = self.interp.execute(art, {'x': -5, 'y': 3})
        self.assertEqual(r['status'], 'PRECONDITION_FAILED')
        self.assertFalse(r['precondition_result']['passed'])

    def test_type_error_missing_input(self):
        art = self._artifact(SPEC_ADD)
        r = self.interp.execute(art, {'x': 3})
        self.assertEqual(r['status'], 'TYPE_ERROR')
        self.assertTrue(any(e['variable'] == 'y' for e in r['errors']))

    def test_type_error_wrong_type(self):
        art = self._artifact(SPEC_ADD)
        r = self.interp.execute(art, {'x': 'three', 'y': 7})
        self.assertEqual(r['status'], 'TYPE_ERROR')

    def test_type_error_float_for_integer(self):
        art = self._artifact(SPEC_ADD)
        r = self.interp.execute(art, {'x': 3.5, 'y': 7})
        self.assertEqual(r['status'], 'TYPE_ERROR')

    def test_postcondition_failed(self):
        art = self._artifact(SPEC_BAD_POST)
        r = self.interp.execute(art, {'x': 3, 'y': 7})
        self.assertEqual(r['status'], 'POSTCONDITION_FAILED')
        self.assertFalse(r['postcondition_result']['passed'])

    def test_runtime_error_div0(self):
        art = self._artifact(SPEC_DIV0)
        r = self.interp.execute(art, {'a': 1, 'b': 0})
        self.assertEqual(r['status'], 'RUNTIME_ERROR')


if __name__ == '__main__':
    unittest.main()
