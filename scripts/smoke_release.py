#!/usr/bin/env python3
"""Check a public release archive on a new machine."""
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath


SKILLS = ('ste100', 'diagram-first')
HOSTS = {'codex': '.agents', 'claude': '.claude', 'grok': '.grok'}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def archive_members(archive):
    names = [name for name in archive.namelist() if not name.endswith('/')]
    if not names:
        raise ValueError('The archive has no files.')
    roots = set()
    members = {}
    for name in names:
        path = PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or len(path.parts) < 2:
            raise ValueError(f'The archive has an unsafe path: {name}')
        roots.add(path.parts[0])
        members[str(PurePosixPath(*path.parts[1:]))] = name
    if len(roots) != 1 or len(members) != len(names):
        raise ValueError('The archive must have one root folder and unique file paths.')
    return next(iter(roots)), members


def verify_archive(archive_path, manifest_path):
    manifest = json.loads(Path(manifest_path).read_text(encoding='utf-8'))
    expected_archive_hash = manifest.get('archive_sha256')
    archive_hash = sha256(archive_path)
    if archive_hash != expected_archive_hash:
        raise ValueError('The archive SHA-256 does not match the manifest.')
    expected_files = manifest.get('files')
    if not isinstance(expected_files, dict) or not expected_files:
        raise ValueError('The manifest has no file records.')
    with zipfile.ZipFile(archive_path) as archive:
        bad_member = archive.testzip()
        if bad_member:
            raise ValueError(f'The archive has a damaged member: {bad_member}')
        root, members = archive_members(archive)
        if set(members) != set(expected_files):
            raise ValueError('The archive files do not match the manifest.')
        for relative, record in expected_files.items():
            data = archive.read(members[relative])
            if len(data) != record.get('bytes') or hashlib.sha256(data).hexdigest() != record.get('sha256'):
                raise ValueError(f'The manifest check fails for: {relative}')
    return root, len(members), archive_hash


def run(command, cwd):
    subprocess.run(command, cwd=cwd, check=True)


def smoke(source, workspace):
    run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'], source)
    run([sys.executable, 'evals/run_evals.py'], source)
    outputs = []
    for host, folder in HOSTS.items():
        project = workspace / f'{host}-project'
        project.mkdir()
        run([sys.executable, 'scripts/install_skills.py', '--host', host, '--scope', 'project', '--project', str(project)], source)
        for skill in SKILLS:
            expected = project / folder / 'skills' / skill / 'SKILL.md'
            if not expected.is_file():
                raise ValueError(f'The {host} installation lacks {skill}.')
        diagram = project / folder / 'skills' / 'diagram-first'
        output = project / 'diagram.html'
        run([sys.executable, str(diagram / 'scripts/render_diagram.py'), str(diagram / 'assets/workflow-example.json'), '--output', str(output)], source)
        if not output.is_file() or b'Clear writing workflow' not in output.read_bytes():
            raise ValueError(f'The {host} diagram render fails.')
        outputs.append(output.read_bytes())
    if any(output != outputs[0] for output in outputs[1:]):
        raise ValueError('The host installations do not render the same diagram.')


def download(url, output):
    with urllib.request.urlopen(url) as response, Path(output).open('wb') as handle:
        while block := response.read(1024 * 1024):
            handle.write(block)


def release_asset_urls(url):
    with urllib.request.urlopen(url) as response:
        release = json.loads(response.read().decode('utf-8'))
    assets = release.get('assets', [])
    archives = [asset.get('browser_download_url') for asset in assets if asset.get('name', '').endswith('.zip')]
    manifests = [asset.get('browser_download_url') for asset in assets if asset.get('name', '').endswith('.manifest.json')]
    if len(archives) != 1 or len(manifests) != 1:
        raise ValueError('The release must have one ZIP archive and one manifest.')
    return archives[0], manifests[0]


def main():
    parser = argparse.ArgumentParser(description='Download, verify, install, and test a public release.')
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--release-api-url')
    source.add_argument('--archive-url')
    parser.add_argument('--manifest-url')
    args = parser.parse_args()
    try:
        if args.release_api_url:
            archive_url, manifest_url = release_asset_urls(args.release_api_url)
        elif args.manifest_url:
            archive_url, manifest_url = args.archive_url, args.manifest_url
        else:
            raise ValueError('Use --manifest-url with --archive-url.')
        with tempfile.TemporaryDirectory(prefix='ste100-release-smoke-') as temporary:
            workspace = Path(temporary)
            archive = workspace / 'release.zip'
            manifest = workspace / 'release.manifest.json'
            download(archive_url, archive)
            download(manifest_url, manifest)
            root, count, digest = verify_archive(archive, manifest)
            with zipfile.ZipFile(archive) as package:
                package.extractall(workspace / 'source')
            source = workspace / 'source' / root
            smoke(source, workspace)
        print(json.dumps({'archive_sha256': digest, 'files': count, 'hosts': list(HOSTS)}, indent=2))
        return 0
    except (OSError, ValueError, json.JSONDecodeError, subprocess.CalledProcessError, urllib.error.URLError, zipfile.BadZipFile) as error:
        print(f'Release smoke error: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
