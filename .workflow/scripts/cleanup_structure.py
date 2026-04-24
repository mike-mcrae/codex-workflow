#!/usr/bin/env python3
from __future__ import annotations

import argparse
import filecmp
import re
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

CANONICAL_DIRS = [
    ROOT / "data/raw",
    ROOT / "data/derived",
    ROOT / "data/external",
    ROOT / "scripts/python",
    ROOT / "scripts/stata",
    ROOT / "scripts/r",
    ROOT / "scripts/shell",
    ROOT / "output/figures",
    ROOT / "output/tables",
    ROOT / "output/logs",
    ROOT / "manuscript/bibliography",
    ROOT / "manuscript/figures",
    ROOT / "manuscript/sections",
    ROOT / "notes",
    ROOT / ".workflow/agents",
    ROOT / ".workflow/config",
    ROOT / ".workflow/decisions",
    ROOT / ".workflow/memory/topics",
    ROOT / ".workflow/prompts",
    ROOT / ".workflow/protocols",
    ROOT / ".workflow/scripts",
    ROOT / ".workflow/skills",
    ROOT / ".workflow/state/runs",
    ROOT / ".workflow/state/audits",
    ROOT / ".workflow/templates",
    ROOT / ".workflow/transcripts/raw",
    ROOT / ".workflow/transcripts/live",
    ROOT / ".workflow/transcripts/index",
]

WHOLE_DIR_MOVES = {
    "agents": ".workflow/agents",
    "config": ".workflow/config",
    "decisions": ".workflow/decisions",
    "memory": ".workflow/memory",
    "prompts": ".workflow/prompts",
    "templates": ".workflow/templates",
    "transcripts": ".workflow/transcripts",
    "workflow": ".workflow/protocols",
    "paper": "manuscript",
}

FILE_MOVES = {
    "workspace/input/project-brief.md": "notes/project-brief.md",
    "workspace/input/source-notes.md": "notes/source-notes.md",
    "workspace/runs/.gitkeep": ".workflow/state/runs/.gitkeep",
    "workspace/audits/.gitkeep": ".workflow/state/audits/.gitkeep",
}

DIR_MOVES = {
    "workspace/runs": ".workflow/state/runs",
    "workspace/audits": ".workflow/state/audits",
}

LEGACY_INTERNAL_SCRIPTS = {
    "bootstrap_project.py",
    "code_audit.py",
    "memory_tools.py",
    "new_project.py",
    "orchestrate.py",
    "session_end_export.py",
    "start_codex_session.sh",
    "validate_setup.sh",
    "cleanup_structure.py",
}

TEXT_EXTENSIONS = {
    ".bib",
    ".do",
    ".json",
    ".md",
    ".py",
    ".R",
    ".r",
    ".sh",
    ".tex",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}

