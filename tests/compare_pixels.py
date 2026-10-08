#!/usr/bin/env python3
"""Compare screenshot pixels, without depending on PNG metadata."""
import json
import sys
from pathlib import Path
from PIL import Image, ImageChops


def main(folder):
    folder = Path(folder)
    results = []
    for width in (1280, 390, 899, 901):
        for theme in ('light', 'dark'):
            prefix = f'{width}-{theme}'
            with Image.open(folder / f'{prefix}-reference.png') as original, Image.open(folder / f'{prefix}-rendered.png') as output:
                a, b = original.convert('RGB'), output.convert('RGB')
                same_size = a.size == b.size
                pixels = sum(any(rgb) for rgb in ImageChops.difference(a, b).getdata()) if same_size else None
                results.append(dict(width=width, theme=theme, same_size=same_size, changed_pixels=pixels, passed=same_size and pixels == 0))
    report = dict(schema_version='1.0', comparisons=results, passed=all(r['passed'] for r in results))
    (folder / 'pixel-results.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__': sys.exit(main(sys.argv[1]))
