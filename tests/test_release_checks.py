import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('build_release', ROOT / 'scripts/build_release.py')
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class ReleaseTests(unittest.TestCase):
    def test_private_files_rejected(self):
        for name in ('dictionary.jsonl', 'part1_rules.md', 'reference.pdf', 'private/context.md', 'node_modules/file.js', '__pycache__/file.pyc'):
            with self.subTest(name=name), self.assertRaises(ValueError): release.inspect_file(name, b'example')

    def test_personal_paths_and_keys_rejected(self):
        # Build strings so the test data does not itself contain a private path or key.
        for content in ('/' + 'Users' + '/example/local.md', '-----BEGIN ' + 'PRIVATE KEY-----'):
            with self.assertRaises(ValueError): release.inspect_file('example.md', content.encode())

    def test_portable_original_text_allowed(self):
        release.inspect_file('skills/ste100/SKILL.md', b'Original project guidance.')


if __name__ == '__main__': unittest.main()
