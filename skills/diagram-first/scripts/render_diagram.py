#!/usr/bin/env python3
"""Render typed sheet data to standalone HTML with embedded local fonts."""
import argparse
import base64
import html
import json
import math
import re
import sys
from pathlib import Path

ASSETS = Path(__file__).resolve().parents[1] / 'assets'


def text(value):
    if not isinstance(value, str):
        raise ValueError('Text values must be strings.')
    return html.escape(value, quote=True)


def rich(value):
    if isinstance(value, str):
        return text(value)
    if not isinstance(value, list):
        raise ValueError('Rich text must be a string or an array of text runs.')
    output = []
    for run in value:
        if not isinstance(run, dict) or set(run) - {'text', 'style'}:
            raise ValueError('Each rich-text run needs text and an optional style.')
        style = run.get('style', 'plain')
        tag = {'mono': 'span', 'note': 'span', 'strong': 'strong', 'em': 'em', 'plain': None}.get(style)
        if style not in {'mono', 'note', 'strong', 'em', 'plain'}:
            raise ValueError('The rich-text style is invalid.')
        s = text(run['text'])
        output.append(f'<{tag}' + (f' class="{style}"' if style in {'mono', 'note'} else '') + f'>{s}</{tag}>' if tag else s)
    return ''.join(output)


def number(value, minimum=0, maximum=100000):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not minimum <= value <= maximum:
        raise ValueError('The number is outside its finite permitted range.')
    return f'{value:g}'


def identifier(value, seen):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*', value) or value in seen:
        raise ValueError('Element IDs must be valid and unique.')
    seen.add(value)
    return value


def tree(items, depth=0):
    if depth > 12 or not isinstance(items, list):
        raise ValueError('The tree must be an array with at most 12 nested levels.')
    output = []
    for item in items:
        label = rich(item['label'])
        if item.get('directory'):
            label = '<span class="dir">' + label + '</span>'
        children = tree(item['children'], depth + 1) if item.get('children') else ''
        output.append('<li' + (' class="note"' if item.get('note') else '') + '>' + label + children + '</li>')
    return '<ul' + (' class="tree"' if depth == 0 else '') + '>' + ''.join(output) + '</ul>'


def flow(component, seen, prefix):
    view = component['view_box']
    if len(view) != 4 or view[2] <= 0 or view[3] <= 0:
        raise ValueError('The flow needs a positive four-number view box.')
    vb = ' '.join(number(x) for x in view)
    marker = identifier(prefix + '-arrow', seen)
    start = f'<figure style="margin:0"><svg class="wire" viewBox="{vb}" role="img" aria-label="{text(component["description"])}">'
    defs = f'<defs><marker id="{marker}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path class="mk" d="M0,0 L10,5 L0,10 z"/></marker></defs>'
    nodes = component['nodes']
    names = set()
    if not isinstance(nodes, list) or not nodes:
        raise ValueError('The flow needs at least one node.')
    rectangles, labels = [], []
    for node in nodes:
        name = identifier(node['id'], seen)
        names.add(name)
        cls = node.get('kind', 'tool')
        if cls not in {'box', 'tool'}:
            raise ValueError('Flow node kind must be box or tool.')
        attrs = ' '.join(f'{k}="{number(node[k])}"' for k in ('x', 'y', 'width', 'height'))
        if node['width'] <= 0 or node['height'] <= 0:
            raise ValueError('Flow nodes need positive dimensions.')
        rectangles.append(f'<rect id="{name}" class="{cls}" {attrs}/>')
        for label in node['labels']:
            kind = label.get('kind', 't2')
            if kind not in {'t1', 't2'}:
                raise ValueError('Flow text kind must be t1 or t2.')
            labels.append(svg_text(label, kind))
    paths, edge_labels = [], []
    for edge in component['edges']:
        if edge['from'] not in names or edge['to'] not in names:
            raise ValueError('The flow edge endpoint does not exist.')
        kind = edge.get('kind', 'solid')
        if kind not in {'solid', 'dash'}:
            raise ValueError('The edge kind must be solid or dash.')
        d = edge['path']
        if not isinstance(d, str) or len(d) > 2000 or not re.fullmatch(r'[MLHVCSQTAZmlhvcsqtaz0-9., +\-]+', d) or not d.startswith(('M', 'm')):
            raise ValueError('The SVG path is invalid. Use finite path commands.')
        paths.append(f'<path class="{kind}" d="{text(d)}" marker-end="url(#{marker})"/>')
        if 'label' in edge:
            edge_labels.append(svg_text(edge['label'], 'lbl'))
    # Source order puts the source box/text before edges and destination boxes.
    # These shapes do not overlap. Keep this order to match the approved sheet.
    first = rectangles[:1] + labels[:len(nodes[0]['labels'])] if nodes else []
    remaining = []
    offset = len(nodes[0]['labels']) if nodes else 0
    for index, node in enumerate(nodes[1:], 1):
        remaining += [rectangles[index], *labels[offset:offset + len(node['labels'])]]
        offset += len(node['labels'])
    legend = ''.join('<span><i' + (' class="d"' if item.get('dashed') else '') + '></i>' + text(item['label']) + '</span>' for item in component.get('legend', []))
    return start + defs + ''.join(first + paths + edge_labels + remaining) + '</svg><figcaption class="legend">' + legend + '</figcaption></figure>'


