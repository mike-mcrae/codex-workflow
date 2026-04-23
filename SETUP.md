# Setup

Use this repository as a reusable Codex workflow template for an academic writing project.

## 1. Clone And Enter The Repo

```bash
git clone git@github.com:mike-mcrae/codex-workflow.git my-paper
cd my-paper
```

## 2. Validate Local Prerequisites

```bash
./scripts/validate_setup.sh
```

This checks for:

- `python3`
- `git`
- `codex`
- `script` for continuous transcript capture

## 3. Set Project-Specific Inputs

Initialize the template first:

```bash
python3 scripts/bootstrap_project.py --title "Paper Title" --author "Your Name"
```

Then edit these files:

- [config/project.toml](config/project.toml)
- [workspace/input/project-brief.md](workspace/input/project-brief.md)
- [workspace/input/source-notes.md](workspace/input/source-notes.md)
- [memory/MEMORY.md](memory/MEMORY.md)

Optional but recommended:

- add topic-specific memory files under [memory/topics](memory/topics)
- add any past architectural decisions under [decisions](decisions)

## 4. Enable Automatic Session Capture

The recommended path is to launch Codex through the wrapper:

```bash
./scripts/start_codex_session.sh
```

If you installed the shell wrapper in `~/.zshrc`, then plain `codex` already routes through the capture launcher in new shells.

## 5. Start Codex With A Consistent Prompt

Use the starter prompt in [STARTER_PROMPT.md](STARTER_PROMPT.md).

That prompt tells Codex to:

- read the workflow files
- honor the layered memory model
- initialize the project from the repo template
- enter the plan-first workflow instead of jumping straight to drafting

## 6. Run The Workflow

Create a run:

```bash
python3 scripts/orchestrate.py init-run --title "Paper Title"
```

Check status:

```bash
python3 scripts/orchestrate.py status
```

Generate the current work packet:

```bash
python3 scripts/orchestrate.py prepare-stage
```

Submit the finished artifact:

```bash
python3 scripts/orchestrate.py submit --artifact workspace/runs/<run-id>/artifacts/plan.md
```

Repeat `prepare-stage` and `submit` until the run reaches `complete`.

## 7. Reuse Across Projects

This repo is meant to stay structurally stable across projects.

Project-to-project variation should mostly live in:

- `config/project.toml`
- `workspace/input/*`
- `memory/*`
- `decisions/*`
- `paper/*`

The workflow engine, prompts, and memory rules should remain largely unchanged unless you are intentionally evolving the template itself.

## 8. Audit Code In Python, Stata, Or R

Generate a language-aware code audit packet:

```bash
python3 scripts/code_audit.py prepare --file path/to/script.py
python3 scripts/code_audit.py prepare --file path/to/script.do
python3 scripts/code_audit.py prepare --file path/to/script.R
```

This creates:

- a packet telling Codex how to review the file
- a structured report stub under `workspace/audits/`
