# Codex Academic Workflow

A complete repository for running a file-backed, multi-agent academic writing workflow in Codex.

The system is built around four enforced ideas:

1. Planning is mandatory before drafting.
2. Writing is separated from review.
3. Review is multi-agent and cannot be skipped.
4. Refinement loops continue until the manuscript clears the configured quality gates or the run is blocked for manual intervention.

The design is adapted from the architecture of a mature multi-agent academic workflow, but reimplemented for Codex with local files, prompt packets, and a Python state machine.

## Quick Start

1. Clone the repo into a new project folder.
2. Run [scripts/validate_setup.sh](scripts/validate_setup.sh).
3. On your machine, run `new_project` for the fast path.
4. Answer only the four startup questions:
   project name, 2 to 3 sentence description, existing/new, and dig deeper now/later.
5. Start Codex through [scripts/start_codex_session.sh](scripts/start_codex_session.sh) or your wrapped `codex` command.
6. Let Codex defer detailed intake until later if you chose that option.
7. Use `/more_input` inside Codex whenever you want the deeper project questions asked and written back into the repo files.

For the full setup path, see [SETUP.md](SETUP.md).

## What Is Included

- `agents/`: role definitions for planner, writer, reviewer, methods referee, adversarial reviewer, and final editor
- `prompts/`: stage-specific prompt templates used to generate Codex-ready work packets
- `templates/`: reusable document templates for plans, drafts, reviews, and revision logs
- `workflow/`: workflow rules and quality standards
- `workflow/intake-protocol.md`: minimal startup intake and deferred `/more_input` protocol
- `memory/`: layered memory for always-read facts, topic notes, and rolling session context
- `decisions/`: dated decision records cited on demand
- `transcripts/`: raw session archive scaffold for searchable long-tail retrieval
- `workspace/`: project brief, source notes, and per-run state
- `paper/`: LaTeX-ready manuscript scaffold for economics-style papers
- `scripts/`: setup validation, project bootstrap, orchestrator, code audit helpers, memory helpers, and transcript capture tools

## Memory Layers

The repository now uses four distinct memory layers with different access costs:

1. Layer 1, always-read curated memory:
   `memory/MEMORY.md` plus concise topic files under `memory/topics/`
2. Layer 2, decision memory:
   dated files under `decisions/` for settled choices and rejected alternatives
3. Layer 3, rolling resume memory:
   `memory/session-log.md`, read at the start of work packets
4. Layer 4, raw archive memory:
   `transcripts/`, for searchable transcript exports and long-tail retrieval

The prompts and workflow rules tell the agent:

- read Layers 1 and 3 at session start
- consult Layer 2 only when a settled question resurfaces
- keep Layer 4 out of normal context and retrieve it only for exact prior commands, errors, or user wording

## Intake Model

The workflow now uses a two-stage intake:

1. Minimal bootstrap intake:
   project name, short description, existing/new, and dig-deeper now/later
2. Deferred deep intake:
   collected later via `/more_input` or when planning is genuinely blocked

This keeps project startup fast while still preserving a place for detailed academic intake later.

The intended default path is:

- minimal intake at project creation
- plan-first workflow with reasonable placeholders
- deferred deep intake only when needed

## Workflow

The orchestrator enforces this sequence:

`planning -> writing -> review -> refinement -> review -> ... -> complete`

Rules:

- A plan file with `status: approved` is required before writing.
- Review requires all configured review agents.
- At least one refinement pass is mandatory, even if the first review is favorable.
- A run only completes after a post-refinement review round with zero open major issues and unanimous approval from the required reviewers.
- If the maximum number of refinement rounds is exhausted, the run is marked `blocked`.

## Common Commands

```bash
./scripts/validate_setup.sh
python3 scripts/bootstrap_project.py --title "Trade Shocks and Worker Mobility" --author "Your Name"
./scripts/start_codex_session.sh
python3 scripts/orchestrate.py init-run --title "Paper Title"
python3 scripts/orchestrate.py status
python3 scripts/orchestrate.py prepare-stage
python3 scripts/orchestrate.py submit --artifact path/to/file.md
python3 scripts/orchestrate.py prepare-stage --run <run-id>
python3 scripts/orchestrate.py status --run <run-id>
python3 scripts/memory_tools.py new-decision --topic "chosen identification strategy"
python3 scripts/memory_tools.py log-session --title "Draft review" --summary "Closed first review cycle" --inputs "draft_cycle1.md, review_cycle1_summary.md" --outputs "revision_cycle1.md" --decisions "Promoted revision policy to decisions/..." --open-items "Need second review cycle" --next-action "Prepare review packets"
python3 scripts/code_audit.py prepare --file analysis/model.py
python3 scripts/code_audit.py prepare --file analysis/specification.do
python3 scripts/code_audit.py prepare --file analysis/cleaning.R
python3 scripts/session_end_export.py search --query "how did we fix bibtex"
```

## First Workflow Run

```bash
python3 scripts/orchestrate.py init-run --title "Paper Title"
python3 scripts/orchestrate.py status
python3 scripts/orchestrate.py prepare-stage
python3 scripts/orchestrate.py submit --artifact workspace/runs/<run-id>/artifacts/plan.md
```

Repeat `prepare-stage` and `submit` until the run is complete.

## Code Audits

The repository includes language-specific code audit packets for:

- Python
- Stata
- R

Use `python3 scripts/code_audit.py prepare --file <path>` to generate a packet and report stub under `workspace/audits/`.

## Repository Layout

```text
.
├── agents/
├── config/
├── decisions/
├── memory/
├── paper/
│   ├── bibliography/
│   └── sections/
├── prompts/
├── scripts/
├── templates/
├── transcripts/
├── workflow/
└── workspace/
    ├── audits/
    ├── input/
    └── runs/
```

## Notes

- The orchestrator uses only the Python standard library.
- The setup validator uses only POSIX shell and standard command discovery.
- The session-end export/index tool also uses only the Python standard library.
- For automatic transcript capture, launch Codex through `./scripts/start_codex_session.sh`.
- Prompt packets are written to `workspace/runs/<run-id>/packets/`.
- Run state is written to `workspace/runs/<run-id>/state.json`.
- Approved prose can be promoted into the LaTeX manuscript under `paper/`.
- The agent-facing packets now include the layered memory protocol and point to the correct memory files for each stage.
