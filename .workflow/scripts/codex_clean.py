#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import filecmp
import fnmatch
import os
import re
import shutil
import subprocess
import textwrap
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


TEMPLATE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DEST_NAME = "codex_cleaned"
IGNORE_NAMES = {
    ".git",
    "__pycache__",
    ".DS_Store",
}
TEXT_EXTENSIONS = {
    ".bib",
    ".cls",
    ".csv",
    ".do",
    ".json",
    ".md",
    ".py",
    ".R",
    ".r",
    ".Rmd",
    ".sh",
    ".tex",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
CODE_EXTENSIONS = {
    ".py",
    ".do",
    ".ado",
    ".R",
    ".r",
    ".Rmd",
    ".ipynb",
    ".sh",
    ".bash",
    ".zsh",
    ".jl",
    ".m",
}
DATA_EXTENSIONS = {
    ".csv",
    ".dta",
    ".xlsx",
    ".xls",
    ".parquet",
    ".feather",
    ".rds",
    ".rdata",
    ".sav",
    ".tsv",
    ".txt",
    ".zip",
    ".gz",
    ".bz2",
    ".xz",
    ".sqlite",
    ".db",
    ".json",
}
MANUSCRIPT_EXTENSIONS = {
    ".tex",
    ".bib",
    ".docx",
    ".doc",
    ".pdf",
    ".cls",
    ".bst",
}
FIGURE_EXTENSIONS = {
    ".png",
    ".svg",
    ".jpg",
    ".jpeg",
    ".pdf",
    ".eps",
    ".tif",
    ".tiff",
}
LOG_EXTENSIONS = {
    ".log",
    ".out",
}
DOC_EXTENSIONS = {
    ".md",
    ".txt",
    ".docx",
}
LEGACY_AGENT_KEYWORDS = {
    "agent",
    "agents",
    "prompt",
    "prompts",
    "workflow",
    "memory",
    "instruction",
    "instructions",
    "claude",
    "codex",
    "review",
    "planner",
}
APP_RELATED_NAMES = {
    "app",
    "apps",
    "frontend",
    "backend",
    "mobile",
    "ios",
    "android",
    "web",
    "client",
    "server",
    "ui",
}
CANONICAL_ROOTS = {"data", "scripts", "output", "manuscript", "notes"}
REWRITE_EXTENSIONS = {
    ".md",
    ".txt",
    ".toml",
    ".tex",
    ".py",
    ".sh",
    ".do",
    ".R",
    ".r",
    ".yaml",
    ".yml",
    ".json",
}
LARGE_FILE_BYTES = 10 * 1024 * 1024


@dataclass
class MappingRecord:
    source_rel: str
    destination_rel: str
    category: str
    mode: str
    notes: str = ""


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


def prompt(label: str, default: str = "", required: bool = False) -> str:
    suffix = f" [{default}]" if default else ""
    if not os.isatty(0):
        if default or not required:
            return default
        raise SystemExit(f"Missing required interactive input: {label}")
    while True:
        value = input(f"{label}{suffix}: ").strip()
        if value:
            return value
        if default:
            return default
        if not required:
            return ""


def prompt_yes_no(label: str, default: bool = False) -> bool:
    suffix = " [Y/n]" if default else " [y/N]"
    if not os.isatty(0):
        return default
    while True:
        value = input(f"{label}{suffix}: ").strip().lower()
        if not value:
            return default
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "_", value.strip())
    slug = re.sub(r"_+", "_", slug).strip("._-")
    return slug or DEFAULT_DEST_NAME


def shell(cmd: list[str], cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)


def copy_template(destination: Path) -> None:
    ignore_names = shutil.ignore_patterns(
        ".git",
        "__pycache__",
        "instructions.md",
        "memory_instructions.md",
    )
    shutil.copytree(TEMPLATE_ROOT, destination, ignore=ignore_names)
    for transient in [
        destination / ".workflow" / "state" / "runs",
        destination / ".workflow" / "state" / "audits",
        destination / ".workflow" / "transcripts" / "raw",
        destination / ".workflow" / "transcripts" / "live",
    ]:
        if transient.exists():
            for child in transient.iterdir():
                if child.name == ".gitkeep":
                    continue
                if child.is_dir():
                    shutil.rmtree(child)
                else:
                    child.unlink()
    index_file = destination / ".workflow" / "transcripts" / "index" / "search-index.json"
    if index_file.exists():
        index_file.unlink()


