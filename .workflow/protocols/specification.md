# Workflow Specification

This repository implements a Codex-native academic workflow with persistent, file-based state.

## Core State Machine

```text
planning -> writing -> review -> refinement -> review -> ... -> complete
                                         \
                                          -> blocked
```

## Mandatory Rules

1. No writing before an approved plan exists.
2. No refinement before all required review reports exist.
3. No completion before at least one refinement pass has been executed.
4. No completion if any required reviewer reports open major issues.
5. No completion unless all required reviewers return `overall_decision: approve`.
6. Every stage transition must be persisted to disk.

## Agents

- `planner`: converts the project brief into a section-level plan
- `writer`: produces the working manuscript draft
- `reviewer`: provides balanced scholarly review
- `methods-referee`: stress-tests identification and inferential claims
- `adversarial-reviewer`: searches for fatal weaknesses and overclaiming
- `final-editor`: prepares approved text for manuscript handoff
- `python-reviewer`: audits Python research code
- `stata-reviewer`: audits Stata workflows
- `r-reviewer`: audits R research code

## Canonical Layout

Researcher-facing work belongs in:

- `data/`
- `scripts/`
- `output/`
- `manuscript/`
- `notes/`

Internal workflow state belongs in `.workflow/`.

## Persistent Memory

The system keeps memory in files rather than chat context:

- Layer 1: `.workflow/memory/MEMORY.md` and `.workflow/memory/topics/`
- Layer 2: `.workflow/decisions/YYYY-MM-DD-topic.md`
- Layer 3: `.workflow/memory/session-log.md`
- Layer 4: `.workflow/transcripts/`
- Working inputs: `notes/project-brief.md` and `notes/source-notes.md`
- Run state: `.workflow/state/runs/<run-id>/state.json` and `.workflow/state/runs/<run-id>/artifacts/`

Access rules:

1. Read Layers 1 and 3 at the start of substantive work.
2. Keep Layer 1 concise.
3. Use Layer 2 when a settled design choice is challenged.
4. Use Layer 4 only for retrieval of exact prior commands, errors, or wording.
5. Do not dump transcripts into Layers 1 or 3.

## Review Logic

Each review cycle requires all reviewers listed in `.workflow/config/project.toml`.

The orchestrator:

- sends the run to `refinement` if any major issues remain open
- sends the run to `refinement` even when the first review is favorable
- sends the run to `complete` only after a post-refinement review cycle clears all major issues and receives unanimous approval
- sends the run to `blocked` if the maximum refinement count is exhausted without clearance

## Code Audit Logic

Standalone code audits are supported for:

- Python (`.py`)
- Stata (`.do`)
- R (`.R`)

Use `python3 .workflow/scripts/code_audit.py prepare --file <path>` to generate a packet and report stub in `.workflow/state/audits/`.

## Output Conventions

- Plans use `.workflow/templates/plan.md`
- Drafts use `.workflow/templates/draft.md`
- Review reports use `.workflow/templates/review-report.md`
- Refinement logs use `.workflow/templates/revision-log.md`

These templates expose frontmatter that the orchestrator validates.
