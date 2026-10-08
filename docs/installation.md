# Installation

Use a local CLI host with skill support. These commands copy the complete folders. Run them from the repository root. They refuse an existing installation. Review or back up an existing skill before you replace it.

## Codex CLI

```sh
python3 scripts/install_skills.py --host codex --scope project --project /path/to/your/project
```

Codex loads project skills from `.agents/skills/` and personal skills from `~/.agents/skills/`. Invoke `$ste100` or `$diagram-first`. Source: [Codex skills](https://learn.chatgpt.com/docs/build-skills).

## Claude Code

```sh
python3 scripts/install_skills.py --host claude --scope project --project /path/to/your/project
```

Claude Code loads project skills from `.claude/skills/` and personal skills from `~/.claude/skills/`. Invoke `/ste100` or `/diagram-first`. Source: [Claude Code skills](https://code.claude.com/docs/en/skills).

## Grok Build

```sh
python3 scripts/install_skills.py --host grok --scope project --project /path/to/your/project
```

Grok Build loads project skills from `.grok/skills/` and personal skills from `~/.grok/skills/`. Invoke `/ste100` or `/diagram-first`. Source: [Grok Build skills](https://docs.x.ai/build/features/skills-plugins-marketplaces).

For a personal installation, use `--scope user` and omit `--project`. To install one skill, add `--skill ste100` or `--skill diagram-first`. The default installs both.

Restart the host or start a new session if its skill list does not refresh. The commands install files. They do not prove model behavior or cloud-product support. Documentation check: 2026-10-07.

## Optional persistent style

Installation keeps normal task-based skill selection. It does not make STE style always on.

To request a persistent plain style, add this instruction yourself: “Use ste100 plain mode for my replies. Preserve meaning and uncertainty.” Put it in the host's project instruction file: `AGENTS.md` for Codex or Grok Build, and `CLAUDE.md` for Claude Code. Personal files use each host's documented user instruction location.

Sources: [Codex instruction files](https://developers.openai.com/codex/guides/agents-md), [Claude Code memory](https://code.claude.com/docs/en/memory), and [Grok Build instruction files](https://docs.x.ai/build/features/skills-plugins-marketplaces).

A local personal installation does not install the skill into ChatGPT, Claude.ai, Cowork, or the Grok web app. Use those products' supported upload routes separately.