REPLACEMENTS = [
    (r"workspace/input/project-brief\.md", "notes/project-brief.md"),
    (r"workspace/input/source-notes\.md", "notes/source-notes.md"),
    (r"workspace/runs/", ".workflow/state/runs/"),
    (r"workspace/audits/", ".workflow/state/audits/"),
    (r"paper/main\.tex", "manuscript/main.tex"),
    (r"paper/sections/", "manuscript/sections/"),
    (r"paper/figures/", "manuscript/figures/"),
    (r"paper/bibliography/", "manuscript/bibliography/"),
    (r"(?<!\.)workflow/specification\.md", ".workflow/protocols/specification.md"),
    (r"(?<!\.)workflow/memory-protocol\.md", ".workflow/protocols/memory-protocol.md"),
    (r"(?<!\.)workflow/intake-protocol\.md", ".workflow/protocols/intake-protocol.md"),
    (r"(?<!\.)workflow/structure-protocol\.md", ".workflow/protocols/structure-protocol.md"),
    (r"(?<!\.workflow/)config/project\.toml", ".workflow/config/project.toml"),
    (r"(?<!\.workflow/)config/quality_gates\.toml", ".workflow/config/quality_gates.toml"),
    (r"(?<!\.workflow/)memory/MEMORY\.md", ".workflow/memory/MEMORY.md"),
    (r"(?<!\.workflow/)memory/session-log\.md", ".workflow/memory/session-log.md"),
    (r"(?<!\.workflow/)memory/topics/", ".workflow/memory/topics/"),
    (r"(?<!\.workflow/)decisions/INDEX\.md", ".workflow/decisions/INDEX.md"),
    (r"(?<!\.workflow/)scripts/bootstrap_project\.py", ".workflow/scripts/bootstrap_project.py"),
    (r"(?<!\.workflow/)scripts/code_audit\.py", ".workflow/scripts/code_audit.py"),
    (r"(?<!\.workflow/)scripts/cleanup_structure\.py", ".workflow/scripts/cleanup_structure.py"),
    (r"(?<!\.workflow/)scripts/memory_tools\.py", ".workflow/scripts/memory_tools.py"),
    (r"(?<!\.workflow/)scripts/new_project\.py", ".workflow/scripts/new_project.py"),
    (r"(?<!\.workflow/)scripts/orchestrate\.py", ".workflow/scripts/orchestrate.py"),
    (r"(?<!\.workflow/)scripts/session_end_export\.py", ".workflow/scripts/session_end_export.py"),
    (r"(?<!\.workflow/)scripts/start_codex_session\.sh", ".workflow/scripts/start_codex_session.sh"),
    (r"(?<!\.workflow/)scripts/validate_setup\.sh", ".workflow/scripts/validate_setup.sh"),
    (r"(?<!\.workflow/)transcripts/README\.md", ".workflow/transcripts/README.md"),
]

SKIP_PARTS = {".git", "__pycache__"}
SKIP_FILES = {
    ROOT / ".workflow/scripts/cleanup_structure.py",
    ROOT / ".workflow/protocols/structure-protocol.md",
}


def iter_text_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        if path in SKIP_FILES:
            continue
        if path.suffix not in TEXT_EXTENSIONS:
            continue
        files.append(path)
    return files


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def try_read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def merge_directory(src: Path, dst: Path, operations: list[str], conflicts: list[str]) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for child in sorted(src.iterdir(), key=lambda item: item.name):
        target = dst / child.name
        if child.is_dir():
            if target.exists() and target.is_dir():
                merge_directory(child, target, operations, conflicts)
                if child.exists() and not any(child.iterdir()):
                    child.rmdir()
            elif target.exists():
                conflicts.append(f"Directory move conflict: {src} -> {target}")
            else:
                shutil.move(str(child), str(target))
                operations.append(f"Moved {child.relative_to(ROOT)} -> {target.relative_to(ROOT)}")
        else:
            if target.exists():
                same = False
                if target.is_file():
                    same = filecmp.cmp(child, target, shallow=False)
                if same:
                    child.unlink()
                else:
                    conflicts.append(f"File move conflict: {child.relative_to(ROOT)} -> {target.relative_to(ROOT)}")
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(child), str(target))
                operations.append(f"Moved {child.relative_to(ROOT)} -> {target.relative_to(ROOT)}")
    if src.exists() and src.is_dir() and not any(src.iterdir()):
        src.rmdir()


def move_path(src: Path, dst: Path, operations: list[str], conflicts: list[str]) -> None:
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        if dst.exists() and dst.is_dir():
            merge_directory(src, dst, operations, conflicts)
            if src.exists() and not any(src.iterdir()):
                src.rmdir()
            return
        if dst.exists():
            conflicts.append(f"Directory move conflict: {src.relative_to(ROOT)} -> {dst.relative_to(ROOT)}")
            return
        shutil.move(str(src), str(dst))
        operations.append(f"Moved {src.relative_to(ROOT)} -> {dst.relative_to(ROOT)}")
        return

    if dst.exists():
        same = dst.is_file() and filecmp.cmp(src, dst, shallow=False)
        if same:
            src.unlink()
        else:
            conflicts.append(f"File move conflict: {src.relative_to(ROOT)} -> {dst.relative_to(ROOT)}")
        return

    shutil.move(str(src), str(dst))
    operations.append(f"Moved {src.relative_to(ROOT)} -> {dst.relative_to(ROOT)}")


