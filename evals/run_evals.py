#!/usr/bin/env python3
"""Validate evaluation records. Semantic judgments need a named reviewer."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def validate():
    all_cases = {}
    for name in ('cases.json', 'triggers.json', 'diagram-cases.json'):
        data = json.loads((ROOT / 'evals' / name).read_text(encoding='utf-8'))
        if data.get('schema_version') != '1.0' or not isinstance(data.get('cases'), list):
            raise ValueError(f'The case file is invalid: {name}')
        for case in data['cases']:
            if not isinstance(case.get('id'), str) or case['id'] in all_cases or not case.get('assessment_method'):
                raise ValueError('Each case needs a unique ID and an assessment method.')
            if name == 'triggers.json':
                if not isinstance(case.get('expected_selection'), bool) or case.get('invocation') not in {'explicit', 'automatic'} or not case.get('prompt'):
                    raise ValueError('The trigger case is invalid.')
            elif not isinstance(case.get('invariants'), list) or not case['invariants'] or not all(isinstance(x, str) and x for x in case['invariants']):
                raise ValueError('The case needs nonempty invariant strings.')
            if name == 'cases.json' and (case.get('mode') not in {'plain', 'technical', 'reference-review'} or not case.get('prompt')):
                raise ValueError('The writing case is invalid.')
            if name == 'diagram-cases.json' and not (ROOT / case.get('input', '')).is_file():
                raise ValueError('The diagram fixture is absent.')
            all_cases[case['id']] = case
    return all_cases


def assess(records, cases):
    if not isinstance(records, list):
        raise ValueError('The outputs file must contain an array.')
    results = []
    seen = set()
    for record in records:
        key = (record['case_id'], record['variant'])
        if key in seen or key[0] not in cases or key[1] not in {'baseline', 'skill'}:
            raise ValueError('Output records need a unique known case and baseline or skill variant.')
        seen.add(key)
        context = record['context']
        for field in ('host', 'host_version', 'model', 'mode', 'source_access'):
            if not isinstance(context.get(field), str) or not context[field]:
                raise ValueError(f'The output context needs {field}.')
        if not isinstance(record.get('output'), str):
            raise ValueError('Each record needs output text.')
        review = record.get('assessment')
        if not review:
            results.append({'case_id': key[0], 'variant': key[1], 'status': 'needs-human-review'})
            continue
        if not isinstance(review.get('reviewer'), str) or not review['reviewer'].strip() or not isinstance(review.get('notes'), str):
            raise ValueError('An assessment needs a named reviewer and notes.')
        checks = review.get('checks')
        expected = len(cases[key[0]].get('invariants', [cases[key[0]]['assessment_method']]))
        if not isinstance(checks, list) or len(checks) != expected or not all(isinstance(x, bool) for x in checks):
            raise ValueError('The reviewer must assess each invariant with a boolean.')
        results.append({'case_id': key[0], 'variant': key[1], 'status': 'reviewer-pass' if all(checks) else 'reviewer-fail', 'reviewer': review['reviewer']})
    return results


def main():
    p = argparse.ArgumentParser(description='Validate cases and supplied review records. This makes no model calls.')
    p.add_argument('--outputs')
    a = p.parse_args()
    try:
        cases = validate()
        results = assess(json.loads(Path(a.outputs).read_text(encoding='utf-8')), cases) if a.outputs else []
        report = dict(schema_version='1.0', validated_cases=len(cases), assessed_outputs=results,
                      live_model_status='not run by this script',
                      judgment='Semantic checks require human review. Keywords cannot establish preserved meaning.')
        print(json.dumps(report, indent=2))
        return 1 if any(r['status'] != 'reviewer-pass' for r in results) else 0
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as exc:
        print(f'Evaluation input error: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__': sys.exit(main())
