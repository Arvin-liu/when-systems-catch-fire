"""Tests: N1 FunctionSpec Parser → N2 Representation → N3 Compiler → N4 Artifact."""
import unittest

from function_os.n1_functionspec_parser import N1FunctionSpecParser, FunctionSpecParseError
from function_os.n2_representation import N2RepresentationEncoder, N2RepresentationValidator
from function_os.n3_compiler import N3SymbolicCompiler
from function_os.n4_artifact_packager import N4ArtifactPackager, N4ArtifactVerifier

SPEC = """{"function_id":"FN-20260715-0001","spec_version":"1.0.0","name":"add","domain":"symbolic","inputs":{"x":"integer","y":"integer"},"outputs":{"result":"integer"},"preconditions":[{"expression":"x >= 0","message":"x"}],"postconditions":[{"expression":"result == x + y","message":"r"}],"effects_declared":["pure"],"created_at":"2026-07-15T00:00:00Z"}"""


class TestN1FunctionSpecParser(unittest.TestCase):
    def setUp(self):
        self.parser = N1FunctionSpecParser()

    def test_parse_valid(self):
        spec = self.parser.parse(SPEC)
        self.assertEqual(spec['function_id'], 'FN-20260715-0001')
        self.assertEqual(spec['domain'], 'symbolic')
        self.assertIn('spec_hash', spec)
        self.assertEqual(len(spec['spec_hash']), 64)

    def test_parse_invalid_function_id(self):
        with self.assertRaises(FunctionSpecParseError):
            self.parser.parse(SPEC.replace('FN-20260715-0001', 'BAD-ID'))

    def test_parse_wrong_domain(self):
        with self.assertRaises(FunctionSpecParseError):
            self.parser.parse(SPEC.replace('"symbolic"', '"neural"'))

    def test_parse_hash_stability(self):
        s1 = self.parser.parse(SPEC)
        s2 = self.parser.parse(SPEC)
        self.assertEqual(s1['spec_hash'], s2['spec_hash'])


class TestN2Representation(unittest.TestCase):
    def setUp(self):
        self.parser = N1FunctionSpecParser()
        self.encoder = N2RepresentationEncoder()
        self.validator = N2RepresentationValidator()
        self.spec = self.parser.parse(SPEC)

    def test_encode(self):
        rep = self.encoder.encode(self.spec)
        self.assertTrue(rep['representation_id'].startswith('REP-FN-'))
        self.assertEqual(rep['representation_type'], 'symbolic_ast')
        self.assertIn('ir_hash', rep)

    def test_validate_ok(self):
        rep = self.encoder.encode(self.spec)
        issues = self.validator.validate(rep, self.spec)
        self.assertEqual(len(issues), 0)

    def test_validate_hash_mismatch(self):
        rep = self.encoder.encode(self.spec)
        rep['spec_hash'] = 'deadbeef'
        issues = self.validator.validate(rep, self.spec)
        self.assertTrue(any(i['check'] == 'spec_hash_match' and not i.get('passed', True)
                          for i in issues))


class TestN3Compiler(unittest.TestCase):
    def setUp(self):
        self.parser = N1FunctionSpecParser()
        self.encoder = N2RepresentationEncoder()
        self.compiler = N3SymbolicCompiler()
        self.spec = self.parser.parse(SPEC)
        self.rep = self.encoder.encode(self.spec)

    def test_compile_ok(self):
        compiled = self.compiler.compile(self.spec, self.rep)
        self.assertEqual(compiled['status'], 'OK')
        self.assertTrue(compiled['compiled_id'].startswith('CMP-'))

    def test_compile_hash_mismatch(self):
        bad_rep = dict(self.rep)
        bad_rep['spec_hash'] = 'deadbeef'
        compiled = self.compiler.compile(self.spec, bad_rep)
        self.assertEqual(compiled['status'], 'ERROR')

    def test_payload_has_entrypoint(self):
        compiled = self.compiler.compile(self.spec, self.rep)
        self.assertEqual(compiled['payload']['entrypoint'], 'add')


class TestN4Artifact(unittest.TestCase):
    def setUp(self):
        self.parser = N1FunctionSpecParser()
        self.encoder = N2RepresentationEncoder()
        self.compiler = N3SymbolicCompiler()
        self.packager = N4ArtifactPackager()
        self.verifier = N4ArtifactVerifier()
        self.spec = self.parser.parse(SPEC)
        self.rep = self.encoder.encode(self.spec)
        self.compiled = self.compiler.compile(self.spec, self.rep)

    def test_package(self):
        artifact = self.packager.package(self.compiled, self.spec, self.rep)
        self.assertTrue(artifact['artifact_id'].startswith('ART-'))
        self.assertIn('artifact_hash', artifact)

    def test_verify_valid(self):
        artifact = self.packager.package(self.compiled, self.spec, self.rep)
        result = self.verifier.verify(artifact)
        self.assertTrue(result['valid'])

    def test_verify_tampered(self):
        artifact = self.packager.package(self.compiled, self.spec, self.rep)
        artifact['payload'] = {'tampered': True}
        result = self.verifier.verify(artifact)
        self.assertFalse(result['valid'])


if __name__ == '__main__':
    unittest.main()
