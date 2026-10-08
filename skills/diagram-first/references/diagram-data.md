# Diagram data format v1

The input is a UTF-8 JSON object. The installed `../assets/workflow-example.json` is a full example. The renderer accepts data, not raw HTML or scripts.

Required top-level fields:

| Field | Type | Meaning |
| --- | --- | --- |
| schema_version | string | Exactly `1.0` |
| document_title | string | Browser title |
| title | string | The question the sheet answers |
| reading_guide | string | Short panel reading order |
| panels | array | A, B, C, D, E, F in that order |
| metadata | object | title, source, scope, date; optional standard |

The date uses a real `YYYY-MM-DD` calendar date. Optional `title_block` carries `title` and `tag`. Its defaults are “Title block” and “sheet 1 of 1”. Panel IDs and spans are fixed. Each panel needs `id`, `title`, `tag`, and a nonempty `components` array.

Text is a string. A rich-text value can also be an array of objects with `text` and optional `style`. Styles are `plain`, `mono`, `note`, `strong`, and `em`. All text is escaped. Use text runs only where a component below permits rich text.

## Components

`note`: `text` is rich text. Optional `mono: true` gives the whole note a technical-label font.

`tree`: `items` is an array. Each item has a rich `label` and optional `directory`, `note`, and nested `children`. The nesting limit is 12 levels.

`example`: `items` contains objects with string `text` and `annotation`. Each annotation sits below its source line.

`checks`: `items` contains objects with `state` (`open`, `pass`, or `fail`) and rich `text`. The output uses a visible mark with the status color. Say “open” in the text or panel tag when it matters.

`table`: `columns` is an array of string labels. `rows` is an array of cell arrays. Each row matches the column count. A cell can be rich text, or an object with rich `text` and optional `mono` or `state`. States are `ok`, `no`, and `unknown`. The renderer adds a status mark if the label has none. State takes priority over `mono`.

`bars`: `items` contains objects with string `label`, numeric `value`, string `unit`, numeric `scale_max`, and numeric `ticks`. The scale starts at zero. The maximum is positive. The value is within the scale. Ticks are unique, ordered, include both endpoints, and stay within the scale. The fill and marker use value divided by scale maximum. Do not enter a percentage by eye.

## SVG flow

A `flow` needs `description`, `view_box`, `nodes`, and `edges`. Optional `legend` contains string `label` and optional boolean `dashed`.

`view_box` is four numbers: origin x, origin y, width, height. Use positive dimensions. The reference uses `[0, 0, 570, 300]`.

Each node needs a unique `id`, `kind` (`box` or `tool`), numeric `x`, `y`, `width`, `height`, and `labels`. A label needs string `text`, numeric `x` and `y`, and optional `kind` (`t1` or `t2`) and `anchor` (`start`, `middle`, or `end`). Label positions are absolute within the SVG view box.

Each edge needs `from`, `to`, and `path`. Its endpoints must name existing nodes. Optional `kind` is `solid` or `dash`. An optional `label` has string `text`, numeric `x` and `y`, and optional `anchor`.

Use SVG path commands and numeric coordinates for `path`. Raw markup, attributes, and scripts are rejected. The renderer supplies arrow markers. IDs begin with a letter and use letters, digits, underscores, or hyphens. IDs must be unique across the sheet.

Use the workflow example's flow geometry as a starting point. Change labels and add supported nodes as the facts need them. Check label fit and connector geometry in a browser. Data validation does not prove readability or the correctness of a connection.

The output is one HTML file with the original styles and six embedded font faces. It includes the font license as inert document data. It works offline. The unchanged historical reference retains its original online font links.
