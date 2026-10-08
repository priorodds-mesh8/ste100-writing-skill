#!/usr/bin/env python3
"""Bounded prose checks. Python 3.11+. No standard-compliance claim."""
import argparse
import json
import re
import sys
from pathlib import Path

METHOD = 'ste100-project-count-v1'
ROLES = {'technical_noun', 'technical_verb', 'proper_name'}
ABBREVIATIONS = re.compile(r'\b(?:e\.g\.|i\.e\.|etc\.|Dr\.|Mr\.|Ms\.|Mrs\.|Prof\.|Fig\.|No\.|vs\.|U\.S\.|U\.K\.)', re.I)
TOKEN = re.compile(r'\d+(?:[.,]\d+)*(?:\s*(?:mm|cm|km|m|kg|g|ms|s|Hz|kHz|MHz|V|kV|A|mA|W|kW|Pa|kPa|MPa|°C|°F|%))\b|[\w]+(?:[’\'\-][\w]+)*(?:[.,]\d+)*', re.UNICODE)


def load_terms(path):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(data, dict) or data.get('schema_version') != '1.0' or not isinstance(data.get('terms'), list):
        raise ValueError('The glossary needs schema_version 1.0 and a terms array.')
    seen = set()
    for entry in data['terms']:
        if not isinstance(entry, dict):
            raise ValueError('Each term must be an object.')
        for key in ('term', 'meaning', 'domain'):
            if not isinstance(entry.get(key), str) or not entry[key].strip():
                raise ValueError(f'Each term needs a nonempty {key}.')
        if entry.get('role') not in ROLES:
            raise ValueError('The term role is invalid.')
        if entry['term'].casefold() in seen:
            raise ValueError('The glossary has a duplicate term.')
        seen.add(entry['term'].casefold())
        for key in ('forms', 'restrictions'):
            if key in entry and (not isinstance(entry[key], list) or not all(isinstance(x, str) and x.strip() for x in entry[key])):
                raise ValueError(f'{key} must be an array of nonempty strings.')
    return data['terms']


def count_words(sentence, terms=()):
    # Labels, parenthetical groups, and inline identifiers are atomic units.
    s = sentence
    for entry in terms:
        if entry['role'] == 'proper_name':
            for name in sorted([entry['term'], *entry.get('forms', [])], key=len, reverse=True):
                s = re.sub(r'(?<!\w)' + re.escape(name) + r'(?!\w)', ' ATOM ', s)
    s = re.sub(r'`[^`\n]+`|"[^"\n]+"|“[^”\n]+”|\([^()]*\)', ' ATOM ', s)
    s = ABBREVIATIONS.sub(' ATOM ', s)
    return len(TOKEN.findall(s))


def sentences(text):
    # Protect opaque labels and common abbreviations before boundary detection.
    protected = list(text)
    pattern = re.compile(r'`[^`\n]+`|"[^"\n]+"|“[^”\n]+”|\([^()]*\)')
    for match in [*pattern.finditer(text), *ABBREVIATIONS.finditer(text)]:
        for i in range(match.start(), match.end()):
            if protected[i] in '.!?':
                protected[i] = '\ue000'
    for match in re.finditer(r'(?<=\d)\.(?=\d)', text):
        protected[match.start()] = '\ue000'
    working = ''.join(protected)
    start = 0
    for match in re.finditer(r'[.!?]+(?=\s|$)', working):
        end = match.end()
        raw = text[start:end]
        if raw.strip():
            leading = len(raw) - len(raw.lstrip())
            yield start + leading, raw.strip()
        start = end
    if text[start:].strip():
        raw = text[start:]
        yield start + len(raw) - len(raw.lstrip()), raw.strip()


