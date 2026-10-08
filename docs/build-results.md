# Build results — 2026-10-07

Release: 0.1.0. The local source package is ready for GitHub publication with these stated limits.

The Python 3.12.14 suite passes 48 tests with zero skips. It includes the optional synthetic PDF lookup through pypdf. The core scripts also pass on Python 3.14.6. Without the optional PDF dependency, its content-lookup test skips. The missing-dependency behavior still runs.

Both skill folders pass the bundled Codex skill metadata validator. Relative skill links resolve. Clean copies in the Codex, Claude Code, and Grok Build project paths run the checker and renderer successfully. A personal-folder copy test uses an isolated test home. Existing files and broken symlinks cause a refusal.

The visual test uses Playwright 1.62.1, Chromium 151.0.7922.34, and macOS. The historical fixture matches the unchanged export with zero changed pixels in all eight comparisons. Widths are 1280, 390, 899, and 901. Both light and dark themes pass. Panel geometry and document width match. Matching local IBM Plex faces load in both documents. See `visual-results.json`.

The new workflow fixture works offline at the same widths and themes. It makes zero remote requests and has no document-wide overflow. Desktop and phone screenshots receive a visual inspection. Generated output embeds six font faces and the font license.

The evaluation runner validates 19 cases. It makes no model calls. Fresh-session writing quality, baseline comparisons, and automatic host discovery remain untested. Codex CLI 0.160.0 and Claude Code 2.1.292 are present in the build environment; their model behavior is not a tested support claim. Grok Build live behavior is also untested.

The checker uses project-defined counts. Grammar and term-role flags need review. Vocabulary approval, preserved meaning, and full standard compliance are outside deterministic coverage.

The source and release archive exclude private inputs, PDFs, extracted dictionaries, development caches, personal absolute paths, and generated reference excerpts. The historical diagram keeps its reviewed source labels. It contains no user account path or source conversation transcript.

The project has a Git repository and an installable source archive. Public upload, repository creation on GitHub, and X or email sends remain separate actions.
