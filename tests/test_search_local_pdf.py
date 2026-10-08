import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/ste100/scripts/search_local_pdf.py'
spec = importlib.util.spec_from_file_location('search_local_pdf', SCRIPT)
lookup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lookup)


def synthetic_pdf(path):
    # Original test text, generated outside the repository. No standard excerpts.
    objects = [b'<< /Type /Catalog /Pages 2 0 R >>', b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>', b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 300] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>', b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>']
    stream = b'BT /F1 12 Tf 20 260 Td (The sample gate holds a blue sample. Sample readings are examples.) Tj ET'
    objects.append(b'<< /Length ' + str(len(stream)).encode() + b' >>\nstream\n' + stream + b'\nendstream')
    data = b'%PDF-1.4\n'; offsets = [0]
    for i, obj in enumerate(objects, 1):
        offsets.append(len(data)); data += str(i).encode() + b' 0 obj\n' + obj + b'\nendobj\n'
    start = len(data)
    data += b'xref\n0 6\n0000000000 65535 f \n' + b''.join(f'{x:010d} 00000 n \n'.encode() for x in offsets[1:])
    data += b'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n' + str(start).encode() + b'\n%%EOF\n'
    path.write_bytes(data)


class PdfTests(unittest.TestCase):
    def test_absent_source(self):
        with self.assertRaises(ValueError): lookup.search('/no-local-pdf', 'sample')

    def test_invalid_parameters(self):
        for term in ('', 'x' * 201):
            with self.assertRaises(ValueError): lookup.search('/no-local-pdf', term)

    def test_missing_dependency_message(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'sample.pdf'; synthetic_pdf(path)
            run = subprocess.run([sys.executable, '-S', str(SCRIPT), 'sample', '--pdf', str(path)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 2)
            self.assertIn('optional pypdf dependency is absent', run.stderr)

    @unittest.skipUnless(importlib.util.find_spec('pypdf'), 'The optional pypdf dependency is not installed.')
    def test_bounded_synthetic_lookup(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'sample.pdf'; synthetic_pdf(path)
            result = lookup.search(path, 'sample', max_hits=1, excerpt_chars=40)
            self.assertEqual(len(result['hits']), 1)
            self.assertEqual(result['hits'][0]['pdf_page'], 1)
            self.assertLessEqual(len(result['hits'][0]['excerpt']), 40)
            self.assertTrue(result['truncated'])
            self.assertEqual(lookup.search(path, 'not present')['hits'], [])
            with self.assertRaises(ValueError): lookup.search(path, 'sample', end=51)
            self.assertEqual(sorted(p.name for p in Path(d).iterdir()), ['sample.pdf'])


if __name__ == '__main__': unittest.main()