def check(text, mode='plain', text_type='description', terms=(), fail_on_review=False):
    if mode not in {'plain', 'technical'} or text_type not in {'procedure', 'description', 'mixed'}:
        raise ValueError('The mode or text type is invalid.')
    if not isinstance(text, str) or not text.strip():
        raise ValueError('The input has no text.')
    findings = []
    def add(code, severity, line, column, reason, basis):
        findings.append(dict(id=code, severity=severity, location=dict(line=line, column=column), reason=reason, basis=basis))
    active = None if text_type == 'mixed' else text_type
    fence = None
    block = []
    paragraph_sentences = 0
    paragraph_start = 1

    def flush():
        nonlocal paragraph_sentences, block
        if not block:
            return
        joined = ' '.join(line for _, line in block)
        offsets = []
        cursor = 0
        for line_num, value in block:
            offsets.append((cursor, line_num))
            cursor += len(value) + 1
        for pos, sentence in sentences(joined):
            origin, line = max((x for x in offsets if x[0] <= pos), default=offsets[0])
            col = pos - origin + 1
            paragraph_sentences += 1
            budget = 20 if active == 'procedure' else 25
            count = count_words(sentence, terms)
            if count > budget:
                add('sentence-length', 'error' if mode == 'technical' else 'review', line, col,
                    f'The sentence has {count} words. The {active} budget is {budget}.', METHOD)
            if re.search(r'\b(?:is|are|was|were|be|been)\s+(?:\w+ly\s+)?(?:\w+ed|shown|known|made|given|written|taken|held|built|found|sent|set|done|kept)\b', sentence, re.I):
                add('possible-passive', 'review', line, col, 'Check the actor and voice. Do not invent an actor.', 'grammar heuristic')
            if active == 'procedure' and re.search(r';|\bthen\b|\band\s+(?:open|close|remove|install|turn|press|start|stop|check|run|send)\b', sentence, re.I):
                if not re.search(r'\b(?:while|simultaneously|at the same time)\b', sentence, re.I):
                    add('possible-sequential-actions', 'review', line, col, 'Check whether this sentence has separate sequential actions.', 'instruction heuristic')
            if re.search(r'\b(?:e\.g\.|i\.e\.|etc\.)', sentence, re.I):
                add('latin-abbreviation', 'review', line, col, 'Consider a full phrase if it preserves the meaning.', 'literal pattern')
            if re.search(r'\([^()]*\([^)]*\)|"[^"\n]*[.!?][^"\n]*"|“[^”\n]*[.!?][^”\n]*”', sentence):
                add('ambiguous-group', 'review', line, col, 'Check the grouped text and sentence boundaries manually.', 'parsing limit')
            if sentence.count('(') != sentence.count(')') or sentence.count('"') % 2 or sentence.count('“') != sentence.count('”') or sentence.count('`') % 2:
                add('unmatched-delimiter', 'review', line, col, 'Check the unmatched quote, identifier, or parenthesis.', 'parsing limit')
            if re.search(r'\b[A-Z]\.(?:[A-Z]\.)*', ABBREVIATIONS.sub('', sentence)):
                add('uncommon-dotted-form', 'review', line, col, 'Check sentence boundaries near the dotted form.', 'parsing limit')
            for entry in terms:
                if entry['role'] == 'technical_noun' and re.search(r'\b(?:to|must|shall)\s+' + re.escape(entry['term']) + r'\b', sentence, re.I):
                    add('possible-term-role', 'review', line, col, f"Check the grammatical role of {entry['term']}.", 'term-role heuristic')
        if active == 'description' and paragraph_sentences > 6:
            add('paragraph-length', 'error' if mode == 'technical' else 'review', paragraph_start, 1,
                f'The paragraph has {paragraph_sentences} sentences. The budget is 6.', 'configured paragraph budget')
        block = []
        paragraph_sentences = 0

    for line_num, raw in enumerate(text.splitlines(), 1):
        marker = re.fullmatch(r'\s*<!--\s*ste100:(procedure|description)\s*-->\s*', raw)
        if fence:
            if re.match(r'^\s{0,3}' + re.escape(fence[0]) + '{' + str(fence[1]) + r',}\s*$', raw):
                fence = None
            continue
        opening = re.match(r'^\s{0,3}(`{3,}|~{3,})', raw)
        if opening:
            flush()
            fence = (opening[1][0], len(opening[1]))
            continue
        if marker:
            flush()
            active = marker[1] if text_type == 'mixed' else text_type
            continue
        if not raw.strip():
            flush()
            continue
        if re.match(r'^\s{0,3}(?:#{1,6}\s|[-*_]{3,}\s*$)', raw):
            flush()
            continue
        if raw.startswith('    ') or '\t' == raw[:1]:
            add('indented-block', 'review', line_num, 1, 'Check whether the indented block is prose or code. Prose is counted.', 'parsing limit')
        if re.search(r'<[^>]+>|\|.*\|', raw):
            add('unsupported-layout', 'review', line_num, 1, 'Check HTML or table structure manually. Visible text is counted per row.', 'parsing limit')
        cleaned = re.sub(r'!?\[([^\]]+)\]\([^)]*\)', r'\1', raw)
        cleaned = re.sub(r'https?://\S+|<[^>]+>', '', cleaned)
        cleaned = re.sub(r'^\s*(?:>\s*|(?:[-+*]|\d+[.)])\s+)', '', cleaned)
        cleaned = re.sub(r'(?<!\w)[*_]+|[*_]+(?!\w)', '', cleaned)
        if not cleaned.strip():
            continue
        if active is None:
            raise ValueError(f'Mixed input has unclassified prose at line {line_num}.')
        if re.match(r'^\s*(?:[-+*]|\d+[.)])\s+', raw) or '|' in raw:
            flush()
        if not block:
            paragraph_start = line_num
        block.append((line_num, cleaned))
        if '|' in raw:
            flush()
    flush()
    if fence:
        add('unclosed-fence', 'review', len(text.splitlines()), 1, 'The code fence has no closing marker. Check excluded text.', 'parsing limit')
    failure = any(f['severity'] == 'error' or fail_on_review for f in findings)
    return dict(schema_version='1.0', mode=mode, text_type=text_type, count_method=METHOD, findings=findings,
                coverage=dict(completed=['sentence budget', 'description paragraph budget', 'glossary schema', 'mixed block classification'],
                              heuristic=['sentence segmentation', 'possible passive voice', 'possible sequential actions', 'possible term role'],
                              unavailable=['ASD vocabulary approval', 'full grammar analysis', 'meaning preservation', 'full STE compliance']),
                exit_code=1 if failure else 0)


