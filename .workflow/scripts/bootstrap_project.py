#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / ".workflow/config/project.toml"
LATEX_PATH = ROOT / "manuscript/main.tex"
BRIEF_PATH = ROOT / "notes/project-brief.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def set_toml_value(text: str, key: str, value: str) -> str:
    pattern = rf'^{re.escape(key)} = ".*"$'
    replacement = f'{key} = "{value}"'
    return re.sub(pattern, replacement, text, flags=re.MULTILINE)


def replace_once(text: str, old: str, new: str) -> str:
    return text.replace(old, new, 1)


def set_section_value(text: str, heading: str, value: str) -> str:
    pattern = rf"(## {re.escape(heading)}\n)(.*?)(\n## |\Z)"
    match = re.search(pattern, text, flags=re.DOTALL)
    if not match:
        return text
    replacement = f"{match.group(1)}\n{value}\n{match.group(3)}"
    return text[: match.start()] + replacement + text[match.end() :]


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap this template for a new project")
    parser.add_argument("--title", required=True, help="Project or paper title")
    parser.add_argument("--author", default="Author Name", help="Author name for the LaTeX scaffold")
    parser.add_argument("--discipline", default="Economics", help="Discipline label")
    parser.add_argument("--paper-type", default="Empirical paper", help="Paper type")
    parser.add_argument("--target-journal", default="General-interest field journal", help="Target journal")
    parser.add_argument("--voice", default="Precise, formal, evidence-led", help="Preferred writing voice")
    args = parser.parse_args()

    config = read_text(CONFIG_PATH)
    config = set_toml_value(config, "title", args.title)
    config = set_toml_value(config, "discipline", args.discipline)
    config = set_toml_value(config, "paper_type", args.paper_type)
    config = set_toml_value(config, "target_journal", args.target_journal)
    config = set_toml_value(config, "voice", args.voice)
    write_text(CONFIG_PATH, config)

    latex = read_text(LATEX_PATH)
    latex = replace_once(latex, r"\title{Working Paper Title}", rf"\title{{{args.title}}}")
    latex = replace_once(latex, r"\author{Author Name}", rf"\author{{{args.author}}}")
    write_text(LATEX_PATH, latex)

    brief = read_text(BRIEF_PATH)
    brief = set_section_value(brief, "Working Title", args.title)
    brief = set_section_value(brief, "Paper Type", args.paper_type)
    brief = set_section_value(brief, "Target Reader Or Journal", args.target_journal)
    write_text(BRIEF_PATH, brief)

    print("Bootstrapped project template.")
    print(f"- title: {args.title}")
    print(f"- author: {args.author}")
    print(f"- discipline: {args.discipline}")
    print(f"- paper_type: {args.paper_type}")
    print(f"- target_journal: {args.target_journal}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