def ensure_dirs(operations: list[str]) -> None:
    for path in CANONICAL_DIRS:
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            operations.append(f"Created {path.relative_to(ROOT)}/")


def move_legacy_internal_scripts(operations: list[str], conflicts: list[str]) -> None:
    legacy_scripts_dir = ROOT / "scripts"
    if not legacy_scripts_dir.exists():
        return
    for name in sorted(LEGACY_INTERNAL_SCRIPTS):
        src = legacy_scripts_dir / name
        if src.exists():
            move_path(src, ROOT / ".workflow/scripts" / name, operations, conflicts)


def rewrite_text_references(operations: list[str]) -> None:
    for path in iter_text_files(ROOT):
        original = try_read_text(path)
        if original is None:
            continue
        updated = original
        for pattern, replacement in REPLACEMENTS:
            updated = re.sub(pattern, replacement, updated)
        if updated != original:
            write_text(path, updated)
            operations.append(f"Rewrote references in {path.relative_to(ROOT)}")


def detect_problems() -> list[str]:
    problems: list[str] = []
    for path in CANONICAL_DIRS:
        if not path.exists():
            problems.append(f"Missing canonical path: {path.relative_to(ROOT)}")

    for src_rel, dst_rel in WHOLE_DIR_MOVES.items():
        src = ROOT / src_rel
        if src.exists() and not src.is_symlink():
            problems.append(f"Legacy directory present: {src_rel} (expected under {dst_rel})")

    for src_rel, dst_rel in DIR_MOVES.items():
        src = ROOT / src_rel
        if src.exists() and not src.is_symlink():
            problems.append(f"Legacy directory present: {src_rel} (expected under {dst_rel})")

    for src_rel, dst_rel in FILE_MOVES.items():
        src = ROOT / src_rel
        if src.exists():
            problems.append(f"Legacy file present: {src_rel} (expected at {dst_rel})")

    for name in sorted(LEGACY_INTERNAL_SCRIPTS):
        src = ROOT / "scripts" / name
        if src.exists():
            problems.append(f"Legacy internal script present at researcher path: scripts/{name}")

    for path in iter_text_files(ROOT):
        content = try_read_text(path)
        if content is None:
            continue
        for pattern, _replacement in REPLACEMENTS:
            if re.search(pattern, content):
                problems.append(f"Stale path reference in {path.relative_to(ROOT)}: {pattern}")
                break

    return problems


def fix_structure() -> tuple[list[str], list[str]]:
    operations: list[str] = []
    conflicts: list[str] = []

    ensure_dirs(operations)
    move_legacy_internal_scripts(operations, conflicts)

    for src_rel, dst_rel in FILE_MOVES.items():
        move_path(ROOT / src_rel, ROOT / dst_rel, operations, conflicts)

    for src_rel, dst_rel in DIR_MOVES.items():
        move_path(ROOT / src_rel, ROOT / dst_rel, operations, conflicts)

    for src_rel, dst_rel in WHOLE_DIR_MOVES.items():
        move_path(ROOT / src_rel, ROOT / dst_rel, operations, conflicts)

    rewrite_text_references(operations)
    return operations, conflicts


def main() -> int:
    parser = argparse.ArgumentParser(description="Check or repair the canonical academic project structure")
    parser.add_argument("command", choices=["check", "fix"], help="Whether to report structure drift or repair it")
    args = parser.parse_args()

    if args.command == "check":
        problems = detect_problems()
        if not problems:
            print("Structure check passed.")
            return 0
        print("Structure drift detected:")
        for problem in problems:
            print(f"- {problem}")
        return 1

    operations, conflicts = fix_structure()
    if operations:
        print("Applied structure fixes:")
        for item in operations:
            print(f"- {item}")
    else:
        print("No structure fixes were needed.")

    if conflicts:
        print("Conflicts requiring manual review:", file=sys.stderr)
        for item in conflicts:
            print(f"- {item}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
