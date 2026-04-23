# Adoption Protocol

Use this when converting an existing project into the Codex workflow.

## Core Rule

Never restructure the original project in place during first adoption.

Create a reviewable copy, preserve the original project contents inside that copy, and normalize the new version around the preserved source material.

## Expected Flow

1. Create a cleaned subdirectory inside the original project root.
2. Install the workflow into that cleaned copy.
3. Preserve a full copy of the original source under `preserved/source/`.
4. Import the original project into the canonical top-level academic structure:
   - `data/`
   - `scripts/`
   - `output/`
   - `manuscript/`
   - `notes/`
5. Archive legacy workflow and agent materials under `.workflow/state/migration/legacy-agent-material/`.
6. Write migration memory and a migration report.
7. Create compatibility symlinks for changed top-level names where safe.

## Special Instructions

The adoption path should ask for:

- optional special instructions
- optional preserve/exclude globs

Special instructions should be written into the migrated project memory and report even if the tool cannot translate every instruction into automatic path rules.

## Safety

- preserve the old project inside the new cleaned repo
- prefer compatibility links over risky bulk rewrites
- route unresolved conflicts into `.workflow/state/migration/conflicts/`
- let the user inspect the cleaned copy before treating it as the working repo
