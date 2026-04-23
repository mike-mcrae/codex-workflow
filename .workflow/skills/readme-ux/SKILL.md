---
name: readme-ux
description: Improve public-facing repository documentation, especially README files, so they are user-first, fork-friendly, and clear about what the user should do, what the agent will do, and which setup steps are optional personal automation rather than part of the public template.
---

# README UX

Use this skill when rewriting or reviewing public-facing documentation for this workflow.

## Goals

- lead with the user journey, not the internal architecture
- make forking and first use obvious
- separate public template behavior from the maintainer's personal machine setup
- explain what the agent actually does after the starter prompt
- keep internal implementation detail available but secondary

## README Order

1. What this repo is
2. Quick start for a new user
3. Starter prompt or first-session entrypoint
4. What the agent will do
5. Researcher-facing project structure
6. Automatic maintenance and safety behavior
7. Optional personal automation
8. Links to deeper setup docs

## Writing Rules

- assume the reader is seeing the repo on GitHub for the first time
- avoid leading with local machine-specific commands unless clearly labeled optional
- prefer short sections and flat bullets
- tell the user what is automatic and what they must do manually
- describe the workflow in user terms such as plan, draft, review, refine, verify
- keep `.workflow/` mostly out of the opening sections except to explain that internal machinery is hidden there

## Required Clarity

The README should answer these questions quickly:

- What happens if I fork this repo?
- What do I need installed?
- What do I type first?
- What happens after I paste the starter prompt?
- Where do my data, scripts, outputs, and manuscript files go?
- Which features are optional personal automation rather than part of the template itself?
