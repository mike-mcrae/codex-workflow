# Transcript Archive

Layer 4 of the memory system: raw session archive for retrieval, not default context.

## Layout

- `transcripts/raw/`: timestamped exported transcript files
- `transcripts/index/search-index.json`: lightweight local search index
- `transcripts/live/`: in-progress terminal captures awaiting recovery/export
- `transcripts/hooks/session-end.example.sh`: example hook wrapper for Codex-style session-end export

## Recommended Automatic Mode

Start Codex through the launcher:

```bash
./scripts/start_codex_session.sh
```

Or pass the command explicitly:

```bash
./scripts/start_codex_session.sh codex
```

Why this is better than a pure session-end hook:

- the terminal session is captured continuously into `transcripts/live/`
- on normal exit, the launcher automatically archives and indexes it
- if the session dies abruptly, the live capture remains on disk
- the next launcher start automatically recovers any leftover live capture and archives it

## Export A Session

From a file:

```bash
python3 scripts/session_end_export.py export \
  --transcript /path/to/session.md \
  --title "Draft review session" \
  --session-id "abc123" \
  --run-id "20260423-paper-revision" \
  --tags "review,round-1"
```

From stdin:

```bash
cat /path/to/session.md | python3 scripts/session_end_export.py export --stdin --title "Codex session"
```

## Rebuild The Index

```bash
python3 scripts/session_end_export.py index
```

## Search Archived Sessions

```bash
python3 scripts/session_end_export.py search --query "latex compile error bibtex"
```

Recover interrupted live captures manually if needed:

```bash
python3 scripts/session_end_export.py recover-live
```

Recommended practice:

- keep transcripts out of normal prompt context
- search them only when you need exact prior commands, error strings, or wording
- if the user says "we did this before" or asks for an exact past setup step, search this layer before declaring the detail unavailable
- prefer the launcher for robustness, because it records continuously instead of waiting for clean session shutdown
- if your runtime supports hooks, you can still wire the example shell wrapper to session end for direct transcript exports

This implementation uses only the Python standard library. The search index is a lightweight local term index, not a vector store.
