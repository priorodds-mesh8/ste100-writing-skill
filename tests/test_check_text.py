import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/ste100/scripts/check_text.py'
spec = importlib.util.spec_from_file_location('check_text', SCRIPT)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class CheckerTests(unittest.TestCase):
    def test_procedure_boundary(self):
        for count in (20, 21):
            result = checker.check(' '.join(['word'] * count) + '.', 'technical', 'procedure')
            self.assertEqual(result['exit_code'], int(count > 20))

    def test_description_boundary(self):
        for count in (25, 26):
            result = checker.check(' '.join(['word'] * count) + '.', 'technical')
            self.assertEqual(result['exit_code'], int(count > 25))

    def test_plain_guidance(self):
        self.assertEqual(checker.check(' '.join(['word'] * 26))['exit_code'], 0)
        self.assertEqual(checker.check(' '.join(['word'] * 26), fail_on_review=True)['exit_code'], 1)

    def test_atomic_tokens(self):
        for phrase in ('3.5 mm', '12 kg', '6 MHz', '15 °C', 'sample-gate', '"sample gate"', '(sample gate)', '`sample_gate.open()`', 'e.g.'):
            with self.subTest(phrase=phrase):
                self.assertEqual(checker.count_words(phrase), 1)

    def test_proper_name_and_terms(self):
        terms = [{'term': 'North Sample Lab', 'role': 'proper_name'}, {'term': 'sample gate', 'role': 'technical_noun'}]
        self.assertEqual(checker.count_words('North Sample Lab checks the sample gate.', terms), 5)
        result = checker.check('North Sample Lab ' + ' '.join(['word'] * 25), 'technical', terms=terms)
        self.assertEqual(result['exit_code'], 1)

    def test_abbreviations_and_decimals(self):
        result = list(checker.sentences('Dr. Lee reads 3.5 mm. The gauge is stable.'))
        self.assertEqual(len(result), 2)

    def test_links_and_fences(self):
        result = checker.check('# Title\n[Open the sample gate](https://example.invalid/test).\n\n```python\n' + 'word ' * 50 + '\n```', 'technical', 'procedure')
        self.assertEqual(result['findings'], [])

    def test_numbered_list(self):
        result = checker.check('1. Open the sample gate.\n2. Check 3.5 mm.', 'technical', 'procedure')
        self.assertEqual(result['findings'], [])

    def test_mixed_classification(self):
        with self.assertRaises(ValueError):
            checker.check('Open the gate.', text_type='mixed')
        result = checker.check('<!-- ste100:procedure -->\n' + 'word ' * 21 + '.\n<!-- ste100:description -->\n' + 'word ' * 21 + '.', 'technical', 'mixed')
        lengths = [f for f in result['findings'] if f['id'] == 'sentence-length']
        self.assertEqual(len(lengths), 1)
        self.assertEqual(lengths[0]['location']['line'], 2)

    def test_paragraph_boundary(self):
        self.assertEqual(checker.check('A works. ' * 6, 'technical')['exit_code'], 0)
        self.assertEqual(checker.check('A works. ' * 7, 'technical')['exit_code'], 1)

    def test_passive_is_review(self):
        result = checker.check('The latch is removed.', 'technical')
        self.assertEqual(result['exit_code'], 0)
        self.assertEqual(result['findings'][0]['id'], 'possible-passive')
        self.assertEqual(result['findings'][0]['severity'], 'review')

    def test_sequence_and_simultaneous(self):
        result = checker.check('Open the gate and then check the gauge.', 'technical', 'procedure')
        self.assertTrue(any(f['id'] == 'possible-sequential-actions' for f in result['findings']))
        self.assertEqual(checker.check('Hold the lever while you press the button.', 'technical', 'procedure')['findings'], [])

    def test_term_role_review(self):
        result = checker.check('You must sample gate the unit.', terms=[{'term': 'sample gate', 'role': 'technical_noun'}])
        self.assertTrue(any(f['id'] == 'possible-term-role' for f in result['findings']))

    def test_ambiguous_parse_is_visible(self):
        for source in ('The tag says "Close the gate."', 'Read (the outer (inner) label).', 'Read "the tag.', 'A. Smith checks it.', '```\ncode'):
            self.assertTrue(checker.check(source)['findings'], source)

    def test_empty_input(self):
        with self.assertRaises(ValueError): checker.check(' ')

    def test_layout_review(self):
        for source in ('<p>The gate is open.</p>', '| Item | Value |', '    Open the gate.'):
            self.assertTrue(checker.check(source)['findings'])

    def test_glossary_validation(self):
        valid = json.loads((ROOT / 'examples/terms.json').read_text())
        invalid = [[], {'schema_version': '1.0', 'terms': [None]}, {'schema_version': '1.0', 'terms': [{'term': 'gate'}]}]
        duplicate = json.loads(json.dumps(valid)); duplicate['terms'].append(duplicate['terms'][0]); invalid.append(duplicate)
        wrong = json.loads(json.dumps(valid)); wrong['terms'][0]['forms'] = 'gates'; invalid.append(wrong)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'terms.json'
            p.write_text(json.dumps(valid)); self.assertEqual(len(checker.load_terms(p)), 3)
            for data in invalid:
                p.write_text(json.dumps(data))
                with self.assertRaises(ValueError): checker.load_terms(p)

    def test_cli_stdin_and_exit_codes(self):
        for source, extra, expected in [('Open the gate.', [], 0), ('word ' * 26, ['--mode', 'technical'], 1), ('', [], 2), ('The gate is removed.', ['--fail-on-review'], 1)]:
            run = subprocess.run([sys.executable, str(SCRIPT), '-', '--format', 'json', *extra], input=source, capture_output=True, text=True)
            self.assertEqual(run.returncode, expected, run.stderr)
            self.assertEqual(json.loads(run.stdout)['exit_code'], expected)

    def test_missing_file(self):
        run = subprocess.run([sys.executable, str(SCRIPT), '/file-that-does-not-exist', '--format', 'json'], capture_output=True, text=True)
        self.assertEqual(run.returncode, 2)
        self.assertIn('error', json.loads(run.stdout))


if __name__ == '__main__': unittest.main()
