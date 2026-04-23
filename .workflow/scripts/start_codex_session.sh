#!/usr/bin/env sh
set -eu

PROJECT_ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"
LIVE_DIR="$PROJECT_ROOT/.workflow/transcripts/live"
STRUCTURE_CHECKER="$PROJECT_ROOT/.workflow/scripts/cleanup_structure.py"
PROJECT_CONFIG="$PROJECT_ROOT/.workflow/config/project.toml"
mkdir -p "$LIVE_DIR"

python3 "$PROJECT_ROOT/.workflow/scripts/session_end_export.py" recover-live >/dev/null 2>&1 || true

if ! python3 "$STRUCTURE_CHECKER" check >/dev/null 2>&1; then
  printf "Structure drift detected. Applying automatic repair before starting Codex.\n" >&2
  python3 "$STRUCTURE_CHECKER" fix >/dev/null
  python3 "$STRUCTURE_CHECKER" check >/dev/null
fi

UNSAFE_MODE="$(PROJECT_CONFIG_PATH="$PROJECT_CONFIG" python3 - <<'PY'
from pathlib import Path
import os
import tomllib

path = Path(os.environ["PROJECT_CONFIG_PATH"])
if not path.exists():
    print("false")
else:
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    value = data.get("workflow", {}).get("dangerously_bypass_approvals_and_sandbox", False)
    print("true" if value else "false")
PY
)"

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
  python3 "$PROJECT_ROOT/.workflow/scripts/session_end_export.py" recover-live >/dev/null 2>&1 || true
}

trap cleanup EXIT HUP INT TERM

if [ "$#" -eq 0 ]; then
  set -- codex
fi

CMD_NAME="$(basename -- "$1")"

if [ "$UNSAFE_MODE" = "true" ] && [ "$#" -gt 0 ] && [ "$CMD_NAME" = "codex" ]; then
  cmd="$1"
  shift
  set -- "$cmd" "--dangerously-bypass-approvals-and-sandbox" "$@"
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
