# Codex Academic Workflow

A ready-to-fork template for AI-assisted academic projects. It gives you a clean research project structure at the top level and keeps the agent machinery hidden under `.workflow/`.

This template is for people who want Codex to help plan, draft, review, refine, and audit academic work without turning the repository itself into a mess.

## Quick Start

1. Fork or clone this repo.
2. Run the setup check:

```bash
./.workflow/scripts/validate_setup.sh
```

3. Bootstrap the project:

```bash
python3 .workflow/scripts/bootstrap_project.py --title "Paper Title" --author "Your Name"
```

4. Start Codex through the launcher:

```bash
./.workflow/scripts/start_codex_session.sh
```

5. Paste the starter prompt from [STARTER_PROMPT.md](STARTER_PROMPT.md).

For full setup details, see [SETUP.md](SETUP.md).

## Starter Prompt

The intended first-session prompt is simple:

> I am starting work on [PROJECT NAME] in this repo. [Describe your project in 2–3 sentences.] Please read the configuration files, adapt them for my project, enter the workflow, and start with planning.

The repo’s full starter prompt is in [STARTER_PROMPT.md](STARTER_PROMPT.md).

## What Codex Will Do

After you start a project, Codex is expected to:

- read the project configuration, notes, and workflow rules
- adapt the repo to your project
- start with a plan rather than drafting immediately
- keep work file-backed rather than hiding state in chat
- write research content into the researcher-facing directories
- run review and refinement loops before treating work as complete
- support code audits for Python, Stata, and R

In practice, the workflow is:

`plan -> draft -> review -> refine -> review`

The goal is that you ask for work in normal language and the repo gives Codex enough structure to handle it consistently.

## Project Structure

The top level is designed for the researcher, not the agent:

```text
.
├── data/
├── scripts/
├── output/
├── manuscript/
├── notes/
└── .workflow/
```

What belongs where:

- `data/`: raw, derived, and external data
- `scripts/`: research code, organized by language
- `output/`: figures, tables, and logs
- `manuscript/`: the paper itself
- `notes/`: the project brief and source notes
- `.workflow/`: internal prompts, memory, state, transcript capture, and workflow scripts

You should mostly work in the first five. `.workflow/` is there so the automation has somewhere to live without cluttering the research project surface.

## Automatic Structure Checks

This repo now checks project structure automatically:

- `new_project` checks and repairs structure before the first commit
- `./.workflow/scripts/start_codex_session.sh` checks and repairs structure before each Codex session
- Codex can also run `/cleanup_structure` if you want an explicit cleanup pass

So if a project starts to drift away from the standard academic layout, the normal entrypoints will pull it back into shape.

## What A New User Needs

For a public fork or clone, the important requirements are:

- `python3`
- `git`
- `codex`
- `script`

Optional:

- `gh` if you want GitHub CLI automation

Most users do not need any machine-specific shell customization to use the template.

## Optional Personal Automation

This repo also supports extra convenience layers, but they are optional:

- a global `new_project` command
- a shell wrapper that routes `codex` through the launcher
- automatic private GitHub repo creation through `gh`

Those are personal machine integrations. They are not required for someone forking this repo.

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

## Included Workflows

This template includes:

- plan-first writing workflow
- multi-stage review and refinement
- layered project memory
- transcript capture and retrieval
- automatic structure cleanup
- code audit flows for Python, Stata, and R

## More Detail

Use these files when you want the deeper mechanics:

- [SETUP.md](SETUP.md)
- [STARTER_PROMPT.md](STARTER_PROMPT.md)
- [.workflow/protocols/specification.md](.workflow/protocols/specification.md)
- [.workflow/protocols/structure-protocol.md](.workflow/protocols/structure-protocol.md)
