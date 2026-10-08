import importlib.util
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('install_skills', ROOT / 'scripts/install_skills.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallTests(unittest.TestCase):
    def test_project_clean_copies_for_each_host(self):
        with tempfile.TemporaryDirectory() as d:
            for host in installer.HOSTS:
                with self.subTest(host=host):
                    project = Path(d) / host; project.mkdir()
                    paths = installer.install(host, 'project', project)
                    self.assertEqual(paths[0], project.resolve() / installer.HOSTS[host] / 'skills/ste100')
                    for skill in paths:
                        self.assertTrue((skill / 'LICENSE').is_file())
                    check = subprocess.run([sys.executable, str(paths[0] / 'scripts/check_text.py'), '-', '--mode', 'technical'], input='Open the sample gate.', capture_output=True, text=True)
                    self.assertEqual(check.returncode, 0, check.stderr)
                    render = subprocess.run([sys.executable, str(paths[1] / 'scripts/render_diagram.py'), str(paths[1] / 'assets/workflow-example.json'), '--output', str(project / 'sheet.html')], capture_output=True, text=True)
                    self.assertEqual(render.returncode, 0, render.stderr)

    def test_refuses_existing_or_broken_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d); target = base / '.agents/skills/ste100'; target.parent.mkdir(parents=True)
            target.symlink_to(base / 'missing')
            with self.assertRaises(ValueError): installer.install('codex', 'project', base)
            self.assertFalse((target.parent / 'diagram-first').exists())

    def test_personal_scope_without_real_home_change(self):
        with tempfile.TemporaryDirectory() as d, patch.object(Path, 'home', return_value=Path(d)):
            paths = installer.install('claude', 'user', skills=('ste100',))
            self.assertEqual(paths[0], Path(d) / '.claude/skills/ste100')

    def test_relative_skill_links(self):
        for skill in installer.SKILLS:
            for md in (ROOT / 'skills' / skill).rglob('*.md'):
                for link in re.findall(r'\]\(([^)]+)\)', md.read_text()):
                    if '://' not in link and not link.startswith('#'):
                        self.assertTrue((md.parent / link.split('#')[0]).exists(), f'{md.name}: {link}')


if __name__ == '__main__': unittest.main()
