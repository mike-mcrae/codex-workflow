# Transcript Archive

Layer 4 of the memory system: raw session archive for retrieval, not default context.

## Layout

- `.workflow/transcripts/raw/`: timestamped exported transcript files
- `.workflow/transcripts/index/search-index.json`: lightweight local search index
- `.workflow/transcripts/live/`: in-progress terminal captures awaiting recovery or export
- `.workflow/transcripts/hooks/session-end.example.sh`: example hook wrapper

## Recommended Automatic Mode

Start Codex through the launcher:

```bash
./.workflow/scripts/start_codex_session.sh
```

Or pass the command explicitly:

```bash
./.workflow/scripts/start_codex_session.sh codex
```

Why this is better than a pure session-end hook:

- the terminal session is captured continuously into `.workflow/transcripts/live/`
- on normal exit, the launcher automatically archives and indexes it
- if the session dies abruptly, the live capture remains on disk
- the next launcher start automatically recovers any leftover live capture and archives it

## Export A Session

From a file:

```bash
python3 .workflow/scripts/session_end_export.py export \
  --transcript /path/to/session.md \
  --title "Draft review session" \
  --session-id "abc123" \
  --run-id "20260423-paper-revision" \
  --tags "review,round-1"
```

From stdin:

```bash
cat /path/to/session.md | python3 .workflow/scripts/session_end_export.py export --stdin --title "Codex session"
```

## Rebuild The Index

```bash
python3 .workflow/scripts/session_end_export.py index
```

## Search Archived Sessions

```bash
python3 .workflow/scripts/session_end_export.py search --query "latex compile error bibtex"
```

Recover interrupted live captures manually if needed:

```bash
python3 .workflow/scripts/session_end_export.py recover-live
```