def set_section_value(text: str, heading: str, value: str) -> str:
    pattern = rf"(## {re.escape(heading)}\n)(.*?)(\n## |\Z)"
    match = re.search(pattern, text, flags=re.DOTALL)
    if not match:
        return text
    body = value.strip()
    replacement = f"{match.group(1)}\n{body}\n{match.group(3)}"
    return text[: match.start()] + replacement + text[match.end() :]


def implied_exclude_globs(special_instructions: str) -> list[str]:
    text = special_instructions.lower()
    if "app" not in text:
        return []
    triggers = {"disregard", "ignore", "leave", "remain", "untouched", "not related"}
    if not any(trigger in text for trigger in triggers):
        return []
    patterns: list[str] = []
    for name in sorted(APP_RELATED_NAMES):
        patterns.extend([name, f"{name}/**"])
    return patterns


def split_glob_input(value: str, source_root: Path) -> list[str]:
    text = value.strip()
    if not text:
        return []

    if "," in text or "\n" in text:
        raw_parts = re.split(r"[\n,]+", text)
        return [item.strip() for item in raw_parts if item.strip()]

    source_prefix = str(source_root)
    if text.count(source_prefix) > 1:
        parts: list[str] = []
        for segment in text.split(source_prefix):
            segment = segment.strip()
            if not segment:
                continue
            parts.append(f"{source_prefix}{segment}")
        return parts

    return [text]


def normalize_exclude_globs(value: str, source_root: Path) -> list[str]:
    normalized: list[str] = []
    for item in split_glob_input(value, source_root):
        candidate = item.strip()
        if not candidate:
            continue
        if candidate.startswith(str(source_root)):
            try:
                rel = Path(candidate).resolve().relative_to(source_root)
                normalized.append(rel.as_posix())
                normalized.append(f"{rel.as_posix()}/**")
                continue
            except Exception:
                pass
        normalized.append(candidate)
    # preserve order while deduplicating
    return list(dict.fromkeys(normalized))


def dedupe(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(values))


def matches_glob(rel_path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(rel_path, pattern) for pattern in patterns)


def preserve_copy(source_root: Path, destination: Path, destination_name: str) -> Path:
    preserved_source = destination / "preserved" / "source"

    def ignore(directory: str, names: list[str]) -> set[str]:
        ignored = set()
        for name in names:
            if name in IGNORE_NAMES:
                ignored.add(name)
        current = Path(directory)
        if current == source_root and destination_name in names:
            ignored.add(destination_name)
        return ignored

    shutil.copytree(source_root, preserved_source, ignore=ignore)
    return preserved_source


def is_legacy_agent_material(rel_path: Path) -> bool:
    lower = rel_path.as_posix().lower()
    if rel_path.suffix.lower() not in DOC_EXTENSIONS:
        return False
    return any(keyword in lower for keyword in LEGACY_AGENT_KEYWORDS)


def score_directory(path: Path) -> dict[str, int]:
    scores = {"code": 0, "data": 0, "manuscript": 0, "output": 0, "docs": 0}
    for file_path in path.rglob("*"):
        if not file_path.is_file():
            continue
        suffix = file_path.suffix
        lower = file_path.name.lower()
        if suffix in CODE_EXTENSIONS:
            scores["code"] += 1
        if suffix in DATA_EXTENSIONS:
            scores["data"] += 1
        if suffix in MANUSCRIPT_EXTENSIONS or lower.endswith(".tex"):
            scores["manuscript"] += 1
        if suffix in FIGURE_EXTENSIONS or suffix in LOG_EXTENSIONS:
            scores["output"] += 1
        if suffix in DOC_EXTENSIONS:
            scores["docs"] += 1
    return scores


