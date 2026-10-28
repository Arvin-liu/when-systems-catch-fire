"""121Q6 Step 016: multi-node integration — full Function OS pipeline (N1->N9)."""
import unittest, copy

from function_os.n1_functionspec_parser import N1FunctionSpecParser
from function_os.n2_representation import N2RepresentationEncoder
from function_os.n3_compiler import N3SymbolicCompiler
from function_os.n4_artifact_packager import N4ArtifactPackager
from function_os.n5_interpreter import N5Interpreter
from function_os.n6_execution_trace import N6TraceCapture
from function_os.n7_validator import N7Validator
from function_os.n9_registry import N9RegistryStore, N9RegistryUpdater, N9RegistryValidator

SPEC = '{"function_id":"FN-20260715-0001","spec_version":"1.0.0","name":"add","domain":"symbolic","inputs":{"x":"integer","y":"integer"},"outputs":{"result":"integer"},"preconditions":[{"expression":"x >= 0","message":"x non-negative"}],"postconditions":[{"expression":"result == x + y","message":"r == sum"}],"effects_declared":["pure"],"created_at":"2026-07-15T12:00:00Z"}'


def build_pipeline(spec_json):
    parser = N1FunctionSpecParser()
    enc = N2RepresentationEncoder()
    comp = N3SymbolicCompiler()
    pack = N4ArtifactPackager()
    spec = parser.parse(spec_json)
    rep = enc.encode(spec)
    compiled = comp.compile(spec, rep)
    artifact = pack.package(compiled, spec, rep)
    return spec, rep, artifact, compiled


class TestFullChain(unittest.TestCase):
    def test_happy_path_end_to_end(self):
        spec, rep, artifact, compiled = build_pipeline(SPEC)
        self.assertEqual(artifact['spec_hash'], spec['spec_hash'])

        interp = N5Interpreter()
        result = interp.execute(artifact, {'x': 3, 'y': 7})
        self.assertEqual(result['status'], 'OK')
        self.assertEqual(result['outputs']['result'], 10)

        trace = N6TraceCapture().capture(result, spec)
        val = N7Validator().validate(spec, rep, artifact, trace)
        self.assertEqual(val['status'], 'PASS')

        store = N9RegistryStore()
        rec = dict(spec); rec.update({
            'artifact_hash': artifact['artifact_hash'],
            'representation_hash': artifact['representation_hash'],
            'trace_hash': trace['trace_hash'],
            'compiler_version': compiled['compiler_version'],
            'content_hash': artifact['content_hash'],
        })
        created = store.create(rec)
        self.assertEqual(created['revision'], 1)
        self.assertTrue(N9RegistryValidator().validate(store)['valid'])

    def test_precondition_failure_not_registered(self):
        spec, rep, artifact, compiled = build_pipeline(SPEC)
        interp = N5Interpreter()
        result = interp.execute(artifact, {'x': -1, 'y': 7})
        self.assertEqual(result['status'], 'PRECONDITION_FAILED')
        # not persisted to registry
        store = N9RegistryStore()
        self.assertIsNone(store.read('FN-20260715-0001'))

    def test_cross_node_hash_chain_consistent(self):
        spec, rep, artifact, compiled = build_pipeline(SPEC)
        # N4 content_hash must match recomputed payload
        import hashlib, json
        payload_bytes = json.dumps(artifact['payload'], sort_keys=True, ensure_ascii=False).encode()
        self.assertEqual(artifact['content_hash'], hashlib.sha256(payload_bytes).hexdigest())
        # N2 ir_hash present and referenced by N4
        self.assertEqual(artifact['representation_hash'], rep['ir_hash'])
        # N1 spec_hash present in N2 and N4
        self.assertEqual(rep['spec_hash'], spec['spec_hash'])
        self.assertEqual(artifact['spec_hash'], spec['spec_hash'])

    def test_deterministic_rebuild_same_hashes(self):
        s1, r1, a1, _ = build_pipeline(SPEC)
        s2, r2, a2, _ = build_pipeline(SPEC)
        self.assertEqual(a1['artifact_hash'], a2['artifact_hash'])
        self.assertEqual(r1['ir_hash'], r2['ir_hash'])

    def test_registry_update_and_rollback(self):
        spec, rep, artifact, compiled = build_pipeline(SPEC)
        store = N9RegistryStore()
        upd = N9RegistryUpdater(store)
        rec = dict(spec); rec.update({
            'artifact_hash': artifact['artifact_hash'],
            'representation_hash': artifact['representation_hash'],
            'trace_hash': 't1', 'compiler_version': compiled['compiler_version'],
            'content_hash': artifact['content_hash']})
        store.create(rec)
        r2 = upd.update('FN-20260715-0001', {'trace_hash': 't2'})
        self.assertEqual(r2['revision'], 2)
        r3 = upd.rollback('FN-20260715-0001', 1)
        self.assertEqual(r3['revision'], 3)
        self.assertEqual(r3['trace_hash'], 't1')


if __name__ == '__main__':
    unittest.main()
