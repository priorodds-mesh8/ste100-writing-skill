import hashlib
import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('smoke_release', ROOT / 'scripts/smoke_release.py')
smoke_release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke_release)


class ReleaseSmokeTests(unittest.TestCase):
    def build_archive(self, directory, members):
        archive = Path(directory) / 'release.zip'
        records = {}
        with zipfile.ZipFile(archive, 'w') as package:
            for name, data in members.items():
                package.writestr('skill/' + name, data)
                records[name] = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
        manifest = Path(directory) / 'release.manifest.json'
        manifest.write_text(json.dumps({'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'files': records}), encoding='utf-8')
        return archive, manifest

    def test_verify_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            archive, manifest = self.build_archive(directory, {'README.md': b'ok', 'skills/ste100/SKILL.md': b'skill'})
            root, count, digest = smoke_release.verify_archive(archive, manifest)
            self.assertEqual(root, 'skill')
            self.assertEqual(count, 2)
            self.assertEqual(digest, hashlib.sha256(archive.read_bytes()).hexdigest())

    def test_verify_archive_rejects_missing_manifest_record(self):
        with tempfile.TemporaryDirectory() as directory:
            archive, manifest = self.build_archive(directory, {'README.md': b'ok'})
            data = json.loads(manifest.read_text(encoding='utf-8'))
            data['files']['extra.md'] = {'bytes': 1, 'sha256': hashlib.sha256(b'x').hexdigest()}
            manifest.write_text(json.dumps(data), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'do not match'):
                smoke_release.verify_archive(archive, manifest)


if __name__ == '__main__':
    unittest.main()