def main():
    parser = argparse.ArgumentParser(description='Check prose under the project count method. This does not certify STE compliance.')
    parser.add_argument('file', nargs='?', default='-')
    parser.add_argument('--mode', choices=['plain', 'technical'], default='plain')
    parser.add_argument('--text-type', choices=['procedure', 'description', 'mixed'], default='description')
    parser.add_argument('--terms')
    parser.add_argument('--format', choices=['text', 'json'], default='text')
    parser.add_argument('--fail-on-review', action='store_true')
    args = parser.parse_args()
    try:
        if args.file == '-' and hasattr(sys.stdin, 'reconfigure'):
            sys.stdin.reconfigure(encoding='utf-8')
        text = sys.stdin.read() if args.file == '-' else Path(args.file).read_text(encoding='utf-8')
        result = check(text, args.mode, args.text_type, load_terms(args.terms) if args.terms else [], args.fail_on_review)
    except (OSError, ValueError, UnicodeError) as exc:
        if args.format == 'json':
            print(json.dumps(dict(schema_version='1.0', error=str(exc), exit_code=2)))
        else:
            print(f'Input error: {exc}', file=sys.stderr)
        return 2
    if args.format == 'json':
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for finding in result['findings']:
            loc = finding['location']
            print(f"{loc['line']}:{loc['column']} {finding['severity']} [{finding['id']}] {finding['reason']}")
        print(f"Count method: {METHOD}. Exit {result['exit_code']} covers selected checks only.")
    return result['exit_code']


if __name__ == '__main__':
    sys.exit(main())