def top_level_target(name: str, path: Path, special_instructions: str, exclude_globs: list[str]) -> tuple[str, str]:
    lower_name = name.lower()
    rel = path.name

    if matches_glob(rel, exclude_globs):
        return ("preserved", f"preserved/{name}")

    if lower_name in APP_RELATED_NAMES and implied_exclude_globs(special_instructions):
        return ("preserved", f"preserved/{name}")

    if lower_name in {"data", "scripts", "output", "manuscript"}:
        return (lower_name, lower_name)

    if lower_name == "notes":
        return ("notes", "notes/imported/notes")

    if lower_name in {"paper", "draft", "drafts", "writeup", "tex"}:
        return ("manuscript", "manuscript")

    if lower_name in {"analysis", "code", "src", "program", "programs", "notebooks", "notebook", "do", "dofiles"}:
        return ("scripts", f"scripts/{name}")

    if lower_name in {"raw", "input", "inputs", "dataset", "datasets", "clean", "cleaned", "processed", "derived", "external", "downloads"}:
        return ("data", f"data/{name}")

    if lower_name in {"results", "result", "figures", "figs", "plots", "tables", "logs", "log", "estimates"}:
        return ("output", f"output/{name}")

    if lower_name in {"docs", "doc", "memos", "memo", "outline", "literature", "readings"}:
        return ("notes", f"notes/{name}")

    if lower_name in LEGACY_AGENT_KEYWORDS:
        return ("legacy_agent_material", f".workflow/state/migration/legacy-agent-material/{name}")

    scores = score_directory(path)
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return ("preserved", f"preserved/{name}")
    if best == "code":
        return ("scripts", f"scripts/{name}")
    if best == "data":
        return ("data", f"data/{name}")
    if best == "manuscript":
        return ("manuscript", f"manuscript/{name}")
    if best == "output":
        return ("output", f"output/{name}")
    if best == "docs":
        return ("notes", f"notes/{name}")
    return ("preserved", f"preserved/{name}")


def classify_root_file(path: Path, special_instructions: str, exclude_globs: list[str]) -> tuple[str, str]:
    name = path.name
    lower_name = name.lower()
    suffix = path.suffix

    if name == ".gitignore":
        return ("source_gitignore", ".workflow/state/migration/original-gitignore.txt")

    if matches_glob(name, exclude_globs):
        return ("preserved", f"preserved/{name}")

    if lower_name in APP_RELATED_NAMES and implied_exclude_globs(special_instructions):
        return ("preserved", f"preserved/{name}")

    if is_legacy_agent_material(Path(name)):
        return ("legacy_agent_material", f".workflow/state/migration/legacy-agent-material/{name}")

    if suffix in CODE_EXTENSIONS:
        return ("scripts", f"scripts/{name}")
    if suffix in DATA_EXTENSIONS:
        return ("data", f"data/{name}")
    if suffix in MANUSCRIPT_EXTENSIONS:
        return ("manuscript", f"manuscript/{name}")
    if suffix in DOC_EXTENSIONS:
        return ("notes", f"notes/imported/{name}")
    return ("preserved", f"preserved/{name}")


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def should_replace_scaffold(destination_root: Path, dst: Path) -> bool:
    rel = dst.relative_to(destination_root).as_posix()
    if rel == "manuscript/main.tex":
        return True
    if rel == "manuscript/bibliography/references.bib":
        return True
    return rel.startswith("manuscript/sections/") and rel.endswith(".tex")


def copy_file_with_conflict(
    src: Path,
    dst: Path,
    conflict_root: Path,
    source_copy_root: Path,
    destination_root: Path,
    conflicts: list[str],
) -> Path:
    ensure_parent(dst)
    if not dst.exists():
        shutil.copy2(src, dst)
        return dst
    if should_replace_scaffold(destination_root, dst):
        shutil.copy2(src, dst)
        return dst
    if dst.is_file() and filecmp.cmp(src, dst, shallow=False):
        return dst
    fallback = conflict_root / src.relative_to(source_copy_root)
    ensure_parent(fallback)
    shutil.copy2(src, fallback)
    conflicts.append(
        f"Conflict copying {src.relative_to(source_copy_root)} -> {dst.relative_to(destination_root)}; "
        f"stored at {fallback.relative_to(destination_root)}"
    )
    return fallback


