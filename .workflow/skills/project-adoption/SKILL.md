---
name: project-adoption
description: Adopt an existing repository into this academic workflow without rewriting the original project in place. Use when converting a legacy project into the Codex workflow, creating a reviewable cleaned copy, preserving original files, normalizing structure, and archiving old agent or workflow materials.
---

# Project Adoption

Use this skill when migrating an existing project into the workflow.

## Quick Start

1. Read `../../protocols/adoption-protocol.md`.
2. Prefer `codex_clean` or `python3 .workflow/scripts/codex_clean.py`.
3. Preserve the source project in the cleaned copy.
4. Normalize the new copy into the canonical top-level research structure.
5. Review `.workflow/state/migration/report.md` before making the cleaned copy the active working repo.

## Rules

- do not rewrite the original project in place
- preserve special instructions in the migrated project memory
- archive legacy workflow or agent markdowns into migration state
- prefer compatibility symlinks over destructive path rewrites
- keep the cleaned copy reviewable
