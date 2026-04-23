#!/usr/bin/env sh
set -eu

PROJECT_ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
LIVE_DIR="$PROJECT_ROOT/transcripts/live"
mkdir -p "$LIVE_DIR"

python3 "$PROJECT_ROOT/scripts/session_end_export.py" recover-live >/dev/null 2>&1 || true

SESSION_START="$(date '+%Y-%m-%dT%H:%M:%S')"
SESSION_ID="${CODEX_SESSION_ID:-$(date '+%Y%m%d-%H%M%S')}"
SESSION_TITLE="${CODEX_SESSION_TITLE:-Codex session}"
RUN_ID="${CODEX_RUN_ID:-}"
TAGS="${CODEX_SESSION_TAGS:-live-capture}"
RAW_FILE="$LIVE_DIR/$SESSION_ID.log"
META_FILE="$LIVE_DIR/$SESSION_ID.json"

cat > "$META_FILE" <<EOF
{
  "session_id": "$SESSION_ID",
  "title": "$SESSION_TITLE",
  "run_id": "$RUN_ID",
  "tags": [$(printf '"%s"' "$(printf "%s" "$TAGS" | sed 's/,/","/g')")],
  "source": "codex-live-capture",
  "started_at": "$SESSION_START"
}
EOF

cleanup() {
  python3 "$PROJECT_ROOT/scripts/session_end_export.py" recover-live >/dev/null 2>&1 || true
}

trap cleanup EXIT HUP INT TERM

if [ "$#" -eq 0 ]; then
  set -- codex
fi

if script --version >/dev/null 2>&1; then
  CMD_STR=""
  for arg in "$@"; do
    escaped=$(printf "%s" "$arg" | sed "s/'/'\\\\''/g")
    if [ -n "$CMD_STR" ]; then
      CMD_STR="$CMD_STR "
    fi
    CMD_STR="$CMD_STR'$escaped'"
  done
  script -q -f "$RAW_FILE" -c "$CMD_STR"
else
  script -q "$RAW_FILE" "$@"
fi
