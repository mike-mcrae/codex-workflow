# Codex Academic Workflow

A complete repository for running a file-backed, multi-agent academic writing workflow in Codex.

The system is built around four enforced ideas:

1. Planning is mandatory before drafting.
2. Writing is separated from review.
3. Review is multi-agent and cannot be skipped.
4. Refinement loops continue until the manuscript clears the configured quality gates or the run is blocked for manual intervention.

The design is adapted from the architecture of a mature multi-agent academic workflow, but reimplemented for Codex with local files, prompt packets, and a Python state machine.

## What Is Included

- `agents/`: role definitions for planner, writer, reviewer, methods referee, adversarial reviewer, and final editor
- `prompts/`: stage-specific prompt templates used to generate Codex-ready work packets
- `templates/`: reusable document templates for plans, drafts, reviews, and revision logs
- `workflow/`: workflow rules and quality standards
- `memory/`: layered memory for always-read facts, topic notes, and rolling session context
- `decisions/`: dated decision records cited on demand
- `transcripts/`: raw session archive scaffold for searchable long-tail retrieval
- `workspace/`: project brief, source notes, and per-run state
- `paper/`: LaTeX-ready manuscript scaffold for economics-style papers
- `scripts/orchestrate.py`: the workflow orchestrator

## Quick Start

1. Fill in [config/project.toml](config/project.toml), [workspace/input/project-brief.md](workspace/input/project-brief.md), and [workspace/input/source-notes.md](workspace/input/source-notes.md).
2. Curate the always-read memory in [memory/MEMORY.md](memory/MEMORY.md), add any topic-specific notes under [memory/topics](memory/topics), and review the rolling log in [memory/session-log.md](memory/session-log.md).
3. Start a run:

```bash
python3 scripts/orchestrate.py init-run --title "Trade Shocks and Worker Mobility"
```

4. Inspect status:

```bash
python3 scripts/orchestrate.py status
```

5. Generate the current stage packet:

```bash
python3 scripts/orchestrate.py prepare-stage
```

6. Complete the generated artifact with Codex, then submit it back to the state machine:

```bash
python3 scripts/orchestrate.py submit --artifact workspace/runs/<run-id>/artifacts/plan.md
```

Repeat `prepare-stage` and `submit` until the run reaches `complete`.

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
python3 scripts/orchestrate.py init-run --title "Paper Title"
python3 scripts/orchestrate.py status
python3 scripts/orchestrate.py prepare-stage
python3 scripts/orchestrate.py submit --artifact path/to/file.md
python3 scripts/orchestrate.py prepare-stage --run <run-id>
python3 scripts/orchestrate.py status --run <run-id>
python3 scripts/memory_tools.py new-decision --topic "chosen identification strategy"
python3 scripts/memory_tools.py log-session --title "Draft review" --summary "Closed first review cycle" --inputs "draft_cycle1.md, review_cycle1_summary.md" --outputs "revision_cycle1.md" --decisions "Promoted revision policy to decisions/..." --open-items "Need second review cycle" --next-action "Prepare review packets"
./scripts/start_codex_session.sh
python3 scripts/session_end_export.py export --transcript /path/to/session.md --title "Codex session"
python3 scripts/session_end_export.py search --query "how did we fix bibtex"
```

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
    ├── input/
    └── runs/
```

## Notes

- The orchestrator uses only the Python standard library.
- The session-end export/index tool also uses only the Python standard library.
- For automatic transcript capture, launch Codex through `./scripts/start_codex_session.sh`.
- Prompt packets are written to `workspace/runs/<run-id>/packets/`.
- Run state is written to `workspace/runs/<run-id>/state.json`.
- Approved prose can be promoted into the LaTeX manuscript under `paper/`.
- The agent-facing packets now include the layered memory protocol and point to the correct memory files for each stage.
