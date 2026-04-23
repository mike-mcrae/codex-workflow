#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import json
from datetime import datetime
from pathlib import Path


TEMPLATE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BASE_DIR = Path.home() / "Documents" / "GitHub"
REAL_CODEX = "/opt/homebrew/bin/codex"
GH_BIN = shutil.which("gh") or "/opt/homebrew/bin/gh"


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


def command_output(cmd: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def ensure_canonical_structure(project_dir: Path) -> None:
    cleanup_script = project_dir / ".workflow" / "scripts" / "cleanup_structure.py"
    check = subprocess.run(
        ["python3", str(cleanup_script), "check"],
        cwd=str(project_dir),
        text=True,
        capture_output=True,
        check=False,
    )
    if check.returncode == 0:
        return

    fix = subprocess.run(
        ["python3", str(cleanup_script), "fix"],
        cwd=str(project_dir),
        text=True,
        capture_output=True,
        check=False,
    )
    if fix.returncode != 0:
        raise SystemExit(
            "The generated project failed the automatic structure repair step.\n"
            f"{fix.stdout}{fix.stderr}"
        )

    verify = subprocess.run(
        ["python3", str(cleanup_script), "check"],
        cwd=str(project_dir),
        text=True,
        capture_output=True,
        check=False,
    )
    if verify.returncode != 0:
        raise SystemExit(
            "The generated project still failed the structure check after repair.\n"
            f"{verify.stdout}{verify.stderr}"
        )


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


def prompt_yes_no(label: str, default: bool = True) -> bool:
    suffix = " [Y/n]" if default else " [y/N]"
    while True:
        value = input(f"{label}{suffix}: ").strip().lower()
        if not value:
            return default
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False


def gh_available() -> bool:
    return bool(shutil.which("gh") or Path(GH_BIN).exists())


def gh_is_authenticated() -> bool:
    if not gh_available():
        return False
    result = subprocess.run(
        [GH_BIN, "auth", "status"],
        text=True,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def gh_login() -> str:
    if not gh_is_authenticated():
        return ""
    try:
        return command_output([GH_BIN, "api", "user"]).strip()
    except Exception:
        return ""


def gh_username() -> str:
    if not gh_is_authenticated():
        return ""
    try:
        payload = json.loads(command_output([GH_BIN, "api", "user"]))
        return payload.get("login", "")
    except Exception:
        return ""


def require_github_ready(owner_hint: str) -> str:
    if not gh_available():
        raise SystemExit("GitHub CLI (`gh`) is required for automatic repo creation. Install it or use `--no-create-github-repo`.")
    if not gh_is_authenticated():
        raise SystemExit("Automatic GitHub repo creation requires a one-time login. Run `gh auth login`, then run `new_project` again.")
    owner = gh_username() or owner_hint
    if not owner:
        raise SystemExit("Could not determine GitHub username from `gh`. Set `--github-owner` explicitly.")
    return owner


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


def set_toml_value(text: str, key: str, value: str) -> str:
    return re.sub(
        rf'^{re.escape(key)} = ".*"$',
        f'{key} = "{value}"',
        text,
        flags=re.MULTILINE,
    )


def set_toml_bool(text: str, key: str, value: bool) -> str:
    return re.sub(
        rf"^{re.escape(key)} = (true|false)$",
        f"{key} = {'true' if value else 'false'}",
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
    path = project_dir / ".workflow" / "memory" / "session-log.md"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    block = "\n".join(
        [
            f"## {timestamp}: Project bootstrap",
            "",
            f"- Summary: Initialized the project template for {project_title}.",
            "- Inputs used: interactive new_project setup answers.",
            f"- Outputs produced: {project_name} repository scaffold, configured project files, and initial git repository.",
            "- Decisions and rationale: Accepted the default Codex academic workflow structure as the base project scaffold.",
            "- Open items: Codex should validate the project brief, decide whether deep intake is needed now, and create the first plan.",
            "- Next recommended action: Start Codex and begin the planning workflow.",
            "",
        ]
    )
    existing = read_text(path).rstrip() + "\n\n"
    write_text(path, existing + block)


def populate_project(project_dir: Path, answers: dict[str, str]) -> None:
    config_path = project_dir / ".workflow" / "config" / "project.toml"
    config = read_text(config_path)
    config = set_toml_value(config, "title", answers["title"])
    config = set_toml_value(config, "discipline", answers["discipline"])
    config = set_toml_value(config, "paper_type", answers["paper_type"])
    config = set_toml_bool(
        config,
        "dangerously_bypass_approvals_and_sandbox",
        answers["dangerously_bypass_approvals_and_sandbox"],
    )
    write_text(config_path, config)

    latex_path = project_dir / "manuscript" / "main.tex"
    latex = read_text(latex_path)
    latex = latex.replace(r"\title{Working Paper Title}", rf"\title{{{answers['title']}}}", 1)
    latex = latex.replace(r"\author{Author Name}", rf"\author{{{answers['author']}}}", 1)
    write_text(latex_path, latex)

    brief_path = project_dir / "notes" / "project-brief.md"
    brief = read_text(brief_path)
    brief = set_section_value(brief, "Working Title", answers["title"])
    brief = set_section_value(brief, "Project Description", answers["project_description"])
    brief = set_section_value(brief, "Project Status", answers["project_status"])
    brief = set_section_value(brief, "Intake Depth", answers["intake_depth"])
    brief = set_section_value(brief, "Research Question", answers["research_question"])
    brief = set_section_value(brief, "Why This Matters", answers["why_matters"])
    brief = set_section_value(brief, "Proposed Contribution", answers["contribution"])
    brief = set_section_value(brief, "Paper Type", answers["paper_type"])
    brief = set_section_value(brief, "Target Reader Or Journal", answers["target_journal"])
    brief = set_section_value(brief, "Constraints", answers["constraints"])
    brief = set_section_value(brief, "Non-Negotiables", answers["non_negotiables"])
    write_text(brief_path, brief)

    notes_path = project_dir / "notes" / "source-notes.md"
    notes = read_text(notes_path)
    notes = set_section_value(notes, "Key Papers", answers["key_papers"])
    notes = set_section_value(notes, "Data", answers["data"])
    notes = set_section_value(notes, "Identification Strategy Notes", answers["identification"])
    notes = set_section_value(notes, "Empirical Design Notes", answers["empirical_design"])
    notes = set_section_value(notes, "Open Questions", answers["open_questions"])
    notes = set_section_value(notes, "Citations To Verify", answers["citations_to_verify"])
    write_text(notes_path, notes)

    memory_path = project_dir / ".workflow" / "memory" / "MEMORY.md"
    memory = read_text(memory_path).rstrip() + "\n\n"
    memory += f"- `[PROJECT:title] {answers['title']}`\n"
    memory += f"- `[PROJECT:status] {answers['project_status']}`\n"
    memory += f"- `[PROJECT:intake_depth] {answers['intake_depth']}`\n"
    write_text(memory_path, memory)

    append_session_log(project_dir, answers["title"], answers["project_name"])


def init_git_repo(project_dir: Path) -> None:
    shell(["git", "init", "-b", "main"], cwd=project_dir)
    shell(["git", "add", "."], cwd=project_dir)
    shell(["git", "commit", "-m", "Bootstrap project from codex-workflow template"], cwd=project_dir)


def create_remote_repo(project_dir: Path, answers: dict[str, str]) -> None:
    if not answers["create_github_repo"]:
        return

    owner = answers["github_owner"]
    repo_name = answers["project_name"]
    visibility = answers["github_visibility"]
    description = answers["github_description"]
    cmd = [
        GH_BIN,
        "repo",
        "create",
        f"{owner}/{repo_name}",
        f"--{visibility}",
        "--source",
        ".",
        "--remote",
        "origin",
        "--push",
    ]
    if description:
        cmd.extend(["--description", description])
    shell(cmd, cwd=project_dir)


def build_codex_prompt(project_dir: Path, answers: dict[str, str]) -> str:
    starter = read_text(project_dir / "STARTER_PROMPT.md").strip()
    tail = "\n\nProject bootstrap notes:\n"
    tail += f"- Project folder: {answers['project_name']}\n"
    tail += f"- Project description: {answers['project_description']}\n"
    tail += f"- Project status: {answers['project_status']}\n"
    tail += f"- Intake depth: {answers['intake_depth']}\n"
    tail += "- The project files have already been pre-populated from the interactive setup.\n"
    if answers["intake_depth"] == "dig deeper now":
        tail += "- Ask the deeper intake questions now before substantial planning, then write the answers into the repo files.\n"
    else:
        tail += "- Do not front-load deeper intake. Proceed with the available information and defer deeper questions until `/more_input` or a genuine planning block.\n"
    tail += "- Continue until you need direct user input, then ask the user the next necessary question.\n"
    return starter + tail


def launch_codex(project_dir: Path, answers: dict[str, str]) -> int:
    launcher = project_dir / ".workflow" / "scripts" / "start_codex_session.sh"
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
    author = args.author or default_author
    discipline = args.discipline or "Economics"
    paper_type = args.paper_type or "Empirical paper"
    project_description = args.project_description or prompt("Describe the project in 2-3 sentences", required=True)
    project_status = args.project_status or prompt("Is this an existing project or a new project", default="existing project", required=True).lower()
    if project_status not in {"existing project", "new project"}:
        raise SystemExit("Project status must be `existing project` or `new project`.")
    intake_depth = args.intake_depth or prompt("Would you like me to dig deeper now or later", default="later", required=True).lower()
    if intake_depth not in {"now", "later"}:
        raise SystemExit("Intake depth must be `now` or `later`.")
    intake_depth_label = "dig deeper now" if intake_depth == "now" else "dig deeper later"
    bypass_sandbox = args.dangerously_bypass_approvals_and_sandbox
    if bypass_sandbox is None:
        bypass_sandbox = prompt_yes_no(
            "Allow Codex to bypass approvals and sandbox for this project",
            default=False,
        )
    research_question = args.research_question or "TBD during planning"
    why_matters = args.why_matters or project_description
    contribution = args.contribution or "TBD during planning"
    target_journal = args.target_journal or "TBD later"
    voice = args.voice or "Precise, formal, evidence-led"
    constraints = args.constraints or "TBD later"
    non_negotiables = args.non_negotiables or "Maintain rigorous academic standards."
    key_papers = args.key_papers or "TBD later"
    data = args.data or "TBD later"
    identification = args.identification or "TBD later"
    empirical_design = args.empirical_design or "TBD later"
    open_questions = args.open_questions or "TBD during planning"
    citations_to_verify = args.citations_to_verify or "TBD later"
    github_owner_default = args.github_owner or gh_username() or "mike-mcrae"
    create_github_repo = args.create_github_repo
    if create_github_repo is None:
        create_github_repo = True
    github_owner = args.github_owner or github_owner_default
    github_visibility = args.github_visibility or "private"
    github_description = args.github_description or f"Academic writing project: {title}"
    if github_visibility not in {"private", "public"}:
        raise SystemExit("GitHub visibility must be `private` or `public`.")
    if create_github_repo:
        github_owner = require_github_ready(github_owner)
    return {
        "project_name": slugify(project_name),
        "title": title,
        "author": author,
        "discipline": discipline,
        "paper_type": paper_type,
        "project_description": project_description,
        "project_status": project_status,
        "intake_depth": intake_depth_label,
        "dangerously_bypass_approvals_and_sandbox": bypass_sandbox,
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
        "create_github_repo": create_github_repo,
        "github_owner": github_owner,
        "github_visibility": github_visibility,
        "github_description": github_description,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a new project from the local Codex workflow template")
    parser.add_argument("--project-name", help="Folder name under the base directory")
    parser.add_argument("--title", help="Project title")
    parser.add_argument("--author", help="Author name")
    parser.add_argument("--discipline", help="Discipline label")
    parser.add_argument("--paper-type", help="Paper type")
    parser.add_argument("--project-description", help="Two to three sentence project description")
    parser.add_argument("--project-status", choices=["existing project", "new project"], help="Whether this is an existing or new project")
    parser.add_argument("--intake-depth", choices=["now", "later"], help="Whether to dig deeper now or later")
    parser.add_argument(
        "--dangerously-bypass-approvals-and-sandbox",
        dest="dangerously_bypass_approvals_and_sandbox",
        action="store_true",
        help="Launch Codex for this project with --dangerously-bypass-approvals-and-sandbox",
    )
    parser.add_argument(
        "--no-dangerously-bypass-approvals-and-sandbox",
        dest="dangerously_bypass_approvals_and_sandbox",
        action="store_false",
        help="Do not launch Codex for this project with --dangerously-bypass-approvals-and-sandbox",
    )
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
    parser.add_argument("--create-github-repo", dest="create_github_repo", action="store_true", help="Create and push a GitHub repository automatically")
    parser.add_argument("--no-create-github-repo", dest="create_github_repo", action="store_false", help="Do not create a GitHub repository automatically")
    parser.add_argument("--github-owner", help="GitHub username or organization")
    parser.add_argument("--github-visibility", choices=["private", "public"], help="GitHub repository visibility")
    parser.add_argument("--github-description", help="GitHub repository description")
    parser.add_argument("--no-launch", action="store_true", help="Create the project but do not launch Codex")
    parser.set_defaults(create_github_repo=None, dangerously_bypass_approvals_and_sandbox=None)
    args = parser.parse_args()

    answers = collect_answers(args)
    base_dir = Path(args.base_dir).expanduser().resolve()
    destination = base_dir / answers["project_name"]
    if destination.exists():
        raise SystemExit(f"Destination already exists: {destination}")
    base_dir.mkdir(parents=True, exist_ok=True)

    copy_template(destination)
    populate_project(destination, answers)
    ensure_canonical_structure(destination)
    init_git_repo(destination)
    create_remote_repo(destination, answers)

    print(f"Created project at {destination}")
    if args.no_launch:
        print("Skipping Codex launch because --no-launch was set.")
        return 0

    return launch_codex(destination, answers)


if __name__ == "__main__":
    raise SystemExit(main())
