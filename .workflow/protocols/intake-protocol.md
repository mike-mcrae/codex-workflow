# Intake Protocol

This workflow uses a two-stage intake model.

## Stage 1: Minimal Bootstrap Intake

At project creation, collect only:

1. Project name
2. Two to three sentences describing the project
3. Whether this is an existing project or a new project
4. Whether to dig deeper now or later

This is enough to create the project folder, seed the brief, and start Codex without front-loading detailed academic questions.

## Stage 2: Deferred Deep Intake

Detailed questions about identification, target journal, key papers, data, empirical design, constraints, and coding workflow are optional at bootstrap.

They should be collected when:

- the user chose `dig deeper now`
- the user later invokes `/more_input`
- Codex is genuinely blocked and cannot proceed responsibly without clarification

## `/more_input` Convention

This repository treats `/more_input` as a project-local command convention inside Codex.

When the user types `/more_input`, Codex should:

1. Pause the current substantive task.
2. Ask the deeper project questions that are still unresolved.
3. Write the answers back into:
   - `notes/project-brief.md`
   - `notes/source-notes.md`
   - `.workflow/memory/session-log.md`
4. Resume the workflow using the updated project state.

## Existing vs New Project

If the project is marked `existing project`:

- prefer adapting existing structure, code, and drafts
- assume prior artifacts may already exist and should be read before replanning

If the project is marked `new project`:

- scaffold from the template defaults
- tolerate more `TBD` placeholders early on

## Dig Deeper Now vs Later

If intake depth is `dig deeper now`:

- ask the deeper intake questions near the start of the first session before serious planning

If intake depth is `dig deeper later`:

- begin with the available information
- defer detailed questions until `/more_input` or a genuine planning block
