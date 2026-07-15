"""121Q6 Step 007: N1 FunctionSpec robust tests (positive / negative / boundary)."""
import unittest

from function_os.n1_functionspec_parser import N1FunctionSpecParser, FunctionSpecParseError
from function_os.n1_semantic_checker import N1SemanticChecker
from function_os.n1_safe_expression_dsl import SafeExpressionDSL

VALID = '{"function_id":"FN-20260715-0001","spec_version":"1.0.0","name":"add","domain":"symbolic","inputs":{"x":"integer","y":"integer"},"outputs":{"result":"integer"},"preconditions":[{"expression":"x >= 0","message":"x non-negative"}],"postconditions":[{"expression":"result == x + y","message":"r == sum"}],"effects_declared":["pure"],"created_at":"2026-07-15T12:00:00Z"}'


class TestN1ParserPositive(unittest.TestCase):
    def setUp(self):
        self.p = N1FunctionSpecParser()

    def test_parse_valid(self):
        spec = self.p.parse(VALID)
        self.assertEqual(spec['function_id'], 'FN-20260715-0001')
        self.assertIn('spec_hash', spec)

    def test_parse_computes_deterministic_hash(self):
        self.assertEqual(self.p.parse(VALID)['spec_hash'],
                         self.p.parse(VALID)['spec_hash'])

    def test_parse_full_featured(self):
        full = ('{"function_id":"FN-20260715-0009","spec_version":"2.3.4","name":"f",'
                '"domain":"symbolic","inputs":{"a":"integer"},"outputs":{"b":"integer"},'
                '"preconditions":[{"expression":"a > 0","message":"m1"}],'
                '"postconditions":[{"expression":"b == a","message":"m2"}],'
                '"effects_declared":["pure","deterministic"],"created_at":"2026-07-15T00:00:00Z"}')
        self.assertEqual(self.p.parse(full)['spec_version'], '2.3.4')


class TestN1ParserNegative(unittest.TestCase):
    def setUp(self):
        self.p = N1FunctionSpecParser()

    def test_missing_function_id(self):
        with self.assertRaises(FunctionSpecParseError):
            self.p.parse(VALID.replace('"function_id":"FN-20260715-0001",', ''))

    def test_bad_function_id_format(self):
        with self.assertRaises(FunctionSpecParseError):
            self.p.parse(VALID.replace('FN-20260715-0001', 'fn_1'))

    def test_zero_spec_version_rejected(self):
        with self.assertRaises(FunctionSpecParseError):
            self.p.parse(VALID.replace('"1.0.0"', '"0.0.0"'))

    def test_negative_like_version_rejected(self):
        with self.assertRaises(FunctionSpecParseError):
            self.p.parse(VALID.replace('"1.0.0"', '"1.0"'))

    def test_non_symbolic_domain_rejected(self):
        with self.assertRaises(FunctionSpecParseError):
            self.p.parse(VALID.replace('"domain":"symbolic"', '"domain":"neural_weight"'))

    def test_empty_effects_declared(self):
        with self.assertRaises(FunctionSpecParseError):
            self.p.parse(VALID.replace('["pure"]', '[]'))

    def test_malformed_json(self):
        with self.assertRaises(FunctionSpecParseError):
            self.p.parse('{not valid json')

    def test_missing_outputs(self):
        with self.assertRaises(FunctionSpecParseError):
            self.p.parse(VALID.replace('"outputs":{"result":"integer"},', ''))


class TestN1SemanticChecker(unittest.TestCase):
    def setUp(self):
        self.p = N1FunctionSpecParser()
        self.c = N1SemanticChecker()

    def _issues_text(self, spec):
        return ' '.join(str(i) for i in self.c.check(spec))

    def test_clean_spec_no_issues(self):
        self.assertEqual(self.c.check(self.p.parse(VALID)), [])

    def test_undefined_symbol_in_precondition(self):
        spec = self.p.parse(VALID.replace('x >= 0', 'zzz >= 0'))
        issues = self.c.check(spec)
        self.assertTrue(any('zzz' in str(i) for i in issues), f"issues={issues}")

    def test_undefined_symbol_in_postcondition(self):
        spec = self.p.parse(VALID.replace('result == x + y', 'result == x + q'))
        issues = self.c.check(spec)
        self.assertTrue(any('q' in str(i) for i in issues), f"issues={issues}")

    def test_input_output_symbol_consistency_ok(self):
        self.assertEqual(self.c.check(self.p.parse(VALID)), [])

    def test_checker_is_stateless(self):
        spec = self.p.parse(VALID)
        self.assertEqual(self.c.check(spec), [])
        self.assertEqual(self.c.check(spec), [])


class TestN1SafeDSL(unittest.TestCase):
    def setUp(self):
        self.dsl = SafeExpressionDSL()

    def test_symbolic_subset_allowed(self):
        self.dsl.evaluate("x + y * 2 - (z / 3)", {"x": 1, "y": 2, "z": 3})

    def test_comparison_allowed(self):
        self.assertTrue(self.dsl.evaluate("result == x + y",
                                          {"result": 5, "x": 2, "y": 3}))

    def test_banned_call_rejected(self):
        with self.assertRaises(ValueError):
            self.dsl.evaluate("__import__('os')", {})

    def test_banned_name_eval_rejected(self):
        with self.assertRaises(ValueError):
            self.dsl.evaluate("eval('1+1')", {})

    def test_banned_name_exec_rejected(self):
        with self.assertRaises(ValueError):
            self.dsl.evaluate("exec('pass')", {})

    def test_banned_name_open_rejected(self):
        with self.assertRaises(ValueError):
            self.dsl.evaluate("open('/etc/passwd')", {})

    def test_banned_attr_subprocess_rejected(self):
        with self.assertRaises(ValueError):
            self.dsl.evaluate("os.system('ls')", {})

    def test_undefined_symbol_rejected(self):
        with self.assertRaises(ValueError):
            self.dsl.evaluate("undefined_sym + 1", {})


if __name__ == '__main__':
    unittest.main()