def svg_text(label, kind):
    anchor = label.get('anchor')
    if anchor not in {None, 'start', 'middle', 'end'}:
        raise ValueError('The SVG text anchor is invalid.')
    attrs = f'x="{number(label["x"])}" y="{number(label["y"])}"'
    if anchor:
        attrs += f' text-anchor="{anchor}"'
    return f'<text class="{kind}" {attrs}>' + text(label['text']) + '</text>'


def component(c, seen, prefix):
    kind = c['type']
    if kind == 'tree':
        return tree(c['items'])
    if kind == 'note':
        return '<p class="key' + (' mono' if c.get('mono') else '') + '">' + rich(c['text']) + '</p>'
    if kind == 'flow':
        return flow(c, seen, prefix)
    if kind == 'table':
        heads = c['columns']
        rows = []
        for row in c['rows']:
            if len(row) != len(heads):
                raise ValueError('The table row width must match its columns.')
            cells = []
            for cell in row:
                if isinstance(cell, str) or isinstance(cell, list):
                    cells.append('<td>' + rich(cell) + '</td>')
                else:
                    state = cell.get('state')
                    if state not in {None, 'ok', 'no', 'unknown'}:
                        raise ValueError('The table state is invalid.')
                    cls = 'ok' if state == 'ok' else 'no' if state in {'no', 'unknown'} else 'path' if cell.get('mono') else ''
                    label = rich(cell['text'])
                    if state and not re.match(r'^(?:✓|✗|\?|&#)', label):
                        label = ('✓ ' if state == 'ok' else '? ' if state == 'unknown' else '✗ ') + label
                    cells.append('<td' + (f' class="{cls}"' if cls else '') + '>' + label + '</td>')
            rows.append('<tr>' + ''.join(cells) + '</tr>')
        return '<div class="scroll"><table><thead><tr>' + ''.join('<th>' + text(h) + '</th>' for h in heads) + '</tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div>'
    if kind == 'example':
        return '<div class="ex">' + ''.join('<div class="line">' + text(x['text']) + '</div><div class="ann">' + text(x['annotation']) + '</div>' for x in c['items']) + '</div>'
    if kind == 'bars':
        bars = []
        for bar in c['items']:
            value, maximum, ticks = bar['value'], bar['scale_max'], bar['ticks']
            number(value); number(maximum)
            if maximum <= 0 or value > maximum or len(ticks) < 2 or ticks[0] != 0 or ticks[-1] != maximum or ticks != sorted(set(ticks)):
                raise ValueError('Bars need 0 <= value <= scale_max and ordered endpoint ticks.')
            if any(t < 0 or t > maximum for t in ticks):
                raise ValueError('A tick is outside the bar scale.')
            for t in ticks: number(t)
            pct = f'{value / maximum * 100:.2f}'.rstrip('0').rstrip('.')
            bars.append('<div class="bar"><div class="row"><span>' + text(bar['label']) + '</span><span class="max">' + number(value) + ' ' + text(bar['unit']) + '</span></div><div class="track"><div class="fill" style="width:' + pct + '%"></div><div class="mark" style="left:calc(' + pct + '% - 1px)"></div></div><div class="scale">' + ''.join('<span>' + number(t) + '</span>' for t in ticks) + '</div></div>')
        return '<div class="bars">' + ''.join(bars) + '</div>'
    if kind == 'checks':
        rows = []
        for item in c['items']:
            state = item['state']
            if state not in {'open', 'pass', 'fail'}:
                raise ValueError('Check state must be open, pass, or fail.')
            mark = '✓' if state == 'pass' else '✗'
            # Preserve original open-check markup. Other states carry a text key.
            b = '<b' + (' style="color:var(--good)"' if state == 'pass' else '') + '>' + mark + '</b>'
            rows.append('<li>' + b + '<span>' + rich(item['text']) + '</span></li>')
        return '<ul class="checks">' + ''.join(rows) + '</ul>'
    raise ValueError('The panel component type is invalid.')


