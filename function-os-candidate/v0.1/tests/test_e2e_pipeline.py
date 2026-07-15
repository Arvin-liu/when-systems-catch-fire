"""End-to-end pipeline test: Spec → Parse → Check → Compile → Interpret → Package → Verify → Register → Validate."""

import sys, os, json, hashlib, tempfile, shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../function_os'))

with open(os.path.join(os.path.dirname(__file__), '../function_os/n1_safe_expression_dsl.py')) as f:
    exec(compile(f.read(), 'dsl', 'exec'))
with open(os.path.join(os.path.dirname(__file__), '../function_os/n1_functionspec_parser.py')) as f:
    exec(compile(f.read(), 'parser', 'exec'))
with open(os.path.join(os.path.dirname(__file__), '../function_os/n1_semantic_checker.py')) as f:
    exec(compile(f.read(), 'semantic', 'exec'))
with open(os.path.join(os.path.dirname(__file__), '../function_os/n2_symbolic_compiler.py')) as f:
    exec(compile(f.read(), 'compiler', 'exec'))
with open(os.path.join(os.path.dirname(__file__), '../function_os/n3_expression_interpreter.py')) as f:
    exec(compile(f.read(), 'interp', 'exec'))
with open(os.path.join(os.path.dirname(__file__), '../function_os/n4_artifact_packager.py')) as f:
    exec(compile(f.read(), 'packager', 'exec'))
with open(os.path.join(os.path.dirname(__file__), '../function_os/n9_registry_store.py')) as f:
    exec(compile(f.read(), 'store', 'exec'))
with open(os.path.join(os.path.dirname(__file__), '../function_os/n9_registry_updater.py')) as f:
    src = f.read()
    clean = [l for l in src.split('\n') if 'from function_os_candidate' not in l]
    exec(compile('\n'.join(clean), 'updater', 'exec'))
with open(os.path.join(os.path.dirname(__file__), '../function_os/n9_registry_validator.py')) as f:
    exec(compile(f.read(), 'validator', 'exec'))

def test_e2e():
    dsl = SafeExpressionDSL()
    parser = N1FunctionSpecParser()
    checker = N1SemanticChecker()
    compiler = N2SymbolicCompiler()
    interpreter = N3ExpressionInterpreter(dsl)
    packager = N4ArtifactPackager()

    spec_json = {
        "function_id": "FN-20260715-0001",
        "spec_version": "1.0.0",
        "name": "add", "domain": "symbolic",
        "inputs": {"x": "integer", "y": "integer"},
        "outputs": {"result": "integer"},
        "preconditions": [{"expression": "x >= 0", "message": "x"}],
        "postconditions": [{"expression": "result == x + y", "message": "result == sum"}],
        "effects_declared": ["pure"],
        "created_at": "2026-07-15T02:20:00Z"
    }

    spec = parser.parse(json.dumps(spec_json))
    assert 'spec_hash' in spec

    assert len(checker.check(spec)) == 0

    compiled = compiler.compile(spec)['compiled']
    result = interpreter.execute(compiled, {"x": 3, "y": 7})
    assert result['ok'] and result['outputs']['result'] == 10

    artifact = packager.package(spec, compiled)['artifact']
    assert packager.verify(artifact)['ok']

    tmpdir = tempfile.mkdtemp()
    try:
        store = N9RegistryStore(tmpdir)
        m = artifact['manifest']
        ch = store._compute_hash(spec['function_id'], spec['spec_hash'], m.get('artifact_hash',''), '1')
        assert store.create({"function_id":spec['function_id'],"revision":1,"spec_hash":spec['spec_hash'],"artifact_hash":m.get('artifact_hash',''),"compiler_version":"0.1.0","status":"active","created_at":"2026-07-15T02:20:00Z","content_hash":ch,"spec":spec,"artifact":m})['ok']
        assert store.read(spec['function_id'])['ok']
        return True
    finally:
        shutil.rmtree(tmpdir)

# Run
passed = test_e2e()
print(f"E2E pipeline test: {'PASS' if passed else 'FAIL'}")
