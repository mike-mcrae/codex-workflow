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
    ".DS_Store",
    ".git",
    "__pycache__",
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
    ".ado",
    ".bash",
    ".do",
    ".ipynb",
    ".jl",
    ".m",
    ".py",
    ".R",
    ".r",
    ".Rmd",
    ".sh",
    ".zsh",
}
DATA_EXTENSIONS = {
    ".bz2",
    ".csv",
    ".db",
    ".dta",
    ".feather",
    ".gz",
    ".json",
    ".parquet",
    ".rdata",
    ".rds",
    ".sav",
    ".sqlite",
    ".tsv",
    ".txt",
    ".xls",
    ".xlsx",
    ".xz",
    ".zip",
}
MANUSCRIPT_EXTENSIONS = {
    ".bib",
    ".bst",
    ".cls",
    ".doc",
    ".docx",
    ".pdf",
    ".tex",
}
FIGURE_EXTENSIONS = {
    ".eps",
    ".jpeg",
    ".jpg",
    ".pdf",
    ".png",
    ".svg",
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
}
NOTE_KEYWORDS = {
    "agenda",
    "audit",
    "brief",
    "handover",
    "literature",
    "meeting",
    "memo",
    "motivation",
    "note",
    "notes",
    "outline",
    "plan",
    "readme",
    "todo",
    "thought",
}
DECISION_PATTERNS = [
    re.compile(r"\b(decision|decided|we decided|agreed|chosen|choice)\b", re.IGNORECASE),
    re.compile(r"\b(use|using|adopt|adopted|prefer|preferred)\b", re.IGNORECASE),
]
RULE_PATTERNS = [
    re.compile(r"\b(must|should|do not|don't|never|always|important|non-negotiable)\b", re.IGNORECASE),
]
OPEN_PATTERNS = [
    re.compile(r"\b(todo|tbd|open question|follow[- ]up|next step|remaining)\b", re.IGNORECASE),
]
LEGACY_AGENT_KEYWORDS = {
    "agent",
    "agents",
    "claude",
    "codex",
    "instruction",
    "instructions",
    "memory",
    "planner",
    "prompt",
    "prompts",
    "review",
    "workflow",
}
APP_RELATED_NAMES = {
    "android",
    "app",
    "apps",
    "backend",
    "client",
    "frontend",
    "ios",
    "mobile",
    "server",
    "ui",
    "web",
}
APP_FILE_NAMES = {
    "angular.json",
    "next.config.js",
    "next.config.mjs",
    "package-lock.json",
    "package.json",
    "pnpm-lock.yaml",
    "render.yaml",
    "tsconfig.json",
    "vite.config.js",
    "vite.config.ts",
    "yarn.lock",
}
CANONICAL_ROOTS = {"data", "scripts", "output", "manuscript", "notes"}
REWRITE_EXTENSIONS = {
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
MEMORY_TEXT_EXTENSIONS = {
    ".bib",
    ".md",
    ".tex",
    ".txt",
}
LARGE_FILE_BYTES = 10 * 1024 * 1024
HIDDEN_SOURCE_SNAPSHOT = ".workflow/state/migration/source-snapshot"
HIDDEN_EXCLUDED = ".workflow/state/migration/excluded"
HIDDEN_UNCLASSIFIED = ".workflow/state/migration/unclassified"
HIDDEN_CONFLICTS = ".workflow/state/migration/conflicts"
LEGACY_AGENT_ARCHIVE = ".workflow/state/migration/legacy-agent-material"
MEMORY_SOURCES_PATH = ".workflow/state/migration/imported-memory-sources.md"


@dataclass
class MappingRecord:
    source_rel: str
    destination_rel: str
    category: str
    mode: str
    notes: str = ""


@dataclass
class MemoryInsight:
    summary: list[str]
    rules: list[tuple[str, str]]
    decisions: list[tuple[str, str]]
    open_items: list[tuple[str, str]]
    citations: list[str]
    sources: list[str]


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
    if "app" not in text and "frontend" not in text and "backend" not in text and "web" not in text:
        return []
    triggers = {"disregard", "ignore", "leave", "remain", "untouched", "not related", "exclude"}
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
    return list(dict.fromkeys(normalized))


def dedupe(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(values))


def matches_glob(rel_path: str, patterns: list[str]) -> bool:
    for pattern in patterns:
        if fnmatch.fnmatch(rel_path, pattern):
            return True
        if fnmatch.fnmatch(f"{rel_path}/", pattern):
            return True
        if fnmatch.fnmatch(f"{rel_path}/placeholder", pattern):
            return True
    return False


def preserve_copy(source_root: Path, destination: Path, destination_name: str) -> Path:
    preserved_source = destination / HIDDEN_SOURCE_SNAPSHOT

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


def classify_script_path(name: str) -> str:
    suffix = Path(name).suffix.lower()
    lower = name.lower()
    if suffix in {".do", ".ado"}:
        return f"scripts/stata/{name}"
    if suffix in {".r", ".rmd"}:
        return f"scripts/r/{name}"
    if suffix in {".sh", ".bash", ".zsh"} or lower == "makefile":
        return f"scripts/shell/{name}"
    if suffix in {".py", ".ipynb", ".jl", ".m"} or lower in {
        "environment.yml",
        "environment.yaml",
        "pyproject.toml",
        "requirements.txt",
        "setup.py",
    }:
        return f"scripts/python/{name}"
    return f"scripts/{name}"


def classify_data_path(name: str, is_dir: bool) -> str:
    lower = name.lower()
    if any(token in lower for token in {"derived", "clean", "processed"}):
        return f"data/derived/{name}"
    if any(token in lower for token in {"external", "download", "source"}):
        return f"data/external/{name}"
    if not is_dir:
        return f"data/raw/{name}"
    return f"data/{name}"


def classify_output_path(name: str) -> str:
    lower = name.lower()
    suffix = Path(name).suffix.lower()
    if lower.endswith(".log") or suffix in LOG_EXTENSIONS:
        return f"output/logs/{name}"
    if any(token in lower for token in {"table", "tables"}):
        return f"output/tables/{name}"
    if any(token in lower for token in {"figure", "figures", "fig", "map", "maps", "plot", "plots", "image"}):
        return f"output/figures/{name}"
    if suffix in FIGURE_EXTENSIONS:
        return f"output/figures/{name}"
    return f"output/{name}"


def classify_note_path(name: str) -> str:
    return f"notes/imported/{name}"


def classify_hidden_path(root: str, name: str) -> str:
    return f"{root}/{name}"


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
        if lower in APP_FILE_NAMES:
            scores["code"] += 2
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


def looks_like_app_material(name: str) -> bool:
    lower = name.lower()
    if lower in APP_RELATED_NAMES:
        return True
    if lower in APP_FILE_NAMES:
        return True
    return any(token in lower for token in {"frontend", "backend", "react", "next", "webapp"})


def top_level_target(name: str, path: Path, special_instructions: str, exclude_globs: list[str]) -> tuple[str, str]:
    lower_name = name.lower()
    rel = path.name

    if matches_glob(rel, exclude_globs):
        return ("excluded", classify_hidden_path(HIDDEN_EXCLUDED, name))

    if looks_like_app_material(lower_name):
        return ("excluded", classify_hidden_path(HIDDEN_EXCLUDED, name))

    if lower_name in {"data", "scripts", "output", "manuscript"}:
        return (lower_name, lower_name)
    if lower_name == "notes":
        return ("notes", "notes/imported")
    if lower_name in {"paper", "draft", "drafts", "writeup", "tex"}:
        return ("manuscript", "manuscript")
    if lower_name in {"docs", "doc", "documentation"}:
        return ("notes", "notes/imported/docs")
    if lower_name in {"logs", "log"}:
        return ("output", "output/logs")

    if any(token in lower_name for token in {"analysis", "code", "src", "program", "notebook", "dofile", "script"}):
        return ("scripts", f"scripts/{name}")
    if any(token in lower_name for token in {"data", "dataset", "raw", "clean", "cleaned", "processed", "derived", "external", "download"}):
        return ("data", classify_data_path(name, is_dir=True))
    if any(token in lower_name for token in {"result", "figure", "fig", "plot", "map", "table", "log", "estimate"}):
        return ("output", classify_output_path(name))
    if any(token in lower_name for token in {"memo", "outline", "literature", "reading", "note", "meeting", "plan"}):
        return ("notes", classify_note_path(name))
    if is_legacy_agent_material(Path(name)):
        return ("legacy_agent_material", f"{LEGACY_AGENT_ARCHIVE}/{name}")

    scores = score_directory(path)
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return ("unclassified", classify_hidden_path(HIDDEN_UNCLASSIFIED, name))
    if best == "code":
        return ("scripts", f"scripts/{name}")
    if best == "data":
        return ("data", classify_data_path(name, is_dir=True))
    if best == "manuscript":
        return ("manuscript", f"manuscript/imported/{name}")
    if best == "output":
        return ("output", classify_output_path(name))
    if best == "docs":
        return ("notes", classify_note_path(name))
    return ("unclassified", classify_hidden_path(HIDDEN_UNCLASSIFIED, name))


def classify_root_file(path: Path, special_instructions: str, exclude_globs: list[str]) -> tuple[str, str]:
    name = path.name
    lower_name = name.lower()
    suffix = path.suffix.lower()

    if name == ".gitignore":
        return ("source_gitignore", ".workflow/state/migration/original-gitignore.txt")

    if matches_glob(name, exclude_globs):
        return ("excluded", classify_hidden_path(HIDDEN_EXCLUDED, name))

    if looks_like_app_material(lower_name):
        return ("excluded", classify_hidden_path(HIDDEN_EXCLUDED, name))

    if is_legacy_agent_material(Path(name)):
        return ("legacy_agent_material", f"{LEGACY_AGENT_ARCHIVE}/{name}")

    if lower_name == "license":
        return ("root_doc", "LICENSE")
    if lower_name in {"readme.md", "readme.txt", "readme"}:
        return ("notes", "notes/imported/original-README.md")
    if lower_name in {"requirements.txt", "pyproject.toml", "setup.py", "environment.yml", "environment.yaml", "makefile"}:
        return ("scripts", classify_script_path(name))
    if lower_name in NOTE_KEYWORDS or any(token in lower_name for token in NOTE_KEYWORDS):
        return ("notes", classify_note_path(name))
    if suffix in CODE_EXTENSIONS:
        return ("scripts", classify_script_path(name))
    if suffix in DATA_EXTENSIONS:
        return ("data", classify_data_path(name, is_dir=False))
    if suffix in MANUSCRIPT_EXTENSIONS:
        if lower_name == "main.tex":
            return ("manuscript", "manuscript/main.tex")
        return ("manuscript", f"manuscript/imported/{name}")
    if suffix in LOG_EXTENSIONS:
        return ("output", classify_output_path(name))
    if suffix in FIGURE_EXTENSIONS:
        return ("output", classify_output_path(name))
    if suffix in DOC_EXTENSIONS:
        return ("notes", classify_note_path(name))
    return ("unclassified", classify_hidden_path(HIDDEN_UNCLASSIFIED, name))


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


def append_ignore_rules(destination: Path, source_root: Path, large_paths: list[str]) -> None:
    path = destination / ".gitignore"
    existing = read_text(path).rstrip() + "\n\n"
    source_ignore = source_root / ".gitignore"
    extra = [
        "# Migration-specific ignores",
        ".workflow/state/migration/source-snapshot/",
        ".workflow/state/migration/excluded/",
        ".workflow/state/migration/unclassified/",
        ".workflow/state/migration/conflicts/",
        "data/**",
        "!data/",
        "!data/README.md",
        "!data/raw/",
        "!data/derived/",
        "!data/external/",
        "output/**",
        "!output/",
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
    for candidate in ("README.md", "Readme.md", "readme.md", "README.txt", "README"):
        path = source_copy_root / candidate
        if not path.exists():
            continue
        text = try_read_text(path)
        if text is None:
            continue
        paragraphs = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
        for block in paragraphs:
            if block.startswith("#"):
                continue
            line = " ".join(block.splitlines()).strip()
            if line:
                return line
    return ""


def clean_snippet(text: str, limit: int = 220) -> str:
    single_line = re.sub(r"\s+", " ", text).strip()
    if len(single_line) <= limit:
        return single_line
    clipped = single_line[: limit - 3].rstrip(" ,;:")
    return f"{clipped}..."


def paragraphs_from_text(text: str) -> list[str]:
    chunks = [chunk.strip() for chunk in re.split(r"\n\s*\n", text) if chunk.strip()]
    paragraphs: list[str] = []
    for chunk in chunks:
        if chunk.startswith("#"):
            continue
        if chunk.lstrip().startswith("\\"):
            continue
        cleaned = clean_snippet(chunk, limit=320)
        if cleaned:
            paragraphs.append(cleaned)
    return paragraphs


def should_skip_memory_path(rel_path: str, exclude_globs: list[str]) -> bool:
    if matches_glob(rel_path, exclude_globs):
        return True
    first = rel_path.split("/", 1)[0].lower()
    return looks_like_app_material(first)


def extract_bib_keys(text: str) -> list[str]:
    return re.findall(r"@\w+\{([^,]+),", text)


def collect_memory_insights(source_copy_root: Path, exclude_globs: list[str]) -> MemoryInsight:
    summary: list[str] = []
    rules: list[tuple[str, str]] = []
    decisions: list[tuple[str, str]] = []
    open_items: list[tuple[str, str]] = []
    citations: list[str] = []
    sources: list[str] = []
    seen_summary: set[str] = set()
    seen_rules: set[str] = set()
    seen_decisions: set[str] = set()
    seen_open: set[str] = set()
    seen_sources: set[str] = set()

    for path in sorted(source_copy_root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(source_copy_root).as_posix()
        if any(part in IGNORE_NAMES for part in path.parts):
            continue
        if should_skip_memory_path(rel, exclude_globs):
            continue
        suffix = path.suffix.lower()
        lower_name = path.name.lower()
        if suffix not in MEMORY_TEXT_EXTENSIONS and lower_name not in {"readme", "readme.md", "readme.txt"}:
            continue
        text = try_read_text(path)
        if text is None:
            continue

        if rel not in seen_sources:
            sources.append(rel)
            seen_sources.add(rel)

        if suffix == ".bib":
            citations.extend(extract_bib_keys(text))

        for paragraph in paragraphs_from_text(text):
            lower = paragraph.lower()
            if len(summary) < 4 and (
                "project" in lower
                or "paper" in lower
                or "study" in lower
                or "analysis" in lower
                or "research" in lower
                or "evidence" in lower
            ):
                key = lower
                if key not in seen_summary:
                    summary.append(paragraph)
                    seen_summary.add(key)
            if "?" in paragraph or any(pattern.search(paragraph) for pattern in OPEN_PATTERNS):
                key = lower
                if key not in seen_open and len(open_items) < 10:
                    open_items.append((paragraph, rel))
                    seen_open.add(key)
                continue
            if any(pattern.search(paragraph) for pattern in RULE_PATTERNS):
                key = lower
                if key not in seen_rules and len(rules) < 10:
                    rules.append((paragraph, rel))
                    seen_rules.add(key)
            if any(pattern.search(paragraph) for pattern in DECISION_PATTERNS):
                key = lower
                if key not in seen_decisions and len(decisions) < 10:
                    decisions.append((paragraph, rel))
                    seen_decisions.add(key)

    citations = dedupe(citations)[:20]
    return MemoryInsight(
        summary=summary,
        rules=rules,
        decisions=decisions,
        open_items=open_items,
        citations=citations,
        sources=sources[:50],
    )


def append_decision_index(destination: Path, date: str, topic: str, file_name: str, status: str) -> None:
    index_path = destination / ".workflow" / "decisions" / "INDEX.md"
    text = read_text(index_path).rstrip() + "\n"
    row = f"| {date} | {topic} | [{file_name}]({file_name}) | {status} |"
    if row not in text:
        text += row + "\n"
    write_text(index_path, text)


def write_imported_context_topic(destination: Path, insight: MemoryInsight) -> None:
    topic_path = destination / ".workflow" / "memory" / "topics" / "imported-context.md"
    lines = [
        "# Imported Context",
        "",
        "Context extracted during `codex_clean` from the legacy project snapshot.",
        "",
        "## Imported Sources",
        "",
    ]
    if insight.sources:
        lines.extend(f"- `{item}`" for item in insight.sources)
    else:
        lines.append("- No text sources were extracted.")
    lines.extend(["", "## Project Summary Signals", ""])
    if insight.summary:
        lines.extend(f"- {item}" for item in insight.summary)
    else:
        lines.append("- No stable summary paragraph was extracted automatically.")
    lines.extend(["", "## Stable Rules", ""])
    if insight.rules:
        lines.extend(f"- {text} Source: `{source}`." for text, source in insight.rules)
    else:
        lines.append("- No durable rules were extracted automatically.")
    lines.extend(["", "## Imported Decisions", ""])
    if insight.decisions:
        lines.extend(f"- {text} Source: `{source}`." for text, source in insight.decisions)
    else:
        lines.append("- No decision-like statements were extracted automatically.")
    lines.extend(["", "## Open Items", ""])
    if insight.open_items:
        lines.extend(f"- {text} Source: `{source}`." for text, source in insight.open_items)
    else:
        lines.append("- No open-item signals were extracted automatically.")
    write_text(topic_path, "\n".join(lines) + "\n")


def write_memory_sources(destination: Path, insight: MemoryInsight) -> None:
    path = destination / MEMORY_SOURCES_PATH
    lines = [
        "# Imported Memory Sources",
        "",
        "These legacy project files were scanned to synthesize the new four-layer memory layout.",
        "",
    ]
    if insight.sources:
        lines.extend(f"- `{item}`" for item in insight.sources)
    else:
        lines.append("- No memory source files were detected.")
    write_text(path, "\n".join(lines) + "\n")


def write_imported_decision_file(destination: Path, insight: MemoryInsight, date_stamp: str) -> str | None:
    if not insight.decisions:
        return None
    file_name = f"{date_stamp}-imported-project-decisions.md"
    decision_path = destination / ".workflow" / "decisions" / file_name
    bullets = "\n".join(f"- {text} Source: `{source}`." for text, source in insight.decisions)
    content = textwrap.dedent(
        f"""\
        ---
        layer: decision
        date: {date_stamp}
        topic: imported-project-decisions
        status: imported
        superseded_by:
        review_date:
        ---

        # Decision Record

        ## Context

        `codex_clean` extracted prior decision-like statements from the legacy project materials and consolidated them here for citation-only reference.

        ## Options Considered

        ### Option A

        - Pros: Leave prior decisions buried in legacy notes and agent markdowns.
        - Cons: Future sessions would need to rediscover them repeatedly.
        - Verdict: Rejected.

        ### Option B

        - Pros: Consolidate those statements into a dated imported decision record with provenance.
        - Cons: Some extracted items may still need refinement after project review.
        - Verdict: Accepted.

        ## Decision

        Keep extracted historical decisions in Layer 2 as an imported reference file.

        ## Rationale

        This makes prior rationale discoverable without forcing old documents into the always-read memory layer.

        ## Implementation

        {bullets}

        ## Risks

        - Some extracted statements may reflect tentative notes rather than fully settled decisions.
        - The user or Codex should prune or supersede weak imports during early project review.

        ## Consequences

        - Prior rationale is now cited from Layer 2 instead of remaining scattered across legacy notes.

        ## Follow-Up Actions

        - Confirm which imported decisions remain active.
        - Supersede outdated decisions with project-specific decision logs as the cleaned repo stabilizes.
        """
    )
    write_text(decision_path, content)
    append_decision_index(destination, date_stamp, "imported-project-decisions", file_name, "imported")
    return file_name


def populate_adopted_project_files(
    destination: Path,
    source_root: Path,
    source_copy_root: Path,
    special_instructions: str,
    exclude_globs: list[str],
    records: list[MappingRecord],
    conflicts: list[str],
    legacy_docs: list[str],
    insight: MemoryInsight,
) -> None:
    brief_path = destination / "notes" / "project-brief.md"
    notes_path = destination / "notes" / "source-notes.md"
    memory_path = destination / ".workflow" / "memory" / "MEMORY.md"
    session_log_path = destination / ".workflow" / "memory" / "session-log.md"
    date_stamp = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    migration_decision_file = f"{date_stamp}-existing-project-migration.md"
    decision_path = destination / ".workflow" / "decisions" / migration_decision_file

    readme_summary = extract_readme_summary(source_copy_root)
    project_description = insight.summary[0] if insight.summary else readme_summary
    if not project_description:
        project_description = "Imported from an existing project and normalized into the Codex workflow structure."
    data_targets = sorted(
        {
            record.destination_rel
            for record in records
            if record.category == "data" and not record.destination_rel.endswith(".txt")
        }
    )

    brief = read_text(brief_path)
    brief = set_section_value(brief, "Working Title", source_root.name)
    brief = set_section_value(brief, "Project Description", project_description)
    brief = set_section_value(brief, "Project Status", "existing project")
    brief = set_section_value(brief, "Intake Depth", "dig deeper later")
    brief = set_section_value(
        brief,
        "Research Question",
        insight.summary[1] if len(insight.summary) > 1 else "TBD after reviewing the migrated repository and migration report.",
    )
    brief = set_section_value(
        brief,
        "Why This Matters",
        insight.summary[2] if len(insight.summary) > 2 else "This project was migrated into the Codex workflow so planning, review, memory, and cleanup can proceed inside a stable academic structure.",
    )
    brief = set_section_value(
        brief,
        "Proposed Contribution",
        insight.summary[3] if len(insight.summary) > 3 else "First stabilize the imported project, then refine the substantive contribution once the migrated structure has been reviewed.",
    )
    brief = set_section_value(brief, "Paper Type", "Imported existing project")
    brief = set_section_value(brief, "Target Reader Or Journal", "TBD after migration review")
    constraints = [
        f"- Hidden source snapshot at `{HIDDEN_SOURCE_SNAPSHOT}/` for provenance and comparison.",
        "- Migration report at `.workflow/state/migration/report.md`.",
        "- Only the canonical academic surface should be used for ongoing work.",
    ]
    if exclude_globs:
        constraints.append(f"- Excluded paths held outside the academic surface: {', '.join(exclude_globs)}.")
    brief = set_section_value(brief, "Constraints", "\n".join(constraints))
    non_negotiables = [
        f"- Do not edit `{HIDDEN_SOURCE_SNAPSHOT}/` in place.",
        "- Keep researcher work in `data/`, `scripts/`, `output/`, `manuscript/`, and `notes/` only.",
    ]
    if special_instructions:
        non_negotiables.append(f"- Special instructions: {special_instructions}")
    brief = set_section_value(brief, "Non-Negotiables", "\n".join(non_negotiables))
    write_text(brief_path, brief)

    source_notes = read_text(notes_path)
    if insight.citations:
        key_papers = "\n".join(f"- `{item}`" for item in insight.citations[:12])
    else:
        key_papers = "TBD from the imported manuscript, notes, and bibliography files."
    source_notes = set_section_value(source_notes, "Key Papers", key_papers)
    source_notes = set_section_value(
        source_notes,
        "Data",
        "\n".join(f"- `{item}`" for item in data_targets[:20]) or "No data targets were imported automatically.",
    )
    source_notes = set_section_value(
        source_notes,
        "Identification Strategy Notes",
        insight.rules[0][0] if insight.rules else "TBD after inspecting imported code, manuscript sections, and legacy notes.",
    )
    source_notes = set_section_value(
        source_notes,
        "Empirical Design Notes",
        insight.decisions[0][0] if insight.decisions else "TBD after reviewing imported scripts and outputs in the cleaned repository.",
    )
    open_questions = [
        "- Review `.workflow/state/migration/report.md`.",
        "- Confirm that rewritten paths resolve for the main empirical pipeline.",
    ]
    if conflicts:
        open_questions.append(f"- Resolve {len(conflicts)} migration conflict(s) under `{HIDDEN_CONFLICTS}/`.")
    for item, source in insight.open_items[:5]:
        open_questions.append(f"- {item} Source: `{source}`.")
    source_notes = set_section_value(source_notes, "Open Questions", "\n".join(open_questions))
    source_notes = set_section_value(
        source_notes,
        "Citations To Verify",
        "\n".join(f"- `{item}`" for item in insight.citations[:12]) or "Imported bibliography and manuscript citations should be checked after the first Codex review pass.",
    )
    write_text(notes_path, source_notes)

    write_imported_context_topic(destination, insight)
    write_memory_sources(destination, insight)

    memory_lines = [read_text(memory_path).rstrip(), "", f"- `[PROJECT:title]` {source_root.name}", "- `[PROJECT:status]` existing project"]
    memory_lines.append(
        f"- `[RULE:surface]` Work from the canonical academic surface only; raw migration material lives under `{HIDDEN_SOURCE_SNAPSHOT}/` and related hidden migration paths."
    )
    memory_lines.append(
        "- `[LEARN:imported_context]` Imported context is summarized in `.workflow/memory/topics/imported-context.md`."
    )
    memory_lines.append(
        "- `[LEARN:migration_report]` Migration details and file map live in `.workflow/state/migration/report.md` and `.workflow/state/migration/file-map.csv`."
    )
    if special_instructions:
        memory_lines.append(f"- `[RULE:special_instructions]` {special_instructions}")
    for rule_text, source in insight.rules[:4]:
        memory_lines.append(f"- `[LEARN:imported_rule]` {rule_text} Source: `{source}`.")
    if legacy_docs:
        memory_lines.append(f"- `[LEARN:legacy_agent_material]` Archived legacy workflow material under `{LEGACY_AGENT_ARCHIVE}/`.")
    write_text(memory_path, "\n".join(memory_lines).rstrip() + "\n")

    session_entry = "\n".join(
        [
            "",
            f"## {timestamp}: Existing project migration",
            "",
            f"- Summary: Migrated `{source_root.name}` into a workflow-managed academic project copy with canonical top-level structure.",
            "- Inputs used: legacy project files, optional special instructions, exclusion globs, and imported note extraction.",
            "- Outputs produced: canonical researcher-facing structure, hidden migration archive, rewritten paths, migration report, and four-layer memory seed.",
            "- Decisions and rationale: Performed migration in a new subdirectory so the original repo remained untouched while the cleaned copy became the workflow-managed working candidate.",
            "- Open items: Review the migration report, inspect any conflicts, and validate the main empirical pipeline inside the cleaned repo.",
            "- Next recommended action: Start Codex in this cleaned repo and ask it to audit the migrated structure before substantive work.",
            "",
        ]
    )
    write_text(session_log_path, read_text(session_log_path).rstrip() + session_entry)

    decision = textwrap.dedent(
        f"""\
        ---
        layer: decision
        date: {date_stamp}
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

        - Pros: Create a new cleaned copy with hidden migration archive, canonical top-level academic structure, rewritten paths, and imported memory.
        - Cons: Requires review before adoption and duplicates the project for inspection.
        - Verdict: Accepted.

        ## Decision

        Create a standalone cleaned repository inside a new subdirectory, archive the original source under `{HIDDEN_SOURCE_SNAPSHOT}/`, and normalize the researcher-facing project into the canonical academic workflow surface.

        ## Rationale

        This keeps the original project untouched while giving Codex a stable workflow-managed version that behaves like a repo started inside the workflow.

        ## Implementation

        - Imported the project into `data/`, `scripts/`, `output/`, `manuscript/`, and `notes/`.
        - Archived excluded, unclassified, and legacy agent material under hidden migration state.
        - Rewrote path references across migrated text files.
        - Seeded Layer 1, Layer 2, and Layer 3 memory from imported notes and legacy workflow material.

        ## Risks

        - Some path assumptions may still require manual follow-up if they depended on highly project-specific conventions.
        - Imported memory may contain tentative notes that should be pruned after review.

        ## Consequences

        - The cleaned repository is immediately usable with the Codex workflow.
        - The source snapshot remains available for comparison without cluttering the academic surface.

        ## Follow-Up Actions

        - Review `.workflow/state/migration/report.md`.
        - Resolve any files copied into `{HIDDEN_CONFLICTS}/`.
        - Confirm the main empirical scripts and manuscript compile paths after migration.
        """
    )
    write_text(decision_path, decision)
    append_decision_index(destination, date_stamp, "existing-project-migration", migration_decision_file, "active")
    write_imported_decision_file(destination, insight, date_stamp)


def write_migration_report(
    destination: Path,
    source_root: Path,
    records: list[MappingRecord],
    conflicts: list[str],
    special_instructions: str,
    exclude_globs: list[str],
    insight: MemoryInsight,
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
        "## Outcome",
        "",
        "- The cleaned repo was rebuilt around the canonical academic surface only:",
        "  - `data/`",
        "  - `scripts/`",
        "  - `output/`",
        "  - `manuscript/`",
        "  - `notes/`",
        "- Legacy leftovers were routed into hidden migration state instead of remaining visible at the top level.",
        "",
        "## Summary",
        "",
        f"- Total mapped items: {len(records)}",
        f"- Conflicts captured for manual review: {len(conflicts)}",
        f"- Imported memory sources scanned: {len(insight.sources)}",
        f"- Imported decision snippets extracted: {len(insight.decisions)}",
        "",
        "## Hidden Migration Paths",
        "",
        f"- Source snapshot: `{HIDDEN_SOURCE_SNAPSHOT}/`",
        f"- Excluded material: `{HIDDEN_EXCLUDED}/`",
        f"- Unclassified material: `{HIDDEN_UNCLASSIFIED}/`",
        f"- Conflict copies: `{HIDDEN_CONFLICTS}/`",
        f"- Legacy agent material: `{LEGACY_AGENT_ARCHIVE}/`",
        "",
        "## Category Breakdown",
        "",
    ]
    for category in sorted(grouped):
        lines.append(f"- `{category}`: {len(grouped[category])}")
    lines.extend(["", "## Conflicts", ""])
    if conflicts:
        lines.extend(f"- {item}" for item in conflicts)
    else:
        lines.append("- None.")
    lines.extend(["", "## Imported Memory Outputs", ""])
    lines.append("- `.workflow/memory/MEMORY.md` updated with durable migration rules and imported project signals.")
    lines.append("- `.workflow/memory/topics/imported-context.md` created from extracted notes and legacy docs.")
    lines.append("- `.workflow/memory/session-log.md` appended with migration state.")
    lines.append("- `.workflow/decisions/` populated with migration and imported-decision records.")
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
    skip_parts = {".git", "__pycache__", ".workflow", "source-snapshot", "excluded", "unclassified", "conflicts"}
    skip_files = {
        destination / "README.md",
        destination / "SETUP.md",
        destination / "STARTER_PROMPT.md",
    }

    def replacement_for(path: Path, new_rel: str) -> str:
        if path.suffix.lower() in {".tex", ".bib"}:
            return os.path.relpath(destination / new_rel, start=path.parent).replace(os.sep, "/")
        return new_rel

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
            file_specific = replacement_for(path, new)
            updated = re.sub(rf"(?<![A-Za-z0-9_.-]){re.escape(old)}(/)", f"{file_specific}/", updated)
            updated = re.sub(rf"(?<![A-Za-z0-9_.-])\./{re.escape(old)}(/)", f"./{file_specific}/", updated)
            updated = re.sub(rf"(?<![A-Za-z0-9_.-])\.\./{re.escape(old)}(/)", f"../{file_specific}/", updated)
            updated = re.sub(
                rf"(?<![A-Za-z0-9_.-/]){re.escape(old)}(?![A-Za-z0-9_.-/])",
                file_specific,
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
        "Paths or globs to keep out of the academic surface (optional; prefer top-level names like backend,frontend)"
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
    parser.add_argument("--exclude-globs", help="Comma-separated globs to keep out of the academic surface")
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

    source_copy_root = preserve_copy(source_root, destination, str(answers["destination_name"]))
    conflict_root = destination / HIDDEN_CONFLICTS
    (destination / LEGACY_AGENT_ARCHIVE).mkdir(parents=True, exist_ok=True)

    records: list[MappingRecord] = []
    conflicts: list[str] = []
    rewrite_map: dict[str, str] = {}
    large_paths: list[str] = []
    legacy_docs: list[str] = []
    exclude_globs = list(dict.fromkeys(answers["exclude_globs"]))
    special_instructions = str(answers["special_instructions"])

    for item in sorted(source_copy_root.iterdir(), key=lambda p: p.name):
        if item.name in IGNORE_NAMES:
            continue
        if item.is_dir():
            category, destination_rel = top_level_target(item.name, item, special_instructions, exclude_globs)
        else:
            category, destination_rel = classify_root_file(item, special_instructions, exclude_globs)

        target = destination / destination_rel
        copied_files: list[Path] = []

        if category == "source_gitignore":
            write_text(target, read_text(item))
            records.append(MappingRecord(item.name, destination_rel, category, "copied"))
            continue

        if item.is_dir():
            merge_tree_copy(item, target, conflict_root, source_copy_root, destination, copied_files, conflicts)
            mode = "merged" if target.exists() else "copied"
        else:
            final_path = copy_file_with_conflict(item, target, conflict_root, source_copy_root, destination, conflicts)
            copied_files.append(final_path)
            mode = "copied"

        records.append(MappingRecord(item.name, destination_rel, category, mode))

        if category == "legacy_agent_material":
            legacy_docs.append(item.name)

        if destination_rel not in {item.name, "."}:
            rewrite_map[item.name] = destination_rel

        for copied_file in copied_files:
            if copied_file.is_file() and copied_file.stat().st_size >= LARGE_FILE_BYTES:
                large_paths.append(str(copied_file.relative_to(destination)))

    append_ignore_rules(destination, source_root, large_paths)
    rewrite_top_level_references(destination, rewrite_map)
    insight = collect_memory_insights(source_copy_root, exclude_globs)
    populate_adopted_project_files(
        destination,
        source_root,
        source_copy_root,
        special_instructions,
        exclude_globs,
        records,
        conflicts,
        legacy_docs,
        insight,
    )
    write_migration_report(
        destination,
        source_root,
        records,
        conflicts,
        special_instructions,
        exclude_globs,
        insight,
    )

    if not args.no_init_git:
        init_git_repo(destination)

    print(f"Created cleaned project at {destination}")
    print("Review these first:")
    print(f"- {destination / '.workflow/state/migration/report.md'}")
    print(f"- {destination / HIDDEN_SOURCE_SNAPSHOT}")
    if conflicts:
        print(f"- {destination / HIDDEN_CONFLICTS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
