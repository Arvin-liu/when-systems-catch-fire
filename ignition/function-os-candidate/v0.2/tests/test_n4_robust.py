"""121Q6 Step 010: N4 Artifact robust tests."""
import unittest, copy

from function_os.n1_functionspec_parser import N1FunctionSpecParser
from function_os.n2_representation import N2RepresentationEncoder
from function_os.n3_compiler import N3SymbolicCompiler
from function_os.n4_artifact_packager import N4ArtifactPackager, N4ArtifactVerifier

SPEC = '{"function_id":"FN-20260715-0001","spec_version":"1.0.0","name":"add","domain":"symbolic","inputs":{"x":"integer","y":"integer"},"outputs":{"result":"integer"},"preconditions":[{"expression":"x >= 0","message":"x non-negative"}],"postconditions":[{"expression":"result == x + y","message":"r == sum"}],"effects_declared":["pure"],"created_at":"2026-07-15T12:00:00Z"}'


class Fixture(unittest.TestCase):
    def setUp(self):
        self.parser = N1FunctionSpecParser()
        self.enc = N2RepresentationEncoder()
        self.comp = N3SymbolicCompiler()
        self.pack = N4ArtifactPackager()
        self.ver = N4ArtifactVerifier()

    def _artifact(self):
        spec = self.parser.parse(SPEC)
        rep = self.enc.encode(spec)
        compiled = self.comp.compile(spec, rep)
        return spec, self.pack.package(compiled, spec, rep)


class TestN4Positive(Fixture):
    def test_package_ok(self):
        spec, art = self._artifact()
        self.assertTrue(art['artifact_id'].startswith('ART-'))
        self.assertEqual(art['spec_hash'], spec['spec_hash'])
        self.assertIn('artifact_hash', art)
        self.assertTrue(art['manifest']['immutable'])

    def test_deterministic_packaging(self):
        _, a1 = self._artifact()
        _, a2 = self._artifact()
        self.assertEqual(a1['content_hash'], a2['content_hash'])
        self.assertEqual(a1['artifact_hash'], a2['artifact_hash'])

    def test_verify_valid(self):
        _, art = self._artifact()
        res = self.ver.verify(art)
        self.assertTrue(res['valid'])
        self.assertTrue(all(c['passed'] for c in res['checks']))


class TestN4Negative(Fixture):
    def test_tamper_content_hash(self):
        _, art = self._artifact()
        bad = copy.deepcopy(art)
        bad['content_hash'] = 'deadbeef' * 8
        res = self.ver.verify(bad)
        self.assertFalse(res['valid'])
        self.assertTrue(any(not c['passed'] and 'content_hash' in c['check'] for c in res['checks']))

    def test_tamper_payload(self):
        _, art = self._artifact()
        bad = copy.deepcopy(art)
        bad['payload'] = dict(bad['payload'])
        bad['payload']['expressions'] = {'result': 'x - y'}  # alter semantics
        res = self.ver.verify(bad)
        self.assertFalse(res['valid'])

    def test_tamper_artifact_hash(self):
        _, art = self._artifact()
        bad = copy.deepcopy(art)
        bad['artifact_hash'] = '00' * 32
        res = self.ver.verify(bad)
        self.assertFalse(res['valid'])
        self.assertTrue(any(not c['passed'] and 'artifact_hash' in c['check'] for c in res['checks']))

    def test_missing_immutable_flag(self):
        _, art = self._artifact()
        bad = copy.deepcopy(art)
        bad['manifest'] = dict(bad['manifest'])
        bad['manifest']['immutable'] = False
        res = self.ver.verify(bad)
        self.assertFalse(res['valid'])


if __name__ == '__main__':
    unittest.main()