def merge_tree_copy(
    src: Path,
    dst: Path,
    conflict_root: Path,
    source_copy_root: Path,
    destination_root: Path,
    copied_files: list[Path],
    conflicts: list[str],
) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for child in sorted(src.iterdir(), key=lambda item: item.name):
        target = dst / child.name
        if child.is_dir():
            merge_tree_copy(child, target, conflict_root, source_copy_root, destination_root, copied_files, conflicts)
        else:
            final_path = copy_file_with_conflict(child, target, conflict_root, source_copy_root, destination_root, conflicts)
            copied_files.append(final_path)


def create_relative_symlink(target: Path, link_path: Path) -> None:
    ensure_parent(link_path)
    if link_path.exists() or link_path.is_symlink():
        return
    relative_target = os.path.relpath(target, start=link_path.parent)
    link_path.symlink_to(relative_target)


def append_ignore_rules(destination: Path, source_root: Path, large_paths: list[str]) -> None:
    path = destination / ".gitignore"
    existing = read_text(path).rstrip() + "\n\n"
    source_ignore = source_root / ".gitignore"
    extra = [
        "# Migration-specific ignores",
        "preserved/**",
        "!preserved/",
        ".workflow/state/migration/conflicts/",
        "data/**",
        "!data/",
        "!data/.gitkeep",
        "!data/README.md",
        "!data/raw/",
        "!data/derived/",
        "!data/external/",
        "output/**",
        "!output/",
        "!output/.gitkeep",
        "!output/README.md",
        "!output/figures/",
        "!output/tables/",
        "!output/logs/",
    ]
    if large_paths:
        extra.append("")
        extra.append("# Large imported files outside data/output")
        extra.extend(sorted(large_paths))
    if source_ignore.exists():
        extra.append("")
        extra.append("# Original source .gitignore was archived to .workflow/state/migration/original-gitignore.txt")
    write_text(path, existing + "\n".join(extra) + "\n")


def extract_readme_summary(source_copy_root: Path) -> str:
    for candidate in ("README.md", "Readme.md", "readme.md"):
        path = source_copy_root / candidate
        if path.exists():
            text = read_text(path)
            paragraphs = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
            for block in paragraphs:
                if not block.startswith("#"):
                    line = " ".join(block.splitlines()).strip()
                    if line:
                        return line
    return ""


