#!/usr/bin/env python3
"""Build an archive from the Git index after bounded release checks."""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_NAMES = {'dictionary.jsonl', 'part1_rules.md', 'ingest_preamble.md', 'qa.md', 'ASD-STE100_ISSUE9.pdf'}


def inspect_file(name, data):
    p = Path(name)
    if p.is_absolute() or '..' in p.parts or p.suffix.lower() == '.pdf' or p.name in PRIVATE_NAMES or p.name == '.env' or p.name.startswith('.env.') or any(x in p.parts for x in ('raw', 'private', 'local-references', '__pycache__', 'node_modules', 'validation-output', '.git')) or p.suffix in {'.pyc', '.env'}:
        raise ValueError(f'The release excludes this path: {name}')
    if p.suffix not in {'.ttf', '.png'}:
        content = data.decode('utf-8')
        if re.search(r'/(?:Users|home)/[A-Za-z0-9_.-]+/', content) or re.search(r'(?:AKIA|ASIA)[A-Z0-9]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----', content):
            raise ValueError(f'The file needs review for private content: {name}')


def build(output):
    names = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    names = sorted(n for n in names if n)
    if not names or 'README.md' not in names or 'LICENSE' not in names:
        raise ValueError('Stage the complete source package before the release build.')
    if subprocess.run(['git', 'diff', '--quiet'], cwd=ROOT).returncode:
        raise ValueError('Stage the final edits before the release build.')
    files = {}
    for name in names:
        mode = subprocess.check_output(['git', 'ls-files', '-s', '--', name], cwd=ROOT).decode().split()[0]
        if mode not in {'100644', '100755'}:
            raise ValueError('The release must contain ordinary files, not symlinks or submodules.')
        data = (ROOT / name).read_bytes()
        inspect_file(name, data)
        files[name] = data
    output = Path(output).resolve()
    if output.is_relative_to(ROOT):
        raise ValueError('Put the release archive outside the source repository.')
    if output.exists() or output.with_suffix('.manifest.json').exists():
        raise ValueError('Choose a new output path. An archive or manifest already exists.')
    records = {name: {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()} for name, data in files.items()}
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            info = zipfile.ZipInfo('ste100-writing-skill/' + name, date_time=(2026, 10, 7, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None or len(archive.namelist()) != len(files):
            raise ValueError('The release archive check fails.')
        for name, data in files.items():
            extracted = archive.read('ste100-writing-skill/' + name)
            inspect_file(name, extracted)
            if extracted != data:
                raise ValueError('An archived file differs from the source.')
    manifest = dict(schema_version='1.0', archive=output.name, archive_sha256=hashlib.sha256(output.read_bytes()).hexdigest(), files=records)
    manifest_path = output.with_suffix('.manifest.json')
    with manifest_path.open('x', encoding='utf-8') as handle:
        json.dump(manifest, handle, indent=2); handle.write('\n')
    return dict(archive=str(output), files=len(files), bytes=output.stat().st_size, sha256=manifest['archive_sha256'])


def main():
    p = argparse.ArgumentParser(description='Build an inspected archive from staged source files.')
    p.add_argument('--output', required=True)
    a = p.parse_args()
    try:
        print(json.dumps(build(a.output), indent=2)); return 0
    except (OSError, ValueError, UnicodeError, subprocess.SubprocessError) as exc:
        print(f'Release build error: {exc}', file=sys.stderr); return 2


if __name__ == '__main__': sys.exit(main())
