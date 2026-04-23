# Setup

This repo supports two setup styles:

1. public/manual setup for anyone who forks or clones the template
2. optional personal machine automation such as `new_project` and a `codex` shell wrapper

Your personal machine setup is separate from the public template. Other users should not assume they already have it.

## Public Manual Setup

Required tools:

- `python3`
- `git`
- `codex`
- `script`

Optional:

- `gh` if the user wants GitHub CLI automation

Validate the environment:

```bash
./.workflow/scripts/validate_setup.sh
```

Clone the repo:

```bash
git clone git@github.com:<your-user>/codex-workflow.git my-project
cd my-project
```

Bootstrap the project files:

```bash
python3 .workflow/scripts/bootstrap_project.py --title "Paper Title" --author "Your Name"
```

Then edit:

- `.workflow/config/project.toml`
- `notes/project-brief.md`
- `notes/source-notes.md`
- `.workflow/memory/MEMORY.md`

Start Codex through the launcher:

```bash
./.workflow/scripts/start_codex_session.sh
```

Use [STARTER_PROMPT.md](STARTER_PROMPT.md) for the first session.

## Optional Personal Machine Setup

If someone wants the same convenience layer you use locally, they can add it themselves. This is optional, not part of the base repo contract.

Typical additions are:

- install `new_project` as a global command
- wrap `codex` so it always launches through `.workflow/scripts/start_codex_session.sh`
- run `gh auth login` once so new projects can be created as private GitHub repos automatically

## `new_project`

`new_project` is a convenience wrapper around this template.

It:

1. creates a new project directory
2. copies the template
3. collects the four bootstrap answers
4. verifies and repairs structure before the first commit
5. asks whether this project should launch Codex with `--dangerously-bypass-approvals-and-sandbox`
6. initializes git
7. optionally creates and pushes a private GitHub repo
8. launches Codex

If a user wants automatic private repo creation, they need:

```bash
gh auth login
```

If they want unrestricted Codex sessions for that project, they can answer `y` when `new_project` asks whether to bypass approvals and sandbox. That preference is stored in `.workflow/config/project.toml` and reused by the session launcher.

## Automatic Structure Checks

Structure checks are automatic if the user follows the normal path:

- `new_project` runs a structure check before the first commit
- `./.workflow/scripts/start_codex_session.sh` runs a structure check before each Codex session

Manual commands are still available:

```bash
python3 .workflow/scripts/cleanup_structure.py check
python3 .workflow/scripts/cleanup_structure.py fix
```

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
