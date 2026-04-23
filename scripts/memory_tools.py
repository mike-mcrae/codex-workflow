#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent.parent
DECISIONS_DIR = ROOT / "decisions"
SESSION_LOG = ROOT / "memory/session-log.md"
DECISION_TEMPLATE = ROOT / "templates/decision-log.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def slugify(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-") or "decision"


def new_decision(args: argparse.Namespace) -> int:
    today = datetime.now().strftime("%Y-%m-%d")
    slug = slugify(args.topic)
    path = DECISIONS_DIR / f"{today}-{slug}.md"
    if path.exists():
        raise SystemExit(f"Decision already exists: {path}")

    content = read_text(DECISION_TEMPLATE)
    content = re.sub(r"^date:\s*$", f"date: {today}", content, flags=re.MULTILINE)
    content = re.sub(r"^topic:\s*$", f"topic: {args.topic}", content, flags=re.MULTILINE)
    write_text(path, content)
    print(path.relative_to(ROOT))
    return 0


def log_session(args: argparse.Namespace) -> int:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"## {timestamp}: {args.title}",
        "",
        f"- Summary: {args.summary}",
        f"- Inputs used: {args.inputs}",
        f"- Outputs produced: {args.outputs}",
        f"- Decisions and rationale: {args.decisions}",
        f"- Open items: {args.open_items}",
        f"- Next recommended action: {args.next_action}",
        "",
    ]
    existing = read_text(SESSION_LOG).rstrip() + "\n\n"
    write_text(SESSION_LOG, existing + "\n".join(lines))
    print(SESSION_LOG.relative_to(ROOT))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Helpers for layered memory maintenance")
    subparsers = parser.add_subparsers(dest="command", required=True)

    decision = subparsers.add_parser("new-decision", help="Create a dated decision record")
    decision.add_argument("--topic", required=True, help="Decision topic")
    decision.set_defaults(func=new_decision)

    log_cmd = subparsers.add_parser("log-session", help="Append a structured session-log entry")
    log_cmd.add_argument("--title", required=True)
    log_cmd.add_argument("--summary", required=True)
    log_cmd.add_argument("--inputs", required=True)
    log_cmd.add_argument("--outputs", required=True)
    log_cmd.add_argument("--decisions", required=True)
    log_cmd.add_argument("--open-items", required=True)
    log_cmd.add_argument("--next-action", required=True)
    log_cmd.set_defaults(func=log_session)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
