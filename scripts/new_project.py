#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


TEMPLATE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BASE_DIR = Path.home() / "Documents" / "GitHub"
REAL_CODEX = "/opt/homebrew/bin/codex"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "_", value.strip())
    slug = re.sub(r"_+", "_", slug).strip("._-")
    return slug or "new_project"


def shell(cmd: list[str], cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)


def git_config_value(key: str, fallback: str) -> str:
    result = subprocess.run(
        ["git", "config", "--global", key],
        text=True,
        capture_output=True,
        check=False,
    )
    value = result.stdout.strip()
    return value or fallback


def prompt(label: str, default: str = "", required: bool = False) -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        value = input(f"{label}{suffix}: ").strip()
        if value:
            return value
        if default:
            return default
        if not required:
            return ""


def copy_template(destination: Path) -> None:
    ignore_names = shutil.ignore_patterns(
        ".git",
        "__pycache__",
        "instructions.md",
        "memory_instructions.md",
    )
    shutil.copytree(TEMPLATE_ROOT, destination, ignore=ignore_names)
    for transient in [
        destination / "workspace" / "runs",
        destination / "workspace" / "audits",
        destination / "transcripts" / "raw",
        destination / "transcripts" / "live",
    ]:
        if transient.exists():
            for child in transient.iterdir():
                if child.name == ".gitkeep":
                    continue
                if child.is_dir():
                    shutil.rmtree(child)
                else:
                    child.unlink()
    index_file = destination / "transcripts" / "index" / "search-index.json"
    if index_file.exists():
        index_file.unlink()


def set_toml_value(text: str, key: str, value: str) -> str:
    return re.sub(
        rf'^{re.escape(key)} = ".*"$',
        f'{key} = "{value}"',
        text,
        flags=re.MULTILINE,
    )


def set_section_value(text: str, heading: str, value: str) -> str:
    pattern = rf"(## {re.escape(heading)}\n)(.*?)(\n## |\Z)"
    match = re.search(pattern, text, flags=re.DOTALL)
    if not match:
        return text
    body = value.strip()
    replacement = f"{match.group(1)}\n{body}\n{match.group(3)}"
    return text[: match.start()] + replacement + text[match.end() :]


def append_session_log(project_dir: Path, project_title: str, project_name: str) -> None:
    path = project_dir / "memory" / "session-log.md"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    block = "\n".join(
        [
            f"## {timestamp}: Project bootstrap",
            "",
            f"- Summary: Initialized the project template for {project_title}.",
            "- Inputs used: interactive new_project setup answers.",
            f"- Outputs produced: {project_name} repository scaffold, configured project files, and initial git repository.",
            "- Decisions and rationale: Accepted the default Codex academic workflow structure as the base project scaffold.",
            "- Open items: Codex should validate the project brief, source notes, and first plan.",
            "- Next recommended action: Start Codex and begin the planning workflow.",
            "",
        ]
    )
    existing = read_text(path).rstrip() + "\n\n"
    write_text(path, existing + block)


def populate_project(project_dir: Path, answers: dict[str, str]) -> None:
    config_path = project_dir / "config" / "project.toml"
    config = read_text(config_path)
    config = set_toml_value(config, "title", answers["title"])
    config = set_toml_value(config, "discipline", answers["discipline"])
    config = set_toml_value(config, "paper_type", answers["paper_type"])
    config = set_toml_value(config, "target_journal", answers["target_journal"])
    config = set_toml_value(config, "voice", answers["voice"])
    write_text(config_path, config)

    latex_path = project_dir / "paper" / "main.tex"
    latex = read_text(latex_path)
    latex = latex.replace(r"\title{Working Paper Title}", rf"\title{{{answers['title']}}}", 1)
    latex = latex.replace(r"\author{Author Name}", rf"\author{{{answers['author']}}}", 1)
    write_text(latex_path, latex)

    brief_path = project_dir / "workspace" / "input" / "project-brief.md"
    brief = read_text(brief_path)
    brief = set_section_value(brief, "Working Title", answers["title"])
    brief = set_section_value(brief, "Research Question", answers["research_question"])
    brief = set_section_value(brief, "Why This Matters", answers["why_matters"])
    brief = set_section_value(brief, "Proposed Contribution", answers["contribution"])
    brief = set_section_value(brief, "Paper Type", answers["paper_type"])
    brief = set_section_value(brief, "Target Reader Or Journal", answers["target_journal"])
    brief = set_section_value(brief, "Constraints", answers["constraints"])
    brief = set_section_value(brief, "Non-Negotiables", answers["non_negotiables"])
    write_text(brief_path, brief)

    notes_path = project_dir / "workspace" / "input" / "source-notes.md"
    notes = read_text(notes_path)
    notes = set_section_value(notes, "Key Papers", answers["key_papers"])
    notes = set_section_value(notes, "Data", answers["data"])
    notes = set_section_value(notes, "Identification Strategy Notes", answers["identification"])
    notes = set_section_value(notes, "Empirical Design Notes", answers["empirical_design"])
    notes = set_section_value(notes, "Open Questions", answers["open_questions"])
    notes = set_section_value(notes, "Citations To Verify", answers["citations_to_verify"])
    write_text(notes_path, notes)

    memory_path = project_dir / "memory" / "MEMORY.md"
    memory = read_text(memory_path).rstrip() + "\n\n"
    memory += f"- `[PROJECT:title] {answers['title']}`\n"
    if answers["non_negotiables"]:
        memory += f"- `[RULE:non_negotiables] {answers['non_negotiables']}`\n"
    if answers["constraints"]:
        memory += f"- `[RULE:constraints] {answers['constraints']}`\n"
    write_text(memory_path, memory)

    append_session_log(project_dir, answers["title"], answers["project_name"])