def populate_adopted_project_files(
    destination: Path,
    source_root: Path,
    special_instructions: str,
    exclude_globs: list[str],
    records: list[MappingRecord],
    conflicts: list[str],
    legacy_docs: list[str],
) -> None:
    brief_path = destination / "notes" / "project-brief.md"
    notes_path = destination / "notes" / "source-notes.md"
    memory_path = destination / ".workflow" / "memory" / "MEMORY.md"
    session_log_path = destination / ".workflow" / "memory" / "session-log.md"
    decision_path = destination / ".workflow" / "decisions" / f"{datetime.now().strftime('%Y-%m-%d')}-existing-project-migration.md"

    readme_summary = extract_readme_summary(destination / "preserved" / "source")
    project_description = special_instructions or readme_summary or "Imported from an existing project and normalized into the Codex workflow structure."
    data_targets = sorted(
        {record.destination_rel for record in records if record.category == "data" and not record.destination_rel.endswith(".txt")}
    )

    brief = read_text(brief_path)
    brief = set_section_value(brief, "Working Title", source_root.name)
    brief = set_section_value(brief, "Project Description", project_description)
    brief = set_section_value(brief, "Project Status", "existing project")
    brief = set_section_value(brief, "Intake Depth", "dig deeper later")
    brief = set_section_value(
        brief,
        "Research Question",
        "TBD after reviewing the migrated repository, preserved source copy, and migration report.",
    )
    brief = set_section_value(
        brief,
        "Why This Matters",
        "This project was migrated into the Codex workflow so planning, review, memory, and cleanup can proceed in a stable academic structure.",
    )
    brief = set_section_value(
        brief,
        "Proposed Contribution",
        "First stabilize the imported project, then refine the substantive contribution once the migrated structure has been reviewed.",
    )
    brief = set_section_value(brief, "Paper Type", "Imported existing project")
    brief = set_section_value(brief, "Target Reader Or Journal", "TBD after migration review")
    constraints = [
        "- Original source preserved at `preserved/source/`.",
        "- Migration report at `.workflow/state/migration/report.md`.",
        "- Review conflicts before deleting compatibility symlinks or preserved content.",
    ]
    if exclude_globs:
        constraints.append(f"- Paths preserved without restructuring: {', '.join(exclude_globs)}.")
    brief = set_section_value(brief, "Constraints", "\n".join(constraints))
    non_negotiables = ["- Do not edit the preserved source copy in place."]
    if special_instructions:
        non_negotiables.append(f"- Special instructions: {special_instructions}")
    brief = set_section_value(brief, "Non-Negotiables", "\n".join(non_negotiables))
    write_text(brief_path, brief)

    source_notes = read_text(notes_path)
    source_notes = set_section_value(
        source_notes,
        "Key Papers",
        "TBD from the imported manuscript, notes, and bibliography files.",
    )
    source_notes = set_section_value(
        source_notes,
        "Data",
        "\n".join(f"- `{item}`" for item in data_targets[:20]) or "No data targets were imported automatically.",
    )
    source_notes = set_section_value(
        source_notes,
        "Identification Strategy Notes",
        "TBD after inspecting imported code, manuscript sections, and legacy notes.",
    )
    source_notes = set_section_value(
        source_notes,
        "Empirical Design Notes",
        "TBD after reviewing imported scripts and outputs in the cleaned repository.",
    )
    open_questions = [
        "- Review `.workflow/state/migration/report.md`.",
        "- Decide whether preserved paths should remain, be archived, or be migrated further.",
    ]
    if conflicts:
        open_questions.append(f"- Resolve {len(conflicts)} migration conflict(s) under `.workflow/state/migration/conflicts/`.")
    source_notes = set_section_value(source_notes, "Open Questions", "\n".join(open_questions))
    source_notes = set_section_value(
        source_notes,
        "Citations To Verify",
        "Imported bibliography and manuscript citations should be checked after the first Codex review pass.",
    )
    write_text(notes_path, source_notes)

    memory = read_text(memory_path).rstrip() + "\n\n"
    memory += f"- `[PROJECT:title] {source_root.name}`\n"
    memory += "- `[PROJECT:status] existing project`\n"
    memory += "- `[PROJECT:migration] Imported into a workflow-managed review copy; original source preserved at `preserved/source/`.\n"
    if special_instructions:
        memory += f"- `[PROJECT:special_instructions] {special_instructions}`\n"
    if legacy_docs:
        memory += "- `[PROJECT:legacy_agent_material] Archived legacy workflow and agent documents under `.workflow/state/migration/legacy-agent-material/`.\n"
    write_text(memory_path, memory)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    session_entry = "\n".join(
        [
            "",
            f"## {timestamp}: Existing project migration",
            "",
            f"- Summary: Migrated `{source_root.name}` into a reviewable Codex workflow copy.",
            "- Inputs used: existing project files, optional special instructions, and optional exclusion globs.",
            "- Outputs produced: canonical researcher-facing structure, preserved source copy, migration report, and compatibility symlinks.",
            "- Decisions and rationale: Chose a reviewable copied migration rather than in-place restructuring to preserve the original project.",
            "- Open items: Inspect the migration report, preserved source, and any conflict files before adopting the cleaned repo as the working version.",
            "- Next recommended action: Start Codex in this cleaned repo and ask it to inventory the imported project before substantive edits.",
            "",
        ]
    )
    write_text(session_log_path, read_text(session_log_path).rstrip() + session_entry)

    decision = textwrap.dedent(
        f"""\
        ---
        layer: decision
        date: {datetime.now().strftime('%Y-%m-%d')}
        topic: existing-project-migration
        status: active
        superseded_by:
        review_date:
        ---

        # Decision Record

        ## Context

        An existing project was converted into a workflow-managed copy rather than restructured in place.

        ## Options Considered

        ### Option A

        - Pros: Rewrite the original repository in place.
        - Cons: High risk of irreversible path breakage and hard-to-audit changes.
        - Verdict: Rejected.

        ### Option B

        - Pros: Create a new cleaned copy with preserved source material and compatibility links.
        - Cons: Requires review before adoption and duplicates the project for inspection.
        - Verdict: Accepted.

        ## Decision

        Create a standalone cleaned repository inside a new subdirectory, preserve the full original source copy under `preserved/source/`, and normalize the researcher-facing structure around that copied version.

        ## Rationale

        This keeps the original project untouched while giving Codex a stable workflow-managed version to operate on.

        ## Implementation

        - Imported the project into the canonical top-level academic structure.
        - Archived legacy agent and workflow documents into `.workflow/state/migration/legacy-agent-material/`.
        - Wrote migration memory, notes, and a migration report.

        ## Risks

        - Some path assumptions may still need manual follow-up despite compatibility symlinks.
        - Preserved content may contain material that should later be archived or deleted once migration is complete.

        ## Consequences

        - The cleaned repository is immediately usable with the Codex workflow.
        - The preserved source remains available for comparison.

        ## Follow-Up Actions

        - Review `.workflow/state/migration/report.md`.
        - Resolve any files copied into `.workflow/state/migration/conflicts/`.
        - Decide whether compatibility symlinks should remain long term.
        """
    )
    write_text(decision_path, decision)


