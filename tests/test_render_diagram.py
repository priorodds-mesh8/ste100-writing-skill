import copy
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/diagram-first/scripts/render_diagram.py'
spec = importlib.util.spec_from_file_location('render_diagram', SCRIPT)
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)


class DiagramTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / 'examples/diagram-reference.json').read_text())

    def test_original_and_new_facts(self):
        original = renderer.render(self.data)
        new = renderer.render(json.loads((ROOT / 'examples/diagram-workflow.json').read_text()))
        self.assertIn(self.data['title'], original)
        self.assertNotEqual(original, new)
        self.assertEqual(original.count('class="badge"'), 7)
        self.assertIn('How does a draft become a checked document?', new)

    def test_source_hash_and_styles(self):
        assets = renderer.ASSETS
        reference = (assets / 'ste100-wiring-sheet.reference.html').read_bytes()
        manifest = json.loads((assets / 'reference-manifest.json').read_text())
        self.assertEqual(hashlib.sha256(reference).hexdigest(), manifest['files']['ste100-wiring-sheet.html']['sha256'])
        css = re.findall(r'<style>(.*?)</style>', reference.decode(), re.S)[1]
        self.assertEqual(hashlib.sha256(css.encode()).hexdigest(), manifest['source_stylesheet_sha256'])
        self.assertIn(css, renderer.render(self.data))

    def test_embedded_fonts_and_license(self):
        output = renderer.render(self.data)
        self.assertNotIn('https://fonts.', output)
        self.assertEqual(output.count('data:font/ttf;base64,'), 6)
        self.assertIn('SIL OPEN FONT LICENSE', output)
        self.assertNotIn('<script', output)

    def test_escape_input(self):
        self.data['title'] = '<script>alert("x")</script>'
        self.data['panels'][0]['components'][1]['text'] = '<img onerror="bad()">'
        output = renderer.render(self.data)
        self.assertIn('&lt;script&gt;', output)
        self.assertNotIn('<script', output)
        self.assertNotIn('<img', output)

    def test_invalid_panel_ids(self):
        self.data['panels'][1]['id'] = 'A'
        with self.assertRaises(ValueError): renderer.render(self.data)

    def test_duplicate_element_ids(self):
        flow = self.data['panels'][1]['components'][0]
        flow['nodes'][1]['id'] = flow['nodes'][0]['id']
        with self.assertRaises(ValueError): renderer.render(self.data)

    def test_missing_endpoint(self):
        self.data['panels'][1]['components'][0]['edges'][0]['to'] = 'missing'
        with self.assertRaises(ValueError): renderer.render(self.data)

    def test_path_injection(self):
        self.data['panels'][1]['components'][0]['edges'][0]['path'] = 'M0,0" onload="bad()'
        with self.assertRaises(ValueError): renderer.render(self.data)

    def test_numeric_limits(self):
        for value in (-1, float('nan'), float('inf'), True, 31):
            data = copy.deepcopy(self.data)
            data['panels'][4]['components'][0]['items'][0]['value'] = value
            with self.assertRaises(ValueError): renderer.render(data)

    def test_invalid_scales_and_ticks(self):
        for ticks in ([0, 30, 10], [0, 10, 10, 30], [0, 31]):
            self.data['panels'][4]['components'][0]['items'][0]['ticks'] = ticks
            with self.assertRaises(ValueError): renderer.render(self.data)

    def test_required_metadata(self):
        for key in ('title', 'source', 'scope', 'date'):
            data = copy.deepcopy(self.data); del data['metadata'][key]
            with self.assertRaises(ValueError): renderer.render(data)

    def test_invalid_date(self):
        self.data['metadata']['date'] = '2026-02-30'
        with self.assertRaises(ValueError): renderer.render(self.data)

    def test_status_marks(self):
        self.data['panels'][2]['components'][0]['rows'][0][-1] = {'state': 'ok', 'text': 'Ready'}
        self.assertIn('✓ Ready', renderer.render(self.data))

    def test_cli_and_clean_install(self):
        import shutil
        with tempfile.TemporaryDirectory() as d:
            skill = Path(d) / 'diagram-first'
            shutil.copytree(ROOT / 'skills/diagram-first', skill, ignore=shutil.ignore_patterns('__pycache__'))
            output = Path(d) / 'diagram.html'
            run = subprocess.run([sys.executable, str(skill / 'scripts/render_diagram.py'), str(skill / 'assets/workflow-example.json'), '--output', str(output)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertTrue(output.is_file())


if __name__ == '__main__': unittest.main()
