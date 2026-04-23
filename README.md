# Codex Academic Workflow

This repo is a reusable academic project template. It keeps the researcher-facing project structure simple and pushes the agent machinery into a hidden `.workflow/` directory.

The researcher-facing directories are:

- `data/`
- `scripts/`
- `output/`
- `manuscript/`
- `notes/`

The internal automation lives under `.workflow/`:

- agent instructions
- prompts and templates
- layered memory
- transcript archive
- workflow scripts
- run state

## Public Use

If you fork or clone this repo, you do not need the author’s personal shell setup.

The standard path is:

1. Fork or clone the repository.
2. Run `./.workflow/scripts/validate_setup.sh`.
3. Bootstrap the project files.
4. Start Codex through the launcher.
5. Paste the starter prompt from [STARTER_PROMPT.md](STARTER_PROMPT.md).

Example:

```bash
git clone git@github.com:<your-user>/codex-workflow.git my-project
cd my-project
./.workflow/scripts/validate_setup.sh
python3 .workflow/scripts/bootstrap_project.py --title "Paper Title" --author "Your Name"
./.workflow/scripts/start_codex_session.sh
```

## Optional Personal Automation

This repo also supports machine-level conveniences, but those are optional:

- a global `new_project` command
- a shell wrapper that routes `codex` through the session launcher
- automatic GitHub repo creation through `gh`

Those are personal machine integrations. They are not required for someone else forking this repo.

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
    ├── skills/
    ├── state/
    ├── templates/
    └── transcripts/
```

## Automatic Structure Hygiene

The repo now checks structure in three places:

1. `new_project` verifies and repairs structure before the first commit.
2. `./.workflow/scripts/start_codex_session.sh` checks and repairs structure before every Codex session.
3. Codex can still be told to run `/cleanup_structure` explicitly if you want a manual cleanup pass.

That means the user usually does not need to trigger structure cleanup manually, as long as they start Codex through the launcher or a wrapper that calls it.

## Internal Workflow

The state machine is:

`planning -> writing -> review -> refinement -> review -> ... -> complete`

The repo keeps four memory layers:

1. `.workflow/memory/MEMORY.md` and `.workflow/memory/topics/*`
2. `.workflow/decisions/*`
3. `.workflow/memory/session-log.md`
4. `.workflow/transcripts/*`

Codex reads the rules from `.workflow/protocols/`.

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

## Structure Hygiene Tools

The cleanup layer includes:

- [structure-protocol.md](/Users/mikemcrae/Documents/GitHub/codex%20workflow/.workflow/protocols/structure-protocol.md)
- [cleanup_structure.py](/Users/mikemcrae/Documents/GitHub/codex%20workflow/.workflow/scripts/cleanup_structure.py)
- [SKILL.md](/Users/mikemcrae/Documents/GitHub/codex%20workflow/.workflow/skills/academic-cleanup/SKILL.md)

## Code Audits

The workflow includes language-specific audit packets for:

- Python
- Stata
- R

Run `python3 .workflow/scripts/code_audit.py prepare --file <path>` to generate a review packet and report stub under `.workflow/state/audits/`.
