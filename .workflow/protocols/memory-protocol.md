# Memory Protocol

This workflow uses a four-layer memory model so the agent can distinguish what should be auto-read from what should be retrieved only when needed.

## Layer 1: Curated Always-Read Memory

Files:

- `.workflow/memory/MEMORY.md`
- `.workflow/memory/topics/*.md`

Purpose:

- stable project facts
- durable writing rules
- non-negotiable preferences
- recurring claims discipline

Rules:

- keep this concise
- update it when a correction should survive many sessions
- do not turn it into a diary
- if a note is narrow, move it into a topic file instead of bloating `.workflow/memory/MEMORY.md`
- if `.workflow/memory/MEMORY.md` grows beyond roughly 200 lines, replace detail with one-line pointers into `.workflow/memory/topics/*.md`
- use `.workflow/memory/MEMORY.md` as an index when possible, not as a dump

## Layer 2: Decision Records

Files:

- `.workflow/decisions/YYYY-MM-DD-topic.md`
- `.workflow/decisions/INDEX.md`

Purpose:

- preserve why a choice was made
- record alternatives considered and rejected
- avoid re-litigating settled tradeoffs

Rules:

- one decision per file
- append new decisions instead of rewriting old rationale
- cite these files on demand, not by default
- if a decision is replaced, keep the old file and mark it as superseded

## Layer 3: Rolling Session Log

File:

- `.workflow/memory/session-log.md`

Purpose:

- resume work quickly
- capture what shipped, what inputs were used, and what remains open

Rules:

- read the most recent entries at the start of substantive work
- in practice, read the latest 3 to 5 entries unless there is a reason to go further back
- append a new structured entry at the end of a session or major block of work
- keep it current, but do not treat it as permanent doctrine

## Layer 4: Raw Transcript Archive

Files:

- `.workflow/transcripts/`

Purpose:

- searchable long-tail memory for exact commands, errors, and prior wording

Rules:

- never auto-load this layer into normal context
- search it only when exact recovery matters
- store exports in dated files so retrieval stays traceable
- if the user says "we did this before" or asks for an exact prior command or error, search Layer 4 first
- use `python3 .workflow/scripts/session_end_export.py search --query "..."`

## Layer Linkage Rule

Pointers are cheap. Duplication is debt.

- summarize settled state in Layer 1 and point to Layer 2 when rationale matters
- summarize recent work in Layer 3 and point to Layer 2 when a major decision was promoted
- keep Layer 4 as the long-tail source of last resort rather than copying transcript detail upward

## Agent Behavior

When activated, the agent should:

1. Read `.workflow/protocols/memory-protocol.md`.
2. Read Layer 1 and Layer 3 before substantive work.
3. Use Layer 2 only if a previously settled question resurfaces.
4. Treat Layer 4 as retrieval-only evidence, not default context.
5. Add new durable rules to Layer 1, new settled tradeoffs to Layer 2, and current-state notes to Layer 3.
6. Search Layer 4 before concluding exact prior details are unavailable.
