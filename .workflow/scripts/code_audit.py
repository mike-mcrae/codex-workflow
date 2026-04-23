#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_SPEC = ROOT / ".workflow/protocols/specification.md"
QUALITY_GATES = ROOT / ".workflow/config/quality_gates.toml"
MEMORY_PROTOCOL = ROOT / ".workflow/protocols/memory-protocol.md"
MEMORY_PATH = ROOT / ".workflow/memory/MEMORY.md"
SESSION_LOG = ROOT / ".workflow/memory/session-log.md"
DECISIONS_INDEX = ROOT / ".workflow/decisions/INDEX.md"
PACKET_TEMPLATE = ROOT / ".workflow/prompts/code-audit.md"
REPORT_TEMPLATE = ROOT / ".workflow/templates/code-review-report.md"
AUDITS_DIR = ROOT / ".workflow/state/audits"

AGENT_BY_LANGUAGE = {
    "python": ROOT / ".workflow/agents/python-reviewer.md",
    "stata": ROOT / ".workflow/agents/stata-reviewer.md",
    "r": ROOT / ".workflow/agents/r-reviewer.md",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def relative_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def infer_language(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".py":
        return "python"
    if suffix == ".do":
        return "stata"
    if suffix == ".r":
        return "r"
    raise SystemExit("Cannot infer language. Use a .py, .do, or .R file.")


def slugify(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-") or "audit"


def stamped_template(template_path: Path, replacements: dict[str, str]) -> str:
    content = read_text(template_path)
    for key, value in replacements.items():
        content = re.sub(rf"^{re.escape(key)}:\s*$", f"{key}: {value}", content, flags=re.MULTILINE)
    return content


def render_prompt(context: dict[str, str]) -> str:
    class SafeDict(dict):
        def __missing__(self, key: str) -> str:
            return "{" + key + "}"

    return read_text(PACKET_TEMPLATE).format_map(SafeDict(context))


def prepare(args: argparse.Namespace) -> int:
    target = Path(args.file)
    if not target.is_absolute():
        target = (ROOT / target).resolve()
    if not target.exists():
        raise SystemExit(f"Target file not found: {target}")

    language = args.language or infer_language(target)
    if language not in AGENT_BY_LANGUAGE:
        raise SystemExit(f"Unsupported language: {language}")

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    audit_dir = AUDITS_DIR / f"{stamp}-{slugify(target.stem)}-{language}"
    report_path = audit_dir / "report.md"
    packet_path = audit_dir / "packet.md"

    report = stamped_template(
        REPORT_TEMPLATE,
        {
            "language": language,
            "agent": Path(AGENT_BY_LANGUAGE[language]).stem,
            "target_file": relative_path(target),
            "created_at": datetime.now().isoformat(timespec="seconds"),
        },
    )
    write_text(report_path, report)

    packet = render_prompt(
        {
            "agent_definition_path": relative_path(AGENT_BY_LANGUAGE[language]),
            "workflow_spec_path": relative_path(WORKFLOW_SPEC),
            "quality_gates_path": relative_path(QUALITY_GATES),
            "memory_protocol_path": relative_path(MEMORY_PROTOCOL),
            "memory_path": relative_path(MEMORY_PATH),
            "session_log_path": relative_path(SESSION_LOG),
            "decisions_index_path": relative_path(DECISIONS_INDEX),
            "target_file_path": relative_path(target),
            "output_path": relative_path(report_path),
            "report_template_path": relative_path(REPORT_TEMPLATE),
            "language": language,
        }
    )
    write_text(packet_path, packet)

    print(relative_path(packet_path))
    print(relative_path(report_path))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare language-specific code audit packets")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare_cmd = subparsers.add_parser("prepare", help="Prepare a code audit packet and report stub")
    prepare_cmd.add_argument("--file", required=True, help="Target code file")
    prepare_cmd.add_argument("--language", choices=["python", "stata", "r"], help="Override inferred language")
    prepare_cmd.set_defaults(func=prepare)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