def write_migration_report(
    destination: Path,
    source_root: Path,
    records: list[MappingRecord],
    conflicts: list[str],
    symlinks: list[str],
    special_instructions: str,
    exclude_globs: list[str],
) -> None:
    migration_root = destination / ".workflow" / "state" / "migration"
    migration_root.mkdir(parents=True, exist_ok=True)
    report_path = migration_root / "report.md"
    csv_path = migration_root / "file-map.csv"

    grouped: dict[str, list[MappingRecord]] = {}
    for record in records:
        grouped.setdefault(record.category, []).append(record)

    lines = [
        "# Migration Report",
        "",
        f"- Source project: `{source_root}`",
        f"- Cleaned project: `{destination}`",
        f"- Generated at: `{datetime.now().isoformat(timespec='seconds')}`",
        "",
        "## Inputs",
        "",
        f"- Special instructions: {special_instructions or 'None provided.'}",
        f"- Explicit exclusion globs: {', '.join(exclude_globs) if exclude_globs else 'None.'}",
        "",
        "## Summary",
        "",
        f"- Total mapped items: {len(records)}",
        f"- Compatibility symlinks created: {len(symlinks)}",
        f"- Conflicts captured for manual review: {len(conflicts)}",
        "",
        "## Category Breakdown",
        "",
    ]
    for category in sorted(grouped):
        lines.append(f"- `{category}`: {len(grouped[category])}")
    lines.extend(["", "## Compatibility Symlinks", ""])
    if symlinks:
        lines.extend(f"- `{item}`" for item in symlinks)
    else:
        lines.append("- None.")
    lines.extend(["", "## Conflicts", ""])
    if conflicts:
        lines.extend(f"- {item}" for item in conflicts)
    else:
        lines.append("- None.")
    write_text(report_path, "\n".join(lines) + "\n")

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["source_rel", "destination_rel", "category", "mode", "notes"])
        for record in records:
            writer.writerow(
                [
                    record.source_rel,
                    record.destination_rel,
                    record.category,
                    record.mode,
                    record.notes,
                ]
            )


def rewrite_top_level_references(destination: Path, rewrite_map: dict[str, str]) -> None:
    skip_parts = {".git", "__pycache__", "preserved", ".workflow"}
    skip_files = {
        destination / "README.md",
        destination / "SETUP.md",
        destination / "STARTER_PROMPT.md",
    }
    for path in destination.rglob("*"):
        if not path.is_file():
            continue
        if any(part in skip_parts for part in path.parts):
            continue
        if path in skip_files:
            continue
        if path.suffix not in REWRITE_EXTENSIONS:
            continue
        original = try_read_text(path)
        if original is None:
            continue
        updated = original
        for old, new in rewrite_map.items():
            updated = re.sub(
                rf"(?<![A-Za-z0-9_.-]){re.escape(old)}(/)",
                f"{new}/",
                updated,
            )
        if updated != original:
            write_text(path, updated)


