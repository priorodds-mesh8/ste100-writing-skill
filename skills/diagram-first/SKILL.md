---
name: diagram-first
description: "Build an HTML diagram in the approved engineering-sheet design when the user requests a diagram or a visual explanation with several parts. Supports structure, flow, status, examples, limits, and checks."
---

# Diagram first

Build a native HTML, CSS, and inline SVG sheet. Use the bundled design. The fixed layout has panels A through F and title block T. A sits beside wide B. Wide C sits beside D. E, F, and T form the last row. It changes to one column at 900 pixels.

Read [diagram-style.md](references/diagram-style.md) for the fixed visual system. Read [diagram-data.md](references/diagram-data.md) before you build the JSON input. The bundled workflow fixture gives a complete input example.

State the question in the title. Choose a source component for each panel: tree, flow, table, annotated example, measured bars, or checks. Use notes for context. A panel can contain more than one component. Keep one main idea per panel.

Use facts supplied by the user or supported by sources. Do not invent a value or status to fill a panel. Write short labels with one meaning. Use one name for each thing. Keep needed identifiers and exact values.

Render from the installed skill folder:

```sh
python3 scripts/render_diagram.py assets/workflow-example.json --output diagram.html
```

For a new diagram, write its JSON to an appropriate working file and use that path. The renderer needs Python 3.11 or later. Its output embeds the matching fonts and their license. It needs no network service, diagram framework, or other skill.

Open the output in a browser or the host's HTML preview. Check light and dark themes, desktop and phone widths, labels, source facts, and document overflow. The renderer validates data; it cannot prove semantic accuracy or fit for every new dataset. Give the HTML link and a short reading guide.

Keep the approved colors, fonts, grid, panel spans, spacing, and component styles. Use a different format only when the user explicitly requests it. Do not replace this design with a generic Mermaid diagram.

Use this skill for a requested diagram or visual explanation. Keep simple answers and requested prose in their natural form. The historical reference fixture records an old setup. Its paths and test states are not current support claims.
