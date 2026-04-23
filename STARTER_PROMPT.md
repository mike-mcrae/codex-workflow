# Starter Prompt

Paste this into Codex after the project has been created:

```text
I am starting work on this academic project in this repository.

Please do the following in order:

1. Read README.md, SETUP.md, .workflow/protocols/specification.md, .workflow/protocols/memory-protocol.md, .workflow/protocols/intake-protocol.md, .workflow/protocols/structure-protocol.md, .workflow/config/project.toml, notes/project-brief.md, notes/source-notes.md, .workflow/memory/MEMORY.md, and .workflow/memory/session-log.md.
2. Treat the researcher-facing structure as canonical: data, scripts, output, manuscript, and notes belong at the top level.
3. Treat `.workflow/` as the hidden internal workflow layer. Use it, but do not invent a parallel internal structure elsewhere in the repo.
4. Use the layered memory model correctly:
   - Layer 1: `.workflow/memory/MEMORY.md` and `.workflow/memory/topics/*`
   - Layer 2: `.workflow/decisions/*`
   - Layer 3: `.workflow/memory/session-log.md`
   - Layer 4: `.workflow/transcripts/*`
5. Follow the intake protocol in this repo. Respect whether the project is marked as existing or new, and whether deeper intake should happen now or later.
6. If I type `/more_input`, pause the current task, ask the deeper intake questions, write the answers into `notes/project-brief.md`, `notes/source-notes.md`, and `.workflow/memory/session-log.md`, then resume.
7. If I type `/cleanup_structure`, or if the repo has visibly drifted from the canonical layout, use `.workflow/protocols/structure-protocol.md` and `python3 .workflow/scripts/cleanup_structure.py fix` to restore structure before continuing.
8. Do not draft the manuscript immediately. Start with planning unless the intake protocol requires deeper intake first.
9. Keep the workflow modular and file-backed. Persist important state to the repository instead of leaving it in chat context.
10. If I ask for a code audit, use the language-specific audit flow for Python, Stata, or R.

Once you understand the repository, tell me the immediate next step and begin the workflow.
```