def init_git_repo(project_dir: Path) -> None:
    shell(["git", "init", "-b", "main"], cwd=project_dir)
    shell(["git", "add", "."], cwd=project_dir)
    shell(["git", "commit", "-m", "Bootstrap project from codex-workflow template"], cwd=project_dir)


def build_codex_prompt(project_dir: Path, answers: dict[str, str]) -> str:
    starter = read_text(project_dir / "STARTER_PROMPT.md").strip()
    tail = "\n\nProject bootstrap notes:\n"
    tail += f"- Project folder: {answers['project_name']}\n"
    tail += "- The project files have already been pre-populated from the interactive setup.\n"
    tail += "- Continue until you need direct user input, then ask the user the next necessary question.\n"
    return starter + tail


def launch_codex(project_dir: Path, answers: dict[str, str]) -> int:
    launcher = project_dir / "scripts" / "start_codex_session.sh"
    prompt_text = build_codex_prompt(project_dir, answers)
    env = os.environ.copy()
    env["CODEX_SESSION_TITLE"] = answers["title"]
    return subprocess.run(
        [str(launcher), REAL_CODEX, "-C", str(project_dir), prompt_text],
        cwd=str(project_dir),
        env=env,
        check=False,
    ).returncode


def collect_answers(args: argparse.Namespace) -> dict[str, str]:
    default_author = git_config_value("user.name", "Author Name")
    project_name = args.project_name or prompt("Project folder name", required=True)
    title = args.title or prompt("Paper or project title", default=project_name.replace("_", " "))
    author = args.author or prompt("Author", default=default_author)
    discipline = args.discipline or prompt("Discipline", default="Economics")
    paper_type = args.paper_type or prompt("Paper type", default="Empirical paper")
    target_journal = args.target_journal or prompt("Target journal or reader", default="General-interest field journal")
    voice = args.voice or prompt("Writing voice", default="Precise, formal, evidence-led")
    research_question = args.research_question or prompt("Research question", required=True)
    why_matters = args.why_matters or prompt("Why this matters", required=True)
    contribution = args.contribution or prompt("Proposed contribution", required=True)
    constraints = args.constraints or prompt("Constraints", default="None yet")
    non_negotiables = args.non_negotiables or prompt("Non-negotiables", default="Maintain rigorous academic standards")
    key_papers = args.key_papers or prompt("Key papers", default="TBD")
    data = args.data or prompt("Data", default="TBD")
    identification = args.identification or prompt("Identification strategy notes", default="TBD")
    empirical_design = args.empirical_design or prompt("Empirical design notes", default="TBD")
    open_questions = args.open_questions or prompt("Open questions", default="TBD")
    citations_to_verify = args.citations_to_verify or prompt("Citations to verify", default="TBD")
    return {
        "project_name": slugify(project_name),
        "title": title,
        "author": author,
        "discipline": discipline,
        "paper_type": paper_type,
        "target_journal": target_journal,
        "voice": voice,
        "research_question": research_question,
        "why_matters": why_matters,
        "contribution": contribution,
        "constraints": constraints,
        "non_negotiables": non_negotiables,
        "key_papers": key_papers,
        "data": data,
        "identification": identification,
        "empirical_design": empirical_design,
        "open_questions": open_questions,
        "citations_to_verify": citations_to_verify,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a new project from the local Codex workflow template")
    parser.add_argument("--project-name", help="Folder name under the base directory")
    parser.add_argument("--title", help="Project title")
    parser.add_argument("--author", help="Author name")
    parser.add_argument("--discipline", help="Discipline label")
    parser.add_argument("--paper-type", help="Paper type")
    parser.add_argument("--target-journal", help="Target journal or audience")
    parser.add_argument("--voice", help="Preferred writing voice")
    parser.add_argument("--research-question", help="Research question")
    parser.add_argument("--why-matters", help="Why the project matters")
    parser.add_argument("--contribution", help="Proposed contribution")
    parser.add_argument("--constraints", help="Constraints")
    parser.add_argument("--non-negotiables", help="Non-negotiables")
    parser.add_argument("--key-papers", help="Key papers")
    parser.add_argument("--data", help="Data notes")
    parser.add_argument("--identification", help="Identification strategy notes")
    parser.add_argument("--empirical-design", help="Empirical design notes")
    parser.add_argument("--open-questions", help="Open questions")
    parser.add_argument("--citations-to-verify", help="Citations to verify")
    parser.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR), help="Base directory for new projects")
    parser.add_argument("--no-launch", action="store_true", help="Create the project but do not launch Codex")
    args = parser.parse_args()

    answers = collect_answers(args)
    base_dir = Path(args.base_dir).expanduser().resolve()
    destination = base_dir / answers["project_name"]
    if destination.exists():
        raise SystemExit(f"Destination already exists: {destination}")
    base_dir.mkdir(parents=True, exist_ok=True)

    copy_template(destination)
    populate_project(destination, answers)
    init_git_repo(destination)

    print(f"Created project at {destination}")
    if args.no_launch:
        print("Skipping Codex launch because --no-launch was set.")
        return 0

    return launch_codex(destination, answers)


if __name__ == "__main__":
    raise SystemExit(main())
