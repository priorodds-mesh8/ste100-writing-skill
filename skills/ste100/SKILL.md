---
name: ste100
description: "Write or review text when the user requests STE, ASD-STE100, Simplified Technical English, or this skill's plain style. Supports procedures, descriptions, and general prose."
---

# STE100 writing aid

Preserve the meaning before you change the style. Keep facts, values, units, dates, negation, conditions, action order, identifiers, and requirement strength. Keep uncertainty. Do not invent an actor to remove passive voice.

Use `plain` when the user invokes this skill without a clear technical task. Use `technical` for an explicit technical STE rewrite. Use `reference-review` for a source-based review with authorized local reference access. Read [modes.md](references/modes.md) for mode-specific work.

Use short sentences, active voice when the actor is known, familiar words, and consistent terms. Keep related facts connected. Use paragraphs and lists where they help. Prefer American spelling unless the user or source needs another convention. Keep official names and needed technical terms.

Keep code, commands, configuration keys, identifiers, and quoted source text unchanged unless the user requests edits. Do not turn recommendations into obligations. If a safe rewrite needs a missing fact, report the ambiguity and rewrite the independent parts.

For technical text, classify each relevant block as a procedure or description. Use 20 words per procedure sentence and 25 per descriptive sentence. Keep necessary simultaneous actions together. Read [counting.md](references/counting.md) before a count-based ruling.

Run the bundled checker from this skill folder when deterministic checks help:

```sh
python3 scripts/check_text.py draft.md --mode technical --text-type description --format json
```

Use the user's document path in place of `draft.md`. Run from the installed folder, or use the script's full resolved path. The checker needs Python 3.11 or later. It has no runtime dependency.

The checker reports selected structural checks and possible grammar issues. A passing check does not prove vocabulary approval, meaning accuracy, or full STE compliance. Do not use a compliance percentage.

For a rewrite, give the requested text first. For a review, give material findings first. In technical reviews, give one compact coverage statement. Separate configured failures, heuristic findings, and source-backed rulings. State unresolved checks.

For authorized reference access, read [local-reference.md](references/local-reference.md). Inspect the relevant meanings, roles, forms, and restrictions. Do not assume one spelling has only one approved role or meaning. If source access is absent, give a limited review and name the checks that do not run.

This is an unofficial writing aid. It does not replace or certify against the official standard. Do not apply this skill to unrelated writing solely because it is installed.
