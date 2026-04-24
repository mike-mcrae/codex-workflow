# Adoption Protocol

Use this when converting an existing project into the Codex workflow.

## Core Rule

Never restructure the original project in place during first adoption.

Create a reviewable copy, archive the original project contents into hidden migration state inside that copy, and normalize the new version around the canonical academic surface.

## Expected Flow

1. Create a cleaned subdirectory inside the original project root.
2. Install the workflow into that cleaned copy.
3. Preserve a full copy of the original source under `.workflow/state/migration/source-snapshot/`.
4. Import the original project into the canonical top-level academic structure:
   - `data/`
   - `scripts/`
   - `output/`
   - `manuscript/`
   - `notes/`
5. Rewrite project paths so migrated empirical code and manuscript files point at the new structure.
6. Archive legacy workflow and agent materials under `.workflow/state/migration/legacy-agent-material/`.
7. Route excluded app or web material under `.workflow/state/migration/excluded/`.
8. Convert useful imported notes into the four-layer memory layout:
   - Layer 1: `.workflow/memory/MEMORY.md`
   - Layer 2: `.workflow/decisions/`
   - Layer 3: `.workflow/memory/session-log.md`
   - Layer 4: leave transcript import empty unless true raw transcripts exist
9. Write migration memory and a migration report.

## Special Instructions

The adoption path should ask for:

- optional special instructions
- optional preserve/exclude globs

Special instructions should be written into the migrated project memory and report even if the tool cannot translate every instruction into automatic path rules.

## Safety

- preserve the old project inside the new cleaned repo, but keep it hidden from the researcher-facing top level
- prefer canonical placement plus explicit rewrites over visible compatibility links
- route unresolved conflicts into `.workflow/state/migration/conflicts/`
- let the user inspect the cleaned copy before treating it as the working repo
