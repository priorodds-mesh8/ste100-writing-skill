# Project count method v1

The method ID is `ste100-project-count-v1`. This is a project convention with bounded parsing. It has no claim of complete ASD counting coverage.

The technical sentence budgets are 20 words for a procedure and 25 for a description. Descriptive paragraphs have a six-sentence budget. Plain mode reports these as review items. Technical mode reports them as errors.

A word is a Unicode word token. Internal apostrophes and hyphens remain within one token. A decimal remains one token. A number plus a recognized unit remains one token. Units include mm, cm, km, m, kg, g, ms, s, Hz, kHz, MHz, V, kV, A, mA, W, kW, Pa, kPa, MPa, °C, and °F. Unsupported units retain ordinary token counts.

A short double-quoted label, a simple parenthetical group, and a backtick identifier each count as one token. A declared proper name counts as one token, with case-sensitive matching. Other multiword technical terms retain their ordinary count. Single-quoted prose retains ordinary counts.

Common abbreviations count as one token and protect their internal periods. These include e.g., i.e., etc., Dr., Mr., Ms., Mrs., Prof., Fig., No., vs., U.S., and U.K. Other dotted forms need review. Sentence endings after abbreviations can remain ambiguous.

The parser excludes fenced code, URLs, headings, and Markdown controls. It counts visible link labels and image descriptions. Each list item starts a separate block. Wrapped prose lines join within a paragraph. HTML and Markdown tables produce review items; their visible text still receives counts. Indented blocks remain counted and produce a review item.

Nested groups, quoted full sentences, uncommon abbreviations, malformed Markdown, and unmatched delimiters can need manual review. Grammar detection is heuristic. A possible passive form does not prove passive voice. A possible action chain does not prove multiple instructions.

Locations use one-based source line numbers and columns in the normalized prose line. Removed Markdown controls can change columns. Use the line and reason to locate the source text.

For mixed input, put one of these markers before the first prose block and each type change:

```markdown
<!-- ste100:procedure -->
Open the sample case.

<!-- ste100:description -->
The sample case contains three sensors.
```

A marker applies until the next marker. Unclassified prose is invalid input. Fenced code and headings need no classification.

Every finding has an ID, severity, location, reason, and basis. Exit 0 means only that configured checks pass. Exit 1 means a configured error, or a review item with `--fail-on-review`. Exit 2 means invalid input or configuration.
