"""121Q6 Step 009: N3 Compiler robust tests."""
import unittest, copy

from function_os.n1_functionspec_parser import N1FunctionSpecParser
from function_os.n2_representation import N2RepresentationEncoder
from function_os.n3_compiler import N3SymbolicCompiler

SPEC = '{"function_id":"FN-20260715-0001","spec_version":"1.0.0","name":"add","domain":"symbolic","inputs":{"x":"integer","y":"integer"},"outputs":{"result":"integer"},"preconditions":[{"expression":"x >= 0","message":"x non-negative"}],"postconditions":[{"expression":"result == x + y","message":"r == sum"}],"effects_declared":["pure"],"created_at":"2026-07-15T12:00:00Z"}'


class Fixture(unittest.TestCase):
    def setUp(self):
        self.parser = N1FunctionSpecParser()
        self.enc = N2RepresentationEncoder()
        self.comp = N3SymbolicCompiler()

    def _build(self):
        spec = self.parser.parse(SPEC)
        rep = self.enc.encode(spec)
        return spec, rep


class TestN3Positive(Fixture):
    def test_compile_ok(self):
        spec, rep = self._build()
        c = self.comp.compile(spec, rep)
        self.assertEqual(c['status'], 'OK')
        self.assertEqual(c['errors'], [])
        self.assertEqual(c['payload']['entrypoint'], 'add')
        self.assertEqual(c['payload']['expressions']['result'], 'x + y')
        self.assertEqual(c['compiled_id'], 'CMP-FN-20260715-0001-1')

    def test_target_is_n5(self):
        spec, rep = self._build()
        c = self.comp.compile(spec, rep)
        self.assertEqual(c['target'], 'n5_interpreter_v0.2')


class TestN3Negative(Fixture):
    def test_hash_mismatch(self):
        spec, rep = self._build()
        bad_spec = dict(spec)
        bad_spec['spec_hash'] = 'deadbeef' * 8
        c = self.comp.compile(bad_spec, rep)
        self.assertEqual(c['status'], 'ERROR')
        self.assertTrue(any(e['category'] == 'HASH_MISMATCH' for e in c['errors']))

    def test_domain_unsupported(self):
        spec, rep = self._build()
        bad_spec = dict(spec)
        bad_spec['domain'] = 'neural_weight'
        c = self.comp.compile(bad_spec, rep)
        self.assertEqual(c['status'], 'ERROR')
        self.assertTrue(any(e['category'] == 'DOMAIN_UNSUPPORTED' for e in c['errors']))

    def test_representation_type_unsupported(self):
        spec, rep = self._build()
        bad_rep = copy.deepcopy(rep)
        bad_rep['representation_type'] = 'bytecode'
        c = self.comp.compile(spec, bad_rep)
        self.assertEqual(c['status'], 'ERROR')
        self.assertTrue(any(e['category'] == 'DOMAIN_UNSUPPORTED' for e in c['errors']))

    def test_type_mismatch_input(self):
        spec, rep = self._build()
        bad_rep = copy.deepcopy(rep)
        bad_rep['canonical_ir']['input_map'].pop('y')
        c = self.comp.compile(spec, bad_rep)
        self.assertEqual(c['status'], 'ERROR')
        self.assertTrue(any(e['category'] == 'TYPE_MISMATCH' for e in c['errors']))

    def test_undeclared_symbol_in_expression(self):
        spec, rep = self._build()
        bad_rep = copy.deepcopy(rep)
        bad_rep['canonical_ir']['expressions']['result'] = 'x + z'
        c = self.comp.compile(spec, bad_rep)
        self.assertEqual(c['status'], 'ERROR')
        self.assertTrue(any(e['category'] == 'UNDECLARED_SYMBOL' for e in c['errors']))

    def test_no_effects_warning(self):
        spec, rep = self._build()
        bad_spec = dict(spec)
        bad_spec['effects_declared'] = []
        c = self.comp.compile(bad_spec, rep)
        self.assertEqual(c['status'], 'WARNING')
        self.assertTrue(any(w['category'] == 'NO_EFFECTS' for w in c['warnings']))


if __name__ == '__main__':
    unittest.main()
