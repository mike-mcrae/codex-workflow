# Codex Academic Workflow

This template is designed to feel like a normal academic project for the researcher and a hidden workflow system for Codex.

The researcher-facing directories are:

- `data/`: raw, derived, and external data
- `scripts/`: researcher code, organized by language
- `output/`: figures, tables, and logs
- `manuscript/`: LaTeX manuscript files
- `notes/`: project brief and source notes

The internal automation lives under `.workflow/`. That folder contains the agent definitions, prompts, memory layers, transcript archive, orchestrator, and setup utilities. Researchers should rarely need to touch it directly.

## Quick Start

1. Run `new_project` from any terminal.
2. Answer four questions:
   - project name
   - 2 to 3 sentence description
   - existing project or new project
   - dig deeper now or later
3. If `gh auth login` has already been completed on the machine, the project is created as a private GitHub repo automatically.
4. Codex starts inside the new project and continues from the starter prompt.

For manual setup, see [SETUP.md](SETUP.md).

## Researcher Layout

```text
.
├── data/
│   ├── derived/
│   ├── external/
│   └── raw/
├── manuscript/
│   ├── bibliography/
│   ├── figures/
│   ├── sections/
│   └── main.tex
├── notes/
│   ├── project-brief.md
│   └── source-notes.md
├── output/
│   ├── figures/
│   ├── logs/
│   └── tables/
├── scripts/
│   ├── python/
│   ├── r/
│   ├── shell/
│   └── stata/
└── .workflow/
    ├── agents/
    ├── config/
    ├── decisions/
    ├── memory/
    ├── prompts/
    ├── protocols/
    ├── scripts/
    ├── state/
    ├── templates/
    └── transcripts/
```

## Internal Workflow

The internal state machine is:

`planning -> writing -> review -> refinement -> review -> ... -> complete`

The repo also keeps four memory layers:

1. `.workflow/memory/MEMORY.md` and `.workflow/memory/topics/*`
2. `.workflow/decisions/*`
3. `.workflow/memory/session-log.md`
4. `.workflow/transcripts/*`

Codex reads the structure, memory, and intake protocols from `.workflow/protocols/`.

## Common Commands

```bash
./.workflow/scripts/validate_setup.sh
python3 .workflow/scripts/bootstrap_project.py --title "Paper Title" --author "Your Name"
./.workflow/scripts/start_codex_session.sh
python3 .workflow/scripts/orchestrate.py init-run --title "Paper Title"
python3 .workflow/scripts/orchestrate.py prepare-stage
python3 .workflow/scripts/code_audit.py prepare --file scripts/python/analysis.py
python3 .workflow/scripts/cleanup_structure.py check
python3 .workflow/scripts/cleanup_structure.py fix
```

## Structure Hygiene

This template now includes an academic structure cleanup layer:

- `.workflow/protocols/structure-protocol.md`: canonical layout and rules
- `.workflow/scripts/cleanup_structure.py`: checker and fixer
- `.workflow/skills/academic-cleanup/`: repo-local skill bundle for Codex

Use the cleanup tool when:

- a project has drifted from the canonical layout
- files need to be migrated from legacy template paths
- internal workflow files need their links repaired after restructuring
- you want Codex to reassert the standard academic folder structure

Inside Codex, this repo also treats `/cleanup_structure` as a project-local command convention.

## Code Audits

The workflow includes language-specific audit packets for:

- Python
- Stata
- R

Run `python3 .workflow/scripts/code_audit.py prepare --file <path>` to generate a review packet and report stub under `.workflow/state/audits/`.
