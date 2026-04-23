#!/usr/bin/env sh
set -eu

# Example wrapper for a Codex-compatible session-end hook.
# Adapt the environment variables and transcript source to whatever your runtime exposes.
#
# Example patterns:
# - if the runtime writes the transcript to a temporary file, pass --transcript "$TRANSCRIPT_PATH"
# - if the runtime pipes transcript text to the hook, replace the final line with:
#   python3 scripts/session_end_export.py export --stdin --title "Codex session" --session-id "${SESSION_ID:-}" --run-id "${RUN_ID:-}" --tags "session-end"

PROJECT_ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"
TRANSCRIPT_PATH="${1:-}"

if [ -z "$TRANSCRIPT_PATH" ]; then
  echo "Usage: $0 /path/to/transcript.md" >&2
  exit 1
fi

cd "$PROJECT_ROOT"
python3 scripts/session_end_export.py export \
  --transcript "$TRANSCRIPT_PATH" \
  --title "${CODEX_SESSION_TITLE:-Codex session}" \
  --session-id "${CODEX_SESSION_ID:-}" \
  --run-id "${CODEX_RUN_ID:-}" \
  --tags "${CODEX_SESSION_TAGS:-session-end}" \
  --source "codex-hook"
