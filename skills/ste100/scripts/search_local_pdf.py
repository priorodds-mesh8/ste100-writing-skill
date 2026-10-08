#!/usr/bin/env python3
"""Offline bounded lookup. No document cache or network access."""
import argparse
import json
import os
import sys
from pathlib import Path


def search(path, term, start=1, end=None, max_hits=5, excerpt_chars=240):
    if not term.strip() or len(term) > 200:
        raise ValueError('Use a literal search term with 1 to 200 characters.')
    if start < 1 or max_hits < 1 or max_hits > 20 or not 40 <= excerpt_chars <= 500 or excerpt_chars < len(term):
        raise ValueError('Use start >= 1, 1 to 20 hits, and 40 to 500 excerpt characters.')
    if not path or not Path(path).is_file():
        raise ValueError('The local PDF file is absent. Set ASD_STE100_PDF or --pdf.')
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ValueError('The optional pypdf dependency is absent. Install requirements-pdf.txt.') from exc
    reader = PdfReader(path)
    if reader.is_encrypted:
        raise ValueError('Encrypted PDFs are not supported by this helper.')
    last = min(start + 49, len(reader.pages)) if end is None else end
    if not start <= last <= len(reader.pages) or last - start + 1 > 50:
        raise ValueError('Use a valid range of at most 50 physical PDF pages.')
    hits = []
    for index in range(start - 1, last):
        text = reader.pages[index].extract_text() or ''
        # Lowercasing per character keeps source offsets stable for Unicode.
        import re
        for match in re.finditer(re.escape(term), text, re.I):
            left = max(0, match.start() - (excerpt_chars - len(term)) // 2)
            hits.append(dict(pdf_page=index + 1, excerpt=text[left:left + excerpt_chars]))
            if len(hits) == max_hits:
                return dict(schema_version='1.0', hits=hits, truncated=True, page_range=[start, last])
    return dict(schema_version='1.0', hits=hits, truncated=False, page_range=[start, last])


def main():
    p = argparse.ArgumentParser(description='Search a local PDF. A hit does not prove an approved meaning.')
    p.add_argument('term')
    p.add_argument('--pdf', default=os.environ.get('ASD_STE100_PDF'))
    p.add_argument('--start-page', type=int, default=1)
    p.add_argument('--end-page', type=int)
    p.add_argument('--max-hits', type=int, default=5)
    p.add_argument('--excerpt-chars', type=int, default=240)
    a = p.parse_args()
    try:
        print(json.dumps(search(a.pdf, a.term, a.start_page, a.end_page, a.max_hits, a.excerpt_chars), ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(f'PDF lookup error: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
