# Structure Protocol

This repository uses a researcher-first academic layout with a hidden internal workflow layer.

## Canonical Top-Level Structure

Researcher-facing work belongs in these top-level directories:

- `data/raw/`: immutable source data snapshots
- `data/derived/`: cleaned, merged, or transformed datasets
- `data/external/`: third-party files, documentation, or reference extracts
- `scripts/python/`: Python analysis and data-processing code
- `scripts/stata/`: Stata do-files
- `scripts/r/`: R scripts
- `scripts/shell/`: shell utilities that support the research workflow
- `output/figures/`: generated figures
- `output/tables/`: generated tables
- `output/logs/`: run logs, estimation logs, or compile logs
- `manuscript/`: the paper itself
- `notes/`: project brief and source notes

For migrated existing projects, substructure inside these top-level directories can remain project-specific. The rigid rule is the top-level academic layout. The internal subfolders do not have to be identical across all projects.

## Hidden Internal Structure

Internal automation belongs under `.workflow/`:

- `.workflow/agents/`
- `.workflow/config/`
- `.workflow/decisions/`
- `.workflow/memory/`
- `.workflow/prompts/`
- `.workflow/protocols/`
- `.workflow/scripts/`
- `.workflow/state/`
- `.workflow/templates/`
- `.workflow/transcripts/`
- `.workflow/skills/`

Researchers should not have to navigate `.workflow/` during normal work.

## Placement Rules

1. Research code belongs under top-level `scripts/`, not under `.workflow/scripts/`.
2. Generated research outputs belong under `output/`, not at the repository root.
3. Manuscript files belong under `manuscript/`, not under legacy `paper/`.
4. Planning notes belong under `notes/`.
5. Internal workflow state, prompts, memory, and transcript archives stay inside `.workflow/`.
6. Do not create a second parallel internal system outside `.workflow/`.

## Repair Rules

If legacy template paths appear, they should be migrated as follows:

- `paper/` -> `manuscript/`
- `workspace/input/project-brief.md` -> `notes/project-brief.md`
- `workspace/input/source-notes.md` -> `notes/source-notes.md`
- `workspace/runs/` -> `.workflow/state/runs/`
- `workspace/audits/` -> `.workflow/state/audits/`
- internal top-level directories such as `agents/`, `config/`, `decisions/`, `memory/`, `prompts/`, `templates/`, `transcripts/`, and `workflow/` -> `.workflow/...`
- old internal top-level scripts -> `.workflow/scripts/`

When a repair moves files, linked paths in repository text files should be rewritten so commands and references still work.

## `/cleanup_structure` Convention

This repository treats `/cleanup_structure` as a project-local Codex command convention.

When the user types `/cleanup_structure`, or when the repo has visibly drifted from the canonical layout, Codex should:

1. Read this protocol.
2. Run `python3 .workflow/scripts/cleanup_structure.py check`.
3. If drift exists, run `python3 .workflow/scripts/cleanup_structure.py fix`.
4. Summarize what moved and any conflicts that need a manual decision.

## Safety Rule

The cleanup tool should be conservative:

- migrate only known template paths automatically
- avoid moving arbitrary researcher files unless their destination is obvious from the canonical layout
- report conflicts instead of overwriting divergent files
