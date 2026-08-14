"""121Q6 Step 015: N9 Registry robust tests."""
import unittest

from function_os.n9_registry import N9RegistryStore, N9RegistryUpdater, N9RegistryValidator

BASE = {"function_id": "FN-20260715-0001", "spec_hash": "abc123",
        "artifact_hash": "def456", "representation_hash": "ghi789",
        "trace_hash": "jkl012", "compiler_version": "0.2.0", "content_hash": "abc123"}


class Fixture(unittest.TestCase):
    def setUp(self):
        self.store = N9RegistryStore()
        self.upd = N9RegistryUpdater(self.store)
        self.val = N9RegistryValidator()
        self.r1 = self.store.create(dict(BASE))


class TestN9CreatePositive(Fixture):
    def test_create_basic(self):
        self.assertEqual(self.r1['revision'], 1)
        self.assertEqual(self.r1['status'], 'active')

    def test_read_latest(self):
        self.assertEqual(self.store.read('FN-20260715-0001')['revision'], 1)

    def test_read_specific_revision(self):
        self.assertEqual(self.store.read('FN-20260715-0001', 1)['revision'], 1)

    def test_read_missing(self):
        self.assertIsNone(self.store.read('FN-19990101-9999'))

    def test_list_one(self):
        self.assertEqual(len(self.store.list()), 1)

    def test_history(self):
        self.assertEqual(len(self.store.history('FN-20260715-0001')), 1)


class TestN9Negative(Fixture):
    def test_invalid_function_id_format(self):
        with self.assertRaises(ValueError):
            self.store.create(dict(BASE, function_id='fn_1'))

    def test_invalid_function_id_short(self):
        with self.assertRaises(ValueError):
            self.store.create(dict(BASE, function_id='FN-20260715-1'))

    def test_duplicate_create_rejected(self):
        with self.assertRaises(ValueError):
            self.store.create(dict(BASE))

    def test_update_missing_function(self):
        with self.assertRaises(ValueError):
            self.upd.update('FN-19990101-9999', {'spec_hash': 'x'})


class TestN9UpdateRollback(Fixture):
    def test_update_increments_revision(self):
        r2 = self.upd.update('FN-20260715-0001', {'spec_hash': 'new'})
        self.assertEqual(r2['revision'], 2)
        self.assertEqual(r2['supersedes'], 1)
        self.assertEqual(self.store.read('FN-20260715-0001')['revision'], 2)

    def test_rollback_creates_new_revision(self):
        self.upd.update('FN-20260715-0001', {'spec_hash': 'new'})
        r3 = self.upd.rollback('FN-20260715-0001', 1)
        self.assertEqual(r3['revision'], 3)
        self.assertEqual(r3['spec_hash'], 'abc123')

    def test_rollback_missing_revision(self):
        with self.assertRaises(ValueError):
            self.upd.rollback('FN-20260715-0001', 99)


class TestN9Validator(Fixture):
    def test_validate_clean(self):
        res = self.val.validate(self.store)
        self.assertTrue(res['valid'])

    def test_validate_detects_duplicate_active(self):
        # Two records with same id would violate uniqueness; simulate by injecting
        dup = N9RegistryStore()
        dup.create(dict(BASE))
        dup.create(dict(BASE, function_id='FN-20260715-0002'))
        # force duplicate active id
        dup._records['FN-20260715-0001'].append(dup._records['FN-20260715-0002'][-1])
        res = N9RegistryValidator().validate(dup)
        self.assertFalse(res['valid'])

    def test_validate_missing_required_field(self):
        bad = N9RegistryStore()
        rec = dict(BASE); del rec['content_hash']
        bad.create(rec)
        res = N9RegistryValidator().validate(bad)
        self.assertFalse(res['valid'])


if __name__ == '__main__':
    unittest.main()