def init_git_repo(project_dir: Path) -> None:
    shell(["git", "init", "-b", "main"], cwd=project_dir)
    shell(["git", "add", "."], cwd=project_dir)
    shell(["git", "commit", "-m", "Migrate existing project into codex workflow"], cwd=project_dir)


def collect_args(args: argparse.Namespace) -> dict[str, object]:
    destination_name = args.destination_name or prompt("Cleaned folder name", default=DEFAULT_DEST_NAME, required=True)
    special_instructions = args.special_instructions or prompt("Special instructions (optional)")
    exclude_globs_value = args.exclude_globs or prompt(
        "Paths or globs to leave untouched in preserved/ (optional; prefer top-level names like backend,frontend)"
    )
    bypass = args.dangerously_bypass_approvals_and_sandbox
    if bypass is None:
        bypass = prompt_yes_no("Allow Codex to bypass approvals and sandbox in the cleaned project", default=False)
    return {
        "destination_name": slugify(destination_name),
        "special_instructions": special_instructions,
        "exclude_globs": dedupe(
            normalize_exclude_globs(exclude_globs_value, Path(args.project_root).expanduser().resolve())
            + implied_exclude_globs(special_instructions)
        ),
        "dangerously_bypass_approvals_and_sandbox": bypass,
    }


