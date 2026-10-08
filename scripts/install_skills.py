#!/usr/bin/env python3
"""Copy selected complete skills. Refuse an existing destination."""
import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOSTS = {'codex': '.agents', 'claude': '.claude', 'grok': '.grok'}
SKILLS = ('ste100', 'diagram-first')


def install(host, scope, project=None, skills=SKILLS):
    if host not in HOSTS or scope not in {'project', 'user'} or not skills or len(set(skills)) != len(skills) or any(s not in SKILLS for s in skills):
        raise ValueError('The host, scope, or skill is invalid.')
    if scope == 'project':
        if project is None or not Path(project).is_dir():
            raise ValueError('Project scope needs an existing --project directory.')
        base = Path(project).resolve()
    else:
        if project is not None:
            raise ValueError('User scope does not use --project.')
        base = Path.home()
    folder = base / HOSTS[host] / 'skills'
    destinations = [folder / s for s in skills]
    for dest in destinations:
        if dest.exists() or dest.is_symlink():
            raise ValueError(f'The destination already exists: {dest}. Review it before replacement.')
    for skill, dest in zip(skills, destinations):
        shutil.copytree(ROOT / 'skills' / skill, dest, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.DS_Store'))
    return destinations


def main():
    p = argparse.ArgumentParser(description='Copy portable skills without replacing existing installations.')
    p.add_argument('--host', required=True, choices=HOSTS)
    p.add_argument('--scope', choices=['project', 'user'], default='project')
    p.add_argument('--project')
    p.add_argument('--skill', action='append', choices=SKILLS)
    a = p.parse_args()
    try:
        for dest in install(a.host, a.scope, a.project, tuple(a.skill) if a.skill else SKILLS):
            print(f'Skill installed: {dest}')
        return 0
    except (ValueError, OSError) as exc:
        print(f'Installation error: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__': sys.exit(main())