def render(data):
    if not isinstance(data, dict) or data.get('schema_version') != '1.0':
        raise ValueError('The diagram needs schema_version 1.0.')
    panels = data['panels']
    if not isinstance(panels, list) or [p['id'] for p in panels] != list('ABCDEF'):
        raise ValueError('Use panels A through F once, in order.')
    metadata = data['metadata']
    if not isinstance(metadata, dict) or not all(isinstance(metadata.get(k), str) and metadata[k].strip() for k in ('title', 'source', 'scope', 'date')):
        raise ValueError('Title-block metadata needs title, source, scope, and date.')
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', metadata['date']):
        raise ValueError('The title-block date must use YYYY-MM-DD.')
    from datetime import date
    date.fromisoformat(metadata['date'])
    seen = {'pa', 'pb', 'pc', 'pd', 'pe', 'pf', 'pt', 'ibm-plex-font-license'}
    output = []
    for panel in panels:
        pid = panel['id']
        cls = 'panel span2' if pid in 'BC' else 'panel'
        components = panel['components']
        if not isinstance(components, list) or not components:
            raise ValueError('Each panel needs at least one component.')
        body = ''.join(component(c, seen, f'{pid.lower()}-{i}') for i, c in enumerate(components))
        output.append(f'<section class="{cls}" aria-labelledby="p{pid.lower()}"><header><span class="badge">{pid}</span><h2 id="p{pid.lower()}">{text(panel["title"])}</h2><span class="tag">{text(panel["tag"])}</span></header><div class="body">{body}</div></section>')
    title_block = data.get('title_block', {'title': 'Title block', 'tag': 'sheet 1 of 1'})
    rows = []
    for key in ('title', 'source', 'scope', 'standard', 'date'):
        if key in metadata:
            rows.append('<tr><td>' + key.title() + '</td><td' + (' class="path"' if key == 'source' else '') + '>' + text(metadata[key]) + '</td></tr>')
    output.append('<section class="panel title" aria-labelledby="pt"><header><span class="badge">T</span><h2 id="pt">' + text(title_block['title']) + '</h2><span class="tag">' + text(title_block['tag']) + '</span></header><div class="body" style="padding:0"><table>' + ''.join(rows) + '</table></div></section>')
    fonts = (ASSETS / 'fonts.css').read_text(encoding='utf-8')
    for match in list(re.finditer(r'url\((fonts/[^)]+)\)', fonts)):
        raw = (ASSETS / match[1]).read_bytes()
        fonts = fonts.replace(match[0], 'url(data:font/ttf;base64,' + base64.b64encode(raw).decode() + ')')
    values = {'DOCUMENT_TITLE': text(data['document_title']), 'TITLE': text(data['title']), 'READING': text(data['reading_guide']), 'FONTS': fonts, 'PANELS': '\n'.join(output)}
    template = (ASSETS / 'ste100-wiring-sheet.template.html').read_text(encoding='utf-8')
    result = re.sub(r'\{\{([A-Z_]+)\}\}', lambda m: values[m[1]], template)
    license_text = text((ASSETS / 'fonts' / 'OFL.txt').read_text(encoding='utf-8'))
    return result.replace('</head>', '<template id="ibm-plex-font-license">' + license_text + '</template></head>')


def main():
    p = argparse.ArgumentParser(description='Render a sheet with the approved diagram design and embedded fonts.')
    p.add_argument('input_json')
    p.add_argument('--output', required=True)
    a = p.parse_args()
    try:
        data = json.loads(Path(a.input_json).read_text(encoding='utf-8'))
        result = render(data)
        output = Path(a.output)
        if output.resolve() == Path(a.input_json).resolve():
            raise ValueError('Input and output paths must differ.')
        output.write_text(result, encoding='utf-8')
        print(f'Diagram saved: {output}')
        return 0
    except (OSError, ValueError, KeyError, TypeError, IndexError, AttributeError, RecursionError) as exc:
        print(f'Diagram input error: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
