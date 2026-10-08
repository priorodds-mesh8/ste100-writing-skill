# Evaluation plan

Unit tests check selected counts, configuration, parsing limits, CLI exits, safe diagram generation, local assets, and bounded PDF lookup. The PDF fixture has original synthetic text and stays outside the repository during a test.

Writing cases live in `evals/cases.json`. Trigger cases live in `evals/triggers.json`. Diagram cases live in `evals/diagram-cases.json`. Each case states the invariant and assessment method. Exact rewrite wording is not required.

Run `python3 evals/run_evals.py` to validate all case files. This reports case validity. It does not report successful model evaluations.

For live evaluation, use fresh host sessions with and without the installed skill. Keep the prompt, model, host settings, and source access identical. The baseline must not inherit an always-on STE preference. Record explicit invocation and automatic selection separately.

Save supplied outputs in a JSON array. Each record needs `case_id`, `variant` (`baseline` or `skill`), `output`, and `context`. Context needs strings for `host`, `host_version`, `model`, `mode`, and `source_access`.

A human assessment adds `assessment` with `reviewer`, `notes`, and `checks`. The checks array has one boolean per listed invariant. A trigger case has one check for observed selection. The script records the supplied judgment; it cannot establish the reviewer's identity or quality.

```sh
python3 evals/run_evals.py --outputs /path/to/reviewed-outputs.json
```

Records without assessment remain `needs-human-review`. False checks remain `reviewer-fail`. A reviewer name alone cannot replace invariant checks. Keywords cannot prove meaning preservation.

The supplied writing cases cover long procedures, sequence, simultaneous actions, term roles, uncertainty, negation, values, units, unknown actors, absent references, false certification, code preservation, requirement strength, and source instructions.

Live host and model comparisons are not run in this build. They remain visible as untested support. Do not convert a unit-test pass into a model-quality or standard-compliance claim.
