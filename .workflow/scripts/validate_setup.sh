#!/usr/bin/env sh
set -eu

missing=0

check_cmd() {
  if command -v "$1" >/dev/null 2>&1; then
    printf "OK   %s -> %s\n" "$1" "$(command -v "$1")"
  else
    printf "MISS %s\n" "$1"
    missing=1
  fi
}

printf "Checking local prerequisites for Codex Academic Workflow\n"
check_cmd python3
check_cmd git
check_cmd codex
check_cmd script

printf "\nChecking repository paths\n"
for path in \
  .workflow/config/project.toml \
  .workflow/protocols/intake-protocol.md \
  .workflow/protocols/structure-protocol.md \
  .workflow/protocols/specification.md \
  .workflow/protocols/memory-protocol.md \
  .workflow/memory/MEMORY.md \
  .workflow/scripts/bootstrap_project.py \
  .workflow/scripts/code_audit.py \
  .workflow/scripts/cleanup_structure.py \
  .workflow/scripts/orchestrate.py \
  .workflow/scripts/start_codex_session.sh \
  notes/project-brief.md \
  notes/source-notes.md \
  manuscript/main.tex \
  data/raw \
  data/derived \
  data/external \
  scripts/python \
  scripts/stata \
  scripts/r \
  output/figures \
  output/tables \
  output/logs
do
  if [ -e "$path" ]; then
    printf "OK   %s\n" "$path"
  else
    printf "MISS %s\n" "$path"
    missing=1
  fi
done

if [ "$missing" -ne 0 ]; then
  printf "\nSetup check failed.\n"
  exit 1
fi

printf "\nSetup check passed.\n"
