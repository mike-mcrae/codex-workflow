# Setup

This repo is a reusable template for academic projects with a researcher-facing layout and hidden Codex workflow support.

## Machine Setup

Required tools:

- `python3`
- `git`
- `codex`
- `script`
- `gh` for automatic private GitHub repo creation

Validate the environment:

```bash
./.workflow/scripts/validate_setup.sh
```

If you want `new_project` to create and push private GitHub repositories automatically, run once:

```bash
gh auth login
```

## Fast Path

Use the machine-level helper:

```bash
new_project
```

That command:

1. creates `~/Documents/GitHub/<project_name>`
2. copies this template into the new folder
3. fills the minimum intake files
4. runs the structure checker and auto-repairs any template drift
5. initializes git
6. creates a private GitHub repo and pushes the initial commit
7. starts Codex in the new project

## Manual Path

Clone the template:

```bash
git clone git@github.com:mike-mcrae/codex-workflow.git my-project
cd my-project
```

Bootstrap the files:

```bash
python3 .workflow/scripts/bootstrap_project.py --title "Paper Title" --author "Your Name"
```

Then edit:

- `.workflow/config/project.toml`
- `notes/project-brief.md`
- `notes/source-notes.md`
- `.workflow/memory/MEMORY.md`

## Launching Codex

Start Codex through the launcher so transcripts are captured continuously:

```bash
./.workflow/scripts/start_codex_session.sh
```

If your shell wrapper is installed, plain `codex` already routes through that launcher.

## Starter Prompt

Use [STARTER_PROMPT.md](STARTER_PROMPT.md) when starting manual sessions. It tells Codex to read:

- `.workflow/protocols/specification.md`
- `.workflow/protocols/memory-protocol.md`
- `.workflow/protocols/intake-protocol.md`
- `.workflow/protocols/structure-protocol.md`
- `.workflow/config/project.toml`
- `notes/project-brief.md`
- `notes/source-notes.md`
- `.workflow/memory/MEMORY.md`
- `.workflow/memory/session-log.md`

## Workflow Commands

```bash
python3 .workflow/scripts/orchestrate.py init-run --title "Paper Title"
python3 .workflow/scripts/orchestrate.py status
python3 .workflow/scripts/orchestrate.py prepare-stage
python3 .workflow/scripts/orchestrate.py submit --artifact .workflow/state/runs/<run-id>/artifacts/plan.md
```

## Maintenance Commands

Code audit:

```bash
python3 .workflow/scripts/code_audit.py prepare --file scripts/python/analysis.py
python3 .workflow/scripts/code_audit.py prepare --file scripts/stata/analysis.do
python3 .workflow/scripts/code_audit.py prepare --file scripts/r/analysis.R
```

Structure check and repair:

```bash
python3 .workflow/scripts/cleanup_structure.py check
python3 .workflow/scripts/cleanup_structure.py fix
```