def enable_bypass_in_project_config(destination: Path, enabled: bool) -> None:
    config_path = destination / ".workflow" / "config" / "project.toml"
    text = read_text(config_path)
    text = re.sub(
        r"^dangerously_bypass_approvals_and_sandbox = (true|false)$",
        f"dangerously_bypass_approvals_and_sandbox = {'true' if enabled else 'false'}",
        text,
        flags=re.MULTILINE,
    )
    write_text(config_path, text)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a workflow-managed cleaned copy of an existing project")
    parser.add_argument("--project-root", default=".", help="Existing project root to migrate")
    parser.add_argument("--destination-name", help="Name of the cleaned subdirectory to create inside the project root")
    parser.add_argument("--special-instructions", help="Optional special migration instructions")
    parser.add_argument("--exclude-globs", help="Comma-separated globs to preserve without restructuring")
    parser.add_argument(
        "--dangerously-bypass-approvals-and-sandbox",
        dest="dangerously_bypass_approvals_and_sandbox",
        action="store_true",
        help="Configure the cleaned project to launch Codex with --dangerously-bypass-approvals-and-sandbox",
    )
    parser.add_argument(
        "--no-dangerously-bypass-approvals-and-sandbox",
        dest="dangerously_bypass_approvals_and_sandbox",
        action="store_false",
        help="Do not configure the cleaned project to launch Codex with --dangerously-bypass-approvals-and-sandbox",
    )
    parser.add_argument("--no-init-git", action="store_true", help="Do not initialize a git repository in the cleaned project")
    parser.set_defaults(dangerously_bypass_approvals_and_sandbox=None)
    args = parser.parse_args()

    source_root = Path(args.project_root).expanduser().resolve()
    if not source_root.is_dir():
        raise SystemExit(f"Project root does not exist: {source_root}")

    answers = collect_args(args)
    destination = source_root / str(answers["destination_name"])
    if destination.exists():
        raise SystemExit(f"Destination already exists: {destination}")

    copy_template(destination)
    enable_bypass_in_project_config(destination, bool(answers["dangerously_bypass_approvals_and_sandbox"]))

    preserved_source = preserve_copy(source_root, destination, str(answers["destination_name"]))
    conflict_root = destination / ".workflow" / "state" / "migration" / "conflicts"
    (destination / ".workflow" / "state" / "migration" / "legacy-agent-material").mkdir(parents=True, exist_ok=True)

    records: list[MappingRecord] = []
    conflicts: list[str] = []
    symlinks: list[str] = []
    rewrite_map: dict[str, str] = {}
    large_paths: list[str] = []
    legacy_docs: list[str] = []

    for item in sorted(preserved_source.iterdir(), key=lambda p: p.name):
        if item.name in IGNORE_NAMES:
            continue
        if item.is_dir():
            category, destination_rel = top_level_target(
                item.name,
                item,
                str(answers["special_instructions"]),
                list(dict.fromkeys(answers["exclude_globs"])),
            )
        else:
            category, destination_rel = classify_root_file(
                item,
                str(answers["special_instructions"]),
                list(dict.fromkeys(answers["exclude_globs"])),
            )

        target = destination / destination_rel
        copied_files: list[Path] = []

        if category == "source_gitignore":
            write_text(target, read_text(item))
            records.append(MappingRecord(item.name, destination_rel, category, "copied"))
            continue

        if category == "legacy_agent_material":
            if item.is_dir():
                merge_tree_copy(item, target, conflict_root, preserved_source, destination, copied_files, conflicts)
            else:
                final_path = copy_file_with_conflict(item, target, conflict_root, preserved_source, destination, conflicts)
                copied_files.append(final_path)
            legacy_docs.append(item.name)
            records.append(MappingRecord(item.name, destination_rel, category, "copied"))
            continue

        if item.is_dir() and destination_rel in CANONICAL_ROOTS:
            merge_tree_copy(item, target, conflict_root, preserved_source, destination, copied_files, conflicts)
            mode = "merged"
        elif item.is_dir() and category in {"preserved", "data", "output"}:
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                merge_tree_copy(item, target, conflict_root, preserved_source, destination, copied_files, conflicts)
                mode = "merged"
            else:
                create_relative_symlink(item, target)
                mode = "symlinked"
                symlinks.append(f"{target.relative_to(destination)} -> {item.relative_to(destination)}")
        elif item.is_dir():
            merge_tree_copy(item, target, conflict_root, preserved_source, destination, copied_files, conflicts)
            mode = "copied"
        elif category in {"preserved", "data", "output"} or item.suffix.lower() not in TEXT_EXTENSIONS:
            if not target.exists():
                create_relative_symlink(item, target)
                mode = "symlinked"
                symlinks.append(f"{target.relative_to(destination)} -> {item.relative_to(destination)}")
            else:
                final_path = copy_file_with_conflict(item, target, conflict_root, preserved_source, destination, conflicts)
                copied_files.append(final_path)
                mode = "copied"
        else:
            final_path = copy_file_with_conflict(item, target, conflict_root, preserved_source, destination, conflicts)
            copied_files.append(final_path)
            mode = "copied"

        records.append(MappingRecord(item.name, destination_rel, category, mode))

        if item.name not in CANONICAL_ROOTS and item.name not in {".gitignore", "README.md", "SETUP.md", "STARTER_PROMPT.md"}:
            link_path = destination / item.name
            if not link_path.exists():
                create_relative_symlink(target, link_path)
                symlinks.append(f"{item.name} -> {destination_rel}")

        if destination_rel not in CANONICAL_ROOTS:
            rewrite_map[item.name] = destination_rel
        elif item.name == "paper":
            rewrite_map[item.name] = "manuscript"

        for copied_file in copied_files:
            if copied_file.is_file() and copied_file.stat().st_size >= LARGE_FILE_BYTES:
                large_paths.append(str(copied_file.relative_to(destination)))

    append_ignore_rules(destination, source_root, large_paths)
    rewrite_top_level_references(destination, rewrite_map)
    populate_adopted_project_files(
        destination,
        source_root,
        str(answers["special_instructions"]),
        list(dict.fromkeys(answers["exclude_globs"])),
        records,
        conflicts,
        legacy_docs,
    )
    write_migration_report(
        destination,
        source_root,
        records,
        conflicts,
        symlinks,
        str(answers["special_instructions"]),
        list(dict.fromkeys(answers["exclude_globs"])),
    )

    if not args.no_init_git:
        init_git_repo(destination)

    print(f"Created cleaned project at {destination}")
    print("Review these first:")
    print(f"- {destination / '.workflow/state/migration/report.md'}")
    print(f"- {destination / 'preserved/source'}")
    if conflicts:
        print(f"- {destination / '.workflow/state/migration/conflicts'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
