# Workflow Specification

This repository implements a Codex-native academic writing workflow with persistent, file-based state.

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

- `planner`: converts the project brief into a section-level writing plan
- `writer`: produces the working manuscript draft
- `reviewer`: provides balanced scholarly review across argument, contribution, and prose
- `methods-referee`: stress-tests identification, econometrics, and inferential claims
- `adversarial-reviewer`: searches for fatal weaknesses, overclaiming, and referee-style objections
- `final-editor`: optional final pass for copy, coherence, and LaTeX handoff

## Persistent Memory

The system keeps memory in files rather than chat context. Memory is split by access pattern:

- Layer 1, always-read curated memory:
  `memory/MEMORY.md` and concise topical files under `memory/topics/`
- Layer 2, cited decision memory:
  append-only files under `decisions/YYYY-MM-DD-topic.md`
- Layer 3, rolling resume memory:
  `memory/session-log.md`
- Layer 4, searchable raw archive:
  `transcripts/`
- Working inputs:
  `workspace/input/project-brief.md` and `workspace/input/source-notes.md`
- Run state:
  `workspace/runs/<run-id>/state.json` and `workspace/runs/<run-id>/artifacts/`

Access rules:

1. Read Layers 1 and 3 at the start of each substantive work packet.
2. Keep Layer 1 concise. Stable facts and rules only.
3. Use Layer 2 when a settled design decision is challenged or revisited.
4. Use Layer 4 only for retrieval of exact prior commands, errors, or phrasing.
5. Do not dump raw transcripts into Layer 1 or Layer 3.

## Review Logic

Each review cycle requires all reviewers listed in `config/project.toml`.

The orchestrator synthesizes those reports into a review summary and then:

- sends the run to `refinement` if any major issues remain open
- sends the run to `refinement` even when the first review is favorable, because the workflow requires at least one revision round
- sends the run to `complete` only after a post-refinement review cycle clears all major issues and receives unanimous approval
- sends the run to `blocked` if the maximum refinement count is exhausted without clearance

## Output Conventions

- Plans must use `templates/plan.md`
- Drafts must use `templates/draft.md`
- Review reports must use `templates/review-report.md`
- Refinement logs must use `templates/revision-log.md`

These templates expose machine-readable frontmatter that the orchestrator validates.
