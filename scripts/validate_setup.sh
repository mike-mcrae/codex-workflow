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
  config/project.toml \
  workflow/specification.md \
  workflow/memory-protocol.md \
  workspace/input/project-brief.md \
  workspace/input/source-notes.md \
  memory/MEMORY.md \
  scripts/orchestrate.py \
  scripts/start_codex_session.sh
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
