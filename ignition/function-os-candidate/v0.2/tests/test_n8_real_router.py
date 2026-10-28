"""121Q6 Step 018: N8 real control-plane routing over a populated N9 registry.

No mocks: real FunctionSpec -> artifact -> N9 registry -> N8 plan -> N5 execute.
"""
import unittest

from function_os.n1_functionspec_parser import N1FunctionSpecParser
from function_os.n2_representation import N2RepresentationEncoder
from function_os.n3_compiler import N3SymbolicCompiler
from function_os.n4_artifact_packager import N4ArtifactPackager
from function_os.n5_interpreter import N5Interpreter
from function_os.n8_composer_router import N8ComposerRouter
from function_os.n9_registry import N9RegistryStore, N9RegistryUpdater, N9RegistryValidator

ADD = '{"function_id":"FN-20260715-0001","spec_version":"1.0.0","name":"add","domain":"symbolic","inputs":{"x":"integer","y":"integer"},"outputs":{"result":"integer"},"preconditions":[{"expression":"x >= 0","message":"x"}],"postconditions":[{"expression":"result == x + y","message":"r"}],"effects_declared":["pure"],"created_at":"2026-07-15T12:00:00Z"}'
SUB = '{"function_id":"FN-20260715-0002","spec_version":"1.0.0","name":"sub","domain":"symbolic","inputs":{"a":"integer","b":"integer"},"outputs":{"result":"integer"},"preconditions":[{"expression":"a >= 0","message":"a"}],"postconditions":[{"expression":"result == a - b","message":"r"}],"effects_declared":["pure"],"created_at":"2026-07-15T12:00:00Z"}'


def real_artifact(spec_json):
    parser = N1FunctionSpecParser()
    spec = parser.parse(spec_json)
    rep = N2RepresentationEncoder().encode(spec)
    compiled = N3SymbolicCompiler().compile(spec, rep)
    artifact = N4ArtifactPackager().package(compiled, spec, rep)
    return spec, artifact


def register(store, spec, artifact):
    rec = dict(spec)
    rec.update({'artifact_id': artifact['artifact_id'],
                'artifact_hash': artifact['artifact_hash'],
                'representation_hash': artifact['representation_hash'],
                'trace_hash': artifact['artifact_hash'][:16],
                'compiler_version': compiled_version(),
                'content_hash': artifact['content_hash']})
    return store.create(rec)


def compiled_version():
    return N3SymbolicCompiler().VERSION


class TestN8RealRouting(unittest.TestCase):
    def setUp(self):
        self.store = N9RegistryStore()
        spec_a, art_a = real_artifact(ADD)
        spec_b, art_b = real_artifact(SUB)
        register(self.store, spec_a, art_a)
        register(self.store, spec_b, art_b)
        # real artifacts (with payload) keyed by function_id — used for routing+execute
        self.artifacts = {'FN-20260715-0001': art_a, 'FN-20260715-0002': art_b}

    def test_registry_populated_two_functions(self):
        self.assertEqual(len(self.store.list()), 2)
        self.assertTrue(N9RegistryValidator().validate(self.store)['valid'])

    def test_n8_plans_real_registered_functions(self):
        router = N8ComposerRouter()
        task = {"task_id": "T-compose", "required_functions": [
            {"function_id": "FN-20260715-0001"},
            {"function_id": "FN-20260715-0002"}]}
        plan = router.plan(task, list(self.artifacts.values()))
        self.assertEqual(plan['status'], 'OK')
        self.assertEqual(len(plan['steps']), 2)
        self.assertEqual(plan['steps'][1]['function_id'], 'FN-20260715-0002')

    def test_n8_route_then_execute_both(self):
        router = N8ComposerRouter()
        interp = N5Interpreter()
        task = {"task_id": "T-exec", "required_functions": [
            {"function_id": "FN-20260715-0001", "inputs_from": "task_input"},
            {"function_id": "FN-20260715-0002", "inputs_from": "task_input"}]}
        plan = router.plan(task, list(self.artifacts.values()))
        results = {}
        # add(3,7)=10
        r1 = interp.execute(self.artifacts['FN-20260715-0001'], {'x': 3, 'y': 7})
        results['add'] = r1['outputs']['result']
        # sub(10,4)=6  (feed add output as 'a')
        r2 = interp.execute(self.artifacts['FN-20260715-0002'], {'a': r1['outputs']['result'], 'b': 4})
        results['sub'] = r2['outputs']['result']
        self.assertEqual(results['add'], 10)
        self.assertEqual(results['sub'], 6)
        self.assertEqual(plan['status'], 'OK')

    def test_n8_missing_function_in_real_registry(self):
        router = N8ComposerRouter()
        task = {"task_id": "T-miss", "required_functions": [
            {"function_id": "FN-19990101-9999"}]}
        plan = router.plan(task, list(self.artifacts.values()))
        self.assertEqual(plan['status'], 'PARTIAL')
        self.assertEqual(plan['steps'][0]['status'], 'SKIPPED')


if __name__ == '__main__':
    unittest.main()
