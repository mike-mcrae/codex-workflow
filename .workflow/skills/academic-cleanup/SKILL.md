---
name: academic-cleanup
description: Enforce the canonical academic project structure in this repo. Use when the user asks to clean up the repository, reorganize files into the standard layout, repair legacy template paths, or restore the hidden `.workflow` internals while preserving researcher-facing directories like `data`, `scripts`, `output`, `manuscript`, and `notes`.
---

# Academic Cleanup

Use this skill when the repository structure has drifted or when the user explicitly asks for cleanup or reorganization.

## Quick Start

1. Read `../../protocols/structure-protocol.md`.
2. Run:
   ```bash
   python3 .workflow/scripts/cleanup_structure.py check
   ```
3. If drift exists, run:
   ```bash
   python3 .workflow/scripts/cleanup_structure.py fix
   ```
4. Re-read any files reported as rewritten if later work depends on exact paths.

## What This Skill Protects

- researcher-facing work stays in `data/`, `scripts/`, `output/`, `manuscript/`, and `notes/`
- internal prompts, memory, state, and automation stay under `.workflow/`
- legacy paths are migrated conservatively
- textual path references are repaired after known moves

## Safety Rules

- do not move arbitrary research files unless their canonical destination is obvious
- do not overwrite divergent files silently
- report conflicts instead of forcing a destructive merge
- if a move could change execution behavior, verify the affected paths after repair
