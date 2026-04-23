# Starter Prompt

Paste this into Codex after you have filled in the project files:

```text
I am starting work on this academic writing project in this repository.

Please do the following in order:

1. Read README.md, SETUP.md, workflow/specification.md, workflow/memory-protocol.md, workflow/intake-protocol.md, config/project.toml, workspace/input/project-brief.md, workspace/input/source-notes.md, memory/MEMORY.md, and memory/session-log.md.
2. Treat this repository as a reusable Codex academic workflow template.
3. Use the layered memory model correctly:
   - Layer 1: MEMORY.md and memory/topics/*
   - Layer 2: decisions/*
   - Layer 3: memory/session-log.md
   - Layer 4: transcripts/*
4. Follow the intake protocol in this repo. Respect whether the project is marked as existing or new, and whether deeper intake should happen now or later.
5. If I type `/more_input`, treat that as an instruction to run the deferred intake flow, ask the deeper project questions, and write the answers back into the repository files.
6. Do not draft the paper immediately. Start with planning unless the intake protocol requires a deeper intake first.
7. Use the planner logic in this repo to create the first approved plan for the project.
8. Keep the workflow modular and file-backed. Do not invent a parallel structure outside the repository conventions.
9. When resuming later sessions, use the existing memory and run-state files instead of starting over.
10. If I ask for a code audit, use the language-specific audit flow for Python, Stata, or R rather than treating code review as generic prose review.

Once you understand the repository, tell me the immediate next step and begin the workflow.
```
