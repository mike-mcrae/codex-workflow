#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TRANSCRIPTS_DIR = ROOT / "transcripts"
RAW_DIR = TRANSCRIPTS_DIR / "raw"
INDEX_DIR = TRANSCRIPTS_DIR / "index"
LIVE_DIR = TRANSCRIPTS_DIR / "live"
INDEX_PATH = INDEX_DIR / "search-index.json"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def slugify(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-") or "session"


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9_./:-]+", text.lower())


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    metadata: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip()
    return metadata, text[end + 5 :]


def clean_terminal_capture(text: str) -> str:
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    cleaned = ansi_escape.sub("", text)
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", cleaned)
    cleaned = re.sub(r"^Script started on .*?\n", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\nScript done on .*?$", "", cleaned, flags=re.MULTILINE | re.DOTALL)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip() + "\n"


def transcript_files() -> list[Path]:
    return sorted(path for path in RAW_DIR.rglob("*.md") if path.is_file())


def parse_tags(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [tag.strip() for tag in raw.split(",") if tag.strip()]


def body_excerpt(text: str, limit: int = 240) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    return compact[:limit] + ("..." if len(compact) > limit else "")


def export_transcript_body(
    *,
    body: str,
    title: str,
    session_id: str,
    run_id: str,
    tags: list[str],
    source: str,
    exported_at: datetime | None = None,
) -> Path:
    if not body.strip():
        raise SystemExit("Transcript body is empty.")

    now = exported_at or datetime.now()
    day_dir = RAW_DIR / now.strftime("%Y-%m-%d")
    filename = f"{now.strftime('%H%M%S')}-{slugify(title)}.md"
    destination = day_dir / filename

    metadata = [
        "---",
        f"session_id: {session_id}",
        f"exported_at: {now.isoformat(timespec='seconds')}",
        f"title: {title}",
        f"run_id: {run_id}",
        f"tags: {', '.join(tags)}",
        f"source: {source}",
        "---",
        "",
        f"# {title}",
        "",
        body.strip(),
        "",
    ]
    write_text(destination, "\n".join(metadata))
    rebuild_index()
    return destination


def export_transcript(args: argparse.Namespace) -> int:
    if args.transcript and args.stdin:
        raise SystemExit("Use either `--transcript` or `--stdin`, not both.")

    if args.transcript:
        body = read_text(Path(args.transcript))
    elif args.stdin:
        body = sys.stdin.read()
    else:
        raise SystemExit("Provide transcript content with `--transcript` or `--stdin`.")

    title = args.title or "Codex session"
    now = datetime.now()
    session_id = args.session_id or now.strftime("%Y%m%d-%H%M%S")
    run_id = args.run_id or ""
    tags = parse_tags(args.tags)
    source = args.source
    if args.terminal_capture:
        body = clean_terminal_capture(body)
    destination = export_transcript_body(
        body=body,
        title=title,
        session_id=session_id,
        run_id=run_id,
        tags=tags,
        source=source,
        exported_at=now,
    )
    print(destination.relative_to(ROOT))
    return 0


def rebuild_index() -> dict:
    docs: list[dict] = []
    doc_freq: Counter[str] = Counter()

    for path in transcript_files():
        text = read_text(path)
        metadata, body = parse_frontmatter(text)
        tokens = tokenize(body)
        if not tokens:
            continue
        token_counts = Counter(tokens)
        for token in token_counts:
            doc_freq[token] += 1
        docs.append(
            {
                "path": str(path.relative_to(ROOT)),
                "title": metadata.get("title", path.stem),
                "session_id": metadata.get("session_id", ""),
                "exported_at": metadata.get("exported_at", ""),
                "run_id": metadata.get("run_id", ""),
                "tags": [tag.strip() for tag in metadata.get("tags", "").split(",") if tag.strip()],
                "token_counts": dict(token_counts),
                "excerpt": body_excerpt(body),
            }
        )

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "document_count": len(docs),
        "document_frequency": dict(doc_freq),
        "documents": docs,
    }
    write_json(INDEX_PATH, payload)
    return payload


def index_transcripts(_: argparse.Namespace) -> int:
    payload = rebuild_index()
    print(f"Indexed {payload['document_count']} transcript(s) into {INDEX_PATH.relative_to(ROOT)}")
    return 0


def recover_live(_: argparse.Namespace) -> int:
    LIVE_DIR.mkdir(parents=True, exist_ok=True)
    recovered = 0
    for meta_path in sorted(LIVE_DIR.glob("*.json")):
        raw_path = meta_path.with_suffix(".log")
        if not raw_path.exists():
            continue
        metadata = json.loads(read_text(meta_path))
        body = clean_terminal_capture(read_text(raw_path))
        if not body.strip():
            raw_path.unlink(missing_ok=True)
            meta_path.unlink(missing_ok=True)
            continue
        destination = export_transcript_body(
            body=body,
            title=metadata.get("title", "Recovered Codex session"),
            session_id=metadata.get("session_id", raw_path.stem),
            run_id=metadata.get("run_id", ""),
            tags=metadata.get("tags", []),
            source=metadata.get("source", "codex-live-capture"),
            exported_at=datetime.fromisoformat(metadata["started_at"]),
        )
        raw_path.unlink(missing_ok=True)
        meta_path.unlink(missing_ok=True)
        recovered += 1
        print(f"Recovered {destination.relative_to(ROOT)}")

    if recovered == 0:
        print("No live captures to recover.")
    else:
        rebuild_index()
    return 0


def search_index(args: argparse.Namespace) -> int:
    if not INDEX_PATH.exists():
        payload = rebuild_index()
    else:
        payload = json.loads(read_text(INDEX_PATH))

    query_tokens = tokenize(args.query)
    if not query_tokens:
        raise SystemExit("Query must contain searchable tokens.")

    documents = payload.get("documents", [])
    total_docs = max(payload.get("document_count", 0), 1)
    doc_freq = payload.get("document_frequency", {})
    scored: list[tuple[float, dict]] = []
    for doc in documents:
        token_counts = doc.get("token_counts", {})
        total_terms = sum(token_counts.values()) or 1
        score = 0.0
        for token in query_tokens:
            tf = token_counts.get(token, 0)
            if not tf:
                continue
            idf = math.log((1 + total_docs) / (1 + int(doc_freq.get(token, 0)))) + 1
            score += (tf / total_terms) * idf
        if score > 0:
            scored.append((score, doc))

    scored.sort(key=lambda item: item[0], reverse=True)
    top = scored[: args.limit]
    if not top:
        print("No transcript hits.")
        return 0

    for rank, (score, doc) in enumerate(top, start=1):
        print(f"{rank}. {doc['title']} [{doc['path']}] score={score:.4f}")
        if doc.get("session_id"):
            print(f"   session_id: {doc['session_id']}")
        if doc.get("run_id"):
            print(f"   run_id: {doc['run_id']}")
        if doc.get("tags"):
            print("   tags: " + ", ".join(doc["tags"]))
        print("   excerpt: " + doc.get("excerpt", ""))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Codex session-end transcript export and local indexing"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    export = subparsers.add_parser("export", help="Export one transcript and rebuild the local index")
    export.add_argument("--transcript", help="Path to a markdown/text transcript file")
    export.add_argument("--stdin", action="store_true", help="Read transcript content from stdin")
    export.add_argument("--terminal-capture", action="store_true", help="Clean ANSI/script output from a terminal capture before archiving")
    export.add_argument("--title", help="Human-readable session title")
    export.add_argument("--session-id", help="Runtime session identifier")
    export.add_argument("--run-id", help="Workflow run identifier, if relevant")
    export.add_argument("--tags", help="Comma-separated tags")
    export.add_argument("--source", default="codex", help="Transcript source label")
    export.set_defaults(func=export_transcript)

    index_cmd = subparsers.add_parser("index", help="Rebuild the transcript search index")
    index_cmd.set_defaults(func=index_transcripts)

    search_cmd = subparsers.add_parser("search", help="Search archived transcripts")
    search_cmd.add_argument("--query", required=True, help="Search terms")
    search_cmd.add_argument("--limit", type=int, default=5, help="Maximum results to show")
    search_cmd.set_defaults(func=search_index)

    recover_cmd = subparsers.add_parser("recover-live", help="Recover any live session captures left by abrupt termination")
    recover_cmd.set_defaults(func=recover_live)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
