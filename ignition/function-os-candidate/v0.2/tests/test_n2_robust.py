"""121Q6 Step 008: N2 Representation robust tests."""
import unittest, json, copy

from function_os.n1_functionspec_parser import N1FunctionSpecParser
from function_os.n2_representation import (N2RepresentationEncoder, N2RepresentationDecoder, N2RepresentationValidator)

SPEC = '{"function_id":"FN-20260715-0001","spec_version":"1.0.0","name":"add","domain":"symbolic","inputs":{"x":"integer","y":"integer"},"outputs":{"result":"integer"},"preconditions":[{"expression":"x >= 0","message":"x non-negative"}],"postconditions":[{"expression":"result == x + y","message":"r == sum"}],"effects_declared":["pure"],"created_at":"2026-07-15T12:00:00Z"}'


class TestN2EncodePositive(unittest.TestCase):
    def setUp(self):
        self.parser = N1FunctionSpecParser()
        self.enc = N2RepresentationEncoder()

    def test_encode_basic(self):
        spec = self.parser.parse(SPEC)
        rep = self.enc.encode(spec)
        self.assertTrue(rep['representation_id'].startswith('REP-'))
        self.assertEqual(rep['representation_type'], 'symbolic_ast')
        self.assertEqual(rep['spec_hash'], spec['spec_hash'])
        self.assertEqual(rep['canonical_ir']['entrypoint'], 'add')

    def test_expression_extraction(self):
        spec = self.parser.parse(SPEC)
        rep = self.enc.encode(spec)
        self.assertEqual(rep['canonical_ir']['expressions']['result'], 'x + y')

    def test_roundtrip_decode(self):
        spec = self.parser.parse(SPEC)
        rep = self.enc.encode(spec)
        dec = N2RepresentationDecoder().decode(rep)
        self.assertEqual(dec['entrypoint'], 'add')
        self.assertEqual(dec['expressions']['result'], 'x + y')
        self.assertEqual(dec['input_map'], {'x': 'integer', 'y': 'integer'})


class TestN2ValidatorNegative(unittest.TestCase):
    def setUp(self):
        self.parser = N1FunctionSpecParser()
        self.enc = N2RepresentationEncoder()
        self.val = N2RepresentationValidator()

    def _rep(self):
        return self.enc.encode(self.parser.parse(SPEC))

    def test_spec_hash_mismatch(self):
        spec = self.parser.parse(SPEC)
        rep = self.enc.encode(spec)
        bad_spec = dict(spec)
        bad_spec['spec_hash'] = 'deadbeef' * 8
        issues = self.val.validate(rep, bad_spec)
        self.assertTrue(any(i['check'] == 'spec_hash_match' and not i['passed'] for i in issues))

    def test_ir_input_incompleteness(self):
        spec = self.parser.parse(SPEC)
        rep = self.enc.encode(spec)
        tampered = copy.deepcopy(rep)
        tampered['canonical_ir']['input_map'].pop('y')
        issues = self.val.validate(tampered, spec)
        self.assertTrue(any(i['check'] == 'ir_input_completeness' and not i['passed'] for i in issues))

    def test_ir_output_incompleteness(self):
        spec = self.parser.parse(SPEC)
        rep = self.enc.encode(spec)
        tampered = copy.deepcopy(rep)
        tampered['canonical_ir']['output_map']['extra'] = 'integer'
        issues = self.val.validate(tampered, spec)
        self.assertTrue(any(i['check'] == 'ir_output_completeness' and not i['passed'] for i in issues))

    def test_representation_type_rejected(self):
        spec = self.parser.parse(SPEC)
        rep = self.enc.encode(spec)
        tampered = dict(rep)
        tampered['representation_type'] = 'neural_weights'
        issues = self.val.validate(tampered, spec)
        self.assertTrue(any(i['check'] == 'representation_type' and not i['passed'] for i in issues))

    def test_provenance_missing_encoder_warning(self):
        spec = self.parser.parse(SPEC)
        rep = self.enc.encode(spec)
        tampered = copy.deepcopy(rep)
        tampered['provenance'] = {}
        issues = self.val.validate(tampered, spec)
        self.assertTrue(any(i['check'] == 'provenance_encoder' for i in issues))

    def test_clean_rep_zero_issues(self):
        rep = self._rep()
        spec = self.parser.parse(SPEC)
        self.assertEqual(self.val.validate(rep, spec), [])


class TestN2NestedEqualityRegression(unittest.TestCase):
    """Regression for task-105 finding: postconditions with nested '==' such as
    'result == (x == y)' were split on every '==' (global split), yielding an
    unbalanced RHS like '(x ' and a downstream "'(' was never closed" runtime
    error. The fix splits on the FIRST '==' only."""

    NESTED_EQ_SPEC = (
        '{"function_id":"FN-20260730-0156","spec_version":"1.0.0","name":"eq",'
        '"domain":"symbolic","inputs":{"x":"integer","y":"integer"},'
        '"outputs":{"result":"boolean"},"preconditions":[],'
        '"postconditions":[{"expression":"result == (x == y)",'
        '"message":"eq semantics"}],"effects_declared":["pure"],'
        '"created_at":"2026-07-30T00:00:00Z"}'
    )

    def setUp(self):
        self.parser = N1FunctionSpecParser()
        self.enc = N2RepresentationEncoder()

    def test_nested_equality_extraction(self):
        spec = self.parser.parse(self.NESTED_EQ_SPEC)
        exprs = self.enc._extract_expressions(spec)
        self.assertEqual(exprs['result'], '(x == y)')

    def test_nested_equality_executes(self):
        from function_os.n3_compiler import N3SymbolicCompiler
        from function_os.n4_artifact_packager import N4ArtifactPackager
        from function_os.n5_interpreter import N5Interpreter

        spec = self.parser.parse(self.NESTED_EQ_SPEC)
        rep = self.enc.encode(spec)
        compiled = N3SymbolicCompiler().compile(spec, rep)
        art = N4ArtifactPackager().package(compiled, spec, rep)

        res_eq = N5Interpreter().execute(art, {"x": 2, "y": 2})
        self.assertEqual(res_eq['status'], 'OK')
        self.assertEqual(res_eq['outputs']['result'], True)

        res_ne = N5Interpreter().execute(art, {"x": 2, "y": 3})
        self.assertEqual(res_ne['status'], 'OK')
        self.assertEqual(res_ne['outputs']['result'], False)


if __name__ == '__main__':
    unittest.main()
