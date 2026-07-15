"""N9 Registry tests."""
import sys, os, tempfile, shutil, hashlib

sys.path.insert(0, '/tmp/wscf-121q2/function-os-candidate/v0.1/function_os')

# Import modules
with open(os.path.join(os.path.dirname(__file__), '../function_os/n9_registry_store.py')) as f:
    exec(compile(f.read(), 'n9_registry_store.py', 'exec'))

with open(os.path.join(os.path.dirname(__file__), '../function_os/n9_registry_updater.py')) as f:
    src = f.read()
    exec(compile('\n'.join(l for l in src.split('\n') if 'from function_os_candidate' not in l), 'n9_registry_updater.py', 'exec'))

with open(os.path.join(os.path.dirname(__file__), '../function_os/n9_registry_validator.py')) as f:
    exec(compile(f.read(), 'n9_registry_validator.py', 'exec'))

def t1():
    tmp = tempfile.mkdtemp()
    try:
        s = N9RegistryStore(tmp)
        sh = hashlib.sha256(b"s").hexdigest()
        ah = hashlib.sha256(b"a").hexdigest()
        ch = hashlib.sha256(f'FN-20260715-0001|{sh}|{ah}|1'.encode()).hexdigest()
        r = s.create({"function_id": "FN-20260715-0001", "revision": 1, "spec_hash": sh, "artifact_hash": ah, "compiler_version": "0.1.0", "status": "active", "created_at": "2026-07-15T02:20:00Z", "content_hash": ch})
        assert r['ok'], f"Create failed: {r}"
        rd = s.read("FN-20260715-0001")
        assert rd['ok'] and rd['record']['revision'] == 1
        return True
    finally: shutil.rmtree(tmp)

def t2():
    tmp = tempfile.mkdtemp()
    try:
        s = N9RegistryStore(tmp)
        sh = hashlib.sha256(b"s").hexdigest()
        ah = hashlib.sha256(b"a").hexdigest()
        ch = hashlib.sha256(f'FN-20260715-0001|{sh}|{ah}|1'.encode()).hexdigest()
        s.create({"function_id": "FN-20260715-0001", "revision": 1, "spec_hash": sh, "artifact_hash": ah, "compiler_version": "0.1.0", "status": "active", "created_at": "2026-07-15T02:20:00Z", "content_hash": ch})
        r2 = s.create({"function_id": "FN-20260715-0001", "revision": 1, "spec_hash": sh, "artifact_hash": ah, "compiler_version": "0.1.0", "status": "active", "created_at": "2026-07-15T02:20:00Z", "content_hash": ch})
        assert not r2['ok'] and r2['error'] == 'DUPLICATE_ID'
        return True
    finally: shutil.rmtree(tmp)

def t3():
    tmp = tempfile.mkdtemp()
    try:
        s = N9RegistryStore(tmp)
        sh = hashlib.sha256(b"s").hexdigest()
        ah = hashlib.sha256(b"a").hexdigest()
        r = s.create({"function_id": "FN-20260715-0001", "revision": 1, "spec_hash": sh, "artifact_hash": ah, "compiler_version": "0.1.0", "status": "active", "created_at": "2026-07-15T02:20:00Z", "content_hash": "0" * 64})
        assert not r['ok'] and r['error'] == 'HASH_MISMATCH'
        return True
    finally: shutil.rmtree(tmp)

def t4():
    tmp = tempfile.mkdtemp()
    try:
        s = N9RegistryStore(tmp)
        u = N9RegistryUpdater(s)
        F = "FN-20260715-0001"
        sh = hashlib.sha256(b"s").hexdigest()
        ah = hashlib.sha256(b"a").hexdigest()
        ch = hashlib.sha256(f'{F}|{sh}|{ah}|1'.encode()).hexdigest()
        s.create({"function_id": F, "revision": 1, "spec_hash": sh, "artifact_hash": ah, "compiler_version": "0.1.0", "status": "active", "created_at": "2026-07-15T02:20:00Z", "content_hash": ch})
        sh2 = hashlib.sha256(b"s2").hexdigest()
        ah2 = hashlib.sha256(b"a2").hexdigest()
        ch2 = hashlib.sha256(f'{F}|{sh2}|{ah2}|2'.encode()).hexdigest()
        assert u.update(F, {"function_id": F, "spec_hash": sh2, "artifact_hash": ah2, "compiler_version": "0.1.0", "status": "active", "created_at": "2026-07-15T02:21:00Z", "content_hash": ch2})['ok']
        assert u.rollback(F, 1, "bug")['ok']
        assert s.history(F)['count'] == 3
        assert s.read(F, revision=2)['ok']
        return True
    finally: shutil.rmtree(tmp)

def t5():
    tmp = tempfile.mkdtemp()
    try:
        s = N9RegistryStore(tmp)
        v = N9RegistryValidator(s)
        assert len(v.validate_all()) == 0
        F = "FN-20260715-0001"
        sh = hashlib.sha256(b"s").hexdigest()
        ah = hashlib.sha256(b"a").hexdigest()
        ch = hashlib.sha256(f'{F}|{sh}|{ah}|1'.encode()).hexdigest()
        s.create({"function_id": F, "revision": 1, "spec_hash": sh, "artifact_hash": ah, "compiler_version": "0.1.0", "status": "active", "created_at": "2026-07-15T02:20:00Z", "content_hash": ch})
        assert len(v.validate_all()) == 0
        return True
    finally: shutil.rmtree(tmp)

def t6():
    tmp = tempfile.mkdtemp()
    try:
        s = N9RegistryStore(tmp)
        ai = hashlib.sha256
        for i in range(3):
            fid = f"FN-20260715-{i:04d}"
            sh = ai(f"s{i}".encode()).hexdigest()
            ah = ai(f"a{i}".encode()).hexdigest()
            ch = ai(f'{fid}|{sh}|{ah}|1'.encode()).hexdigest()
            s.create({"function_id": fid, "revision": 1, "spec_hash": sh, "artifact_hash": ah, "compiler_version": "0.1.0", "status": "active", "created_at": "2026-07-15T02:20:00Z", "content_hash": ch})
        assert s.list()['count'] == 3
        return True
    finally: shutil.rmtree(tmp)

tests = [t1, t2, t3, t4, t5, t6]
passed = 0
for t in tests:
    try:
        ok = t()
        print(f"  PASS: {t.__name__}")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {t.__name__} - {e}")
print(f"\n{passed}/{len(tests)} tests passed")
