#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tomllib
from datetime import datetime
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / ".workflow/config/project.toml"
QUALITY_PATH = ROOT / ".workflow/config/quality_gates.toml"
WORKFLOW_SPEC_PATH = ROOT / ".workflow/protocols/specification.md"
MEMORY_PROTOCOL_PATH = ROOT / ".workflow/protocols/memory-protocol.md"
MEMORY_PATH = ROOT / ".workflow/memory/MEMORY.md"
MEMORY_TOPICS_PATH = ROOT / ".workflow/memory/topics/README.md"
SESSION_LOG_PATH = ROOT / ".workflow/memory/session-log.md"
DECISIONS_INDEX_PATH = ROOT / ".workflow/decisions/INDEX.md"
PROJECT_BRIEF_PATH = ROOT / "notes/project-brief.md"
SOURCE_NOTES_PATH = ROOT / "notes/source-notes.md"
RUNS_DIR = ROOT / ".workflow/state/runs"

STAGE_TO_TEMPLATE = {
    "planning": ROOT / ".workflow/templates/plan.md",
    "writing": ROOT / ".workflow/templates/draft.md",
    "review": ROOT / ".workflow/templates/review-report.md",
    "refinement": ROOT / ".workflow/templates/revision-log.md",
}

STAGE_TO_PROMPT = {
    "planning": ROOT / ".workflow/prompts/planner.md",
    "writing": ROOT / ".workflow/prompts/writer.md",
    "review": ROOT / ".workflow/prompts/reviewer.md",
    "refinement": ROOT / ".workflow/prompts/refiner.md",
}

AGENT_PATHS = {
    "planner": ROOT / ".workflow/agents/planner.md",
    "writer": ROOT / ".workflow/agents/writer.md",
    "reviewer": ROOT / ".workflow/agents/reviewer.md",
    "methods-referee": ROOT / ".workflow/agents/methods-referee.md",
    "adversarial-reviewer": ROOT / ".workflow/agents/adversarial-reviewer.md",
    "final-editor": ROOT / ".workflow/agents/final-editor.md",
}


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_toml(path: Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "run"


def relative_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def latest_run_id() -> str | None:
    runs = sorted((path for path in RUNS_DIR.iterdir() if path.is_dir()), key=lambda item: item.name)
    return runs[-1].name if runs else None


def resolve_run_id(run_id: str | None) -> str:
    resolved = run_id or latest_run_id()
    if not resolved:
        raise SystemExit("No run found. Start one with `init-run`.")
    return resolved


def run_dir(run_id: str) -> Path:
    return RUNS_DIR / run_id


def state_path(run_id: str) -> Path:
    return run_dir(run_id) / "state.json"


def load_state(run_id: str) -> dict:
    path = state_path(run_id)
    if not path.exists():
        raise SystemExit(f"Run state not found for `{run_id}`.")
    return json.loads(read_text(path))


def save_state(run_id: str, state: dict) -> None:
    state["updated_at"] = now_iso()
    write_text(state_path(run_id), json.dumps(state, indent=2) + "\n")


def parse_frontmatter(path: Path) -> dict:
    text = read_text(path)
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}
    metadata: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip()
    return metadata


def stamped_template(template_path: Path, replacements: dict[str, str]) -> str:
    content = read_text(template_path)
    for key, value in replacements.items():
        pattern = rf"^{re.escape(key)}:\s*$"
        content = re.sub(pattern, f"{key}: {value}", content, flags=re.MULTILINE)
    return content


def render_prompt(template_path: Path, context: dict[str, str]) -> str:
    class SafeDict(dict):
        def __missing__(self, key: str) -> str:
            return "{" + key + "}"

    return read_text(template_path).format_map(SafeDict(context))


def review_stub_path(run_id: str, cycle: int, agent: str) -> Path:
    return run_dir(run_id) / "artifacts" / f"review_cycle{cycle}_{agent}.md"


def draft_stub_path(run_id: str, cycle: int) -> Path:
    return run_dir(run_id) / "artifacts" / f"draft_cycle{cycle}.md"


def revision_stub_path(run_id: str, cycle: int) -> Path:
    return run_dir(run_id) / "artifacts" / f"revision_cycle{cycle}.md"


def plan_stub_path(run_id: str) -> Path:
    return run_dir(run_id) / "artifacts" / "plan.md"


def review_summary_path(run_id: str, cycle: int) -> Path:
    return run_dir(run_id) / "artifacts" / f"review_cycle{cycle}_summary.md"


def packet_path(run_id: str, label: str) -> Path:
    return run_dir(run_id) / "packets" / label


def latest_draft_path(state: dict, run_id: str) -> Path:
    drafts = state["artifacts"]["drafts"]
    if drafts:
        return ROOT / drafts[-1]
    return draft_stub_path(run_id, state["cycle"])


def copy_if_needed(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.resolve() == target.resolve():
        return
    shutil.copyfile(source, target)


def build_base_context(run_id: str, state: dict, config: dict) -> dict[str, str]:
    workflow = config["workflow"]
    latex_root = ROOT / workflow["latex_root"]
    latest_draft = latest_draft_path(state, run_id)
    return {
        "run_id": run_id,
        "cycle": str(state["cycle"]),
        "workflow_spec_path": relative_path(WORKFLOW_SPEC_PATH),
        "memory_protocol_path": relative_path(MEMORY_PROTOCOL_PATH),
        "project_config_path": relative_path(CONFIG_PATH),
        "quality_gates_path": relative_path(QUALITY_PATH),
        "memory_path": relative_path(MEMORY_PATH),
        "memory_topics_path": relative_path(MEMORY_TOPICS_PATH),
        "session_log_path": relative_path(SESSION_LOG_PATH),
        "decisions_index_path": relative_path(DECISIONS_INDEX_PATH),
        "project_brief_path": relative_path(PROJECT_BRIEF_PATH),
        "source_notes_path": relative_path(SOURCE_NOTES_PATH),
        "latex_root_path": relative_path(latex_root),
        "plan_template_path": relative_path(STAGE_TO_TEMPLATE["planning"]),
        "draft_template_path": relative_path(STAGE_TO_TEMPLATE["writing"]),
        "review_template_path": relative_path(STAGE_TO_TEMPLATE["review"]),
        "revision_template_path": relative_path(STAGE_TO_TEMPLATE["refinement"]),
        "plan_path": relative_path(plan_stub_path(run_id)),
        "draft_path": relative_path(latest_draft),
        "review_summary_path": relative_path(review_summary_path(run_id, state["cycle"])),
    }


def ensure_artifact_stub(path: Path, template_path: Path, replacements: dict[str, str]) -> None:
    if path.exists():
        return
    write_text(path, stamped_template(template_path, replacements))


def init_run(args: argparse.Namespace) -> int:
    config = load_toml(CONFIG_PATH)
    title = args.title or config["project"]["title"]
    base_run_id = f"{datetime.now().strftime('%Y%m%d')}-{slugify(title)}"
    run_id = base_run_id
    counter = 2
    while run_dir(run_id).exists():
        run_id = f"{base_run_id}-{counter}"
        counter += 1

    current_run = run_dir(run_id)
    (current_run / "packets").mkdir(parents=True, exist_ok=True)
    (current_run / "artifacts").mkdir(parents=True, exist_ok=True)

    state = {
        "run_id": run_id,
        "title": title,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "stage": "planning",
        "cycle": 1,
        "required_reviewers": config["workflow"]["required_reviewers"],
        "max_refinement_rounds": config["workflow"]["max_refinement_rounds"],
        "artifacts": {
            "plan": None,
            "drafts": [],
            "reviews": {},
            "review_summaries": [],
            "refinements": [],
        },
        "history": [
            {"timestamp": now_iso(), "event": "run-created", "stage": "planning"}
        ],
    }
    save_state(run_id, state)
    prepare_stage(argparse.Namespace(run=run_id))
    print(f"Created run: {run_id}")
    return 0


def prepare_stage(args: argparse.Namespace) -> int:
    run_id = resolve_run_id(getattr(args, "run", None))
    state = load_state(run_id)
    config = load_toml(CONFIG_PATH)
    context = build_base_context(run_id, state, config)
    stage = state["stage"]

    if stage == "blocked":
        print(f"Run `{run_id}` is blocked. Resolve issues manually before continuing.")
        return 1
    if stage == "complete":
        print(f"Run `{run_id}` is complete.")
        return 0

    if stage == "planning":
        output = plan_stub_path(run_id)
        ensure_artifact_stub(
            output,
            STAGE_TO_TEMPLATE["planning"],
            {"run_id": run_id, "created_at": now_iso()},
        )
        context.update(
            {
                "agent_definition_path": relative_path(AGENT_PATHS["planner"]),
                "output_path": relative_path(output),
            }
        )
        packet = render_prompt(STAGE_TO_PROMPT["planning"], context)
        write_text(packet_path(run_id, "planning_packet.md"), packet)
        print(relative_path(packet_path(run_id, "planning_packet.md")))
        return 0

    if stage == "writing":
        output = draft_stub_path(run_id, state["cycle"])
        ensure_artifact_stub(
            output,
            STAGE_TO_TEMPLATE["writing"],
            {"run_id": run_id, "cycle": str(state["cycle"]), "created_at": now_iso()},
        )
        context.update(
            {
                "agent_definition_path": relative_path(AGENT_PATHS["writer"]),
                "output_path": relative_path(output),
            }
        )
        packet = render_prompt(STAGE_TO_PROMPT["writing"], context)
        write_text(packet_path(run_id, f"writing_cycle{state['cycle']}.md"), packet)
        print(relative_path(packet_path(run_id, f"writing_cycle{state['cycle']}.md")))
        return 0

    if stage == "review":
        written_packets: list[str] = []
        for agent in state["required_reviewers"]:
            output = review_stub_path(run_id, state["cycle"], agent)
            ensure_artifact_stub(
                output,
                STAGE_TO_TEMPLATE["review"],
                {
                    "run_id": run_id,
                    "agent": agent,
                    "cycle": str(state["cycle"]),
                    "created_at": now_iso(),
                },
            )
            context.update(
                {
                    "agent_definition_path": relative_path(AGENT_PATHS[agent]),
                    "output_path": relative_path(output),
                }
            )
            packet = render_prompt(STAGE_TO_PROMPT["review"], context)
            packet_file = packet_path(run_id, f"review_cycle{state['cycle']}_{agent}.md")
            write_text(packet_file, packet)
            written_packets.append(relative_path(packet_file))
        print("\n".join(written_packets))
        return 0

    if stage == "refinement":
        output = revision_stub_path(run_id, state["cycle"])
        ensure_artifact_stub(
            output,
            STAGE_TO_TEMPLATE["refinement"],
            {
                "run_id": run_id,
                "cycle": str(state["cycle"]),
                "source_review_cycle": str(state["cycle"]),
                "created_at": now_iso(),
            },
        )
        reports = [
            f"- {relative_path(review_stub_path(run_id, state['cycle'], agent))}"
            for agent in state["required_reviewers"]
        ]
        context.update(
            {
                "draft_path": relative_path(latest_draft_path(state, run_id)),
                "review_summary_path": relative_path(review_summary_path(run_id, state["cycle"])),
                "review_report_list": "\n".join(reports),
                "output_path": relative_path(output),
            }
        )
        packet = render_prompt(STAGE_TO_PROMPT["refinement"], context)
        packet_file = packet_path(run_id, f"refinement_cycle{state['cycle']}.md")
        write_text(packet_file, packet)
        print(relative_path(packet_file))
        return 0

    raise SystemExit(f"Unsupported stage: {stage}")


def require_stage(meta: dict, expected: str, path: Path) -> None:
    actual = meta.get("stage")
    if actual != expected:
        raise SystemExit(f"`{relative_path(path)}` has stage `{actual}`; expected `{expected}`.")


def require_int(meta: dict, key: str, path: Path) -> int:
    value = meta.get(key)
    if value is None:
        raise SystemExit(f"`{relative_path(path)}` is missing `{key}` in frontmatter.")
    try:
        return int(value)
    except ValueError as exc:
        raise SystemExit(f"`{relative_path(path)}` has non-integer `{key}`.") from exc


def synthesize_reviews(run_id: str, state: dict) -> tuple[Path, dict]:
    cycle = state["cycle"]
    reviews = state["artifacts"]["reviews"].get(str(cycle), {})
    total_major = 0
    total_minor = 0
    decisions: list[str] = []
    rows: list[str] = []
    for agent in state["required_reviewers"]:
        path = ROOT / reviews[agent]
        meta = parse_frontmatter(path)
        major = require_int(meta, "major_issues_open", path)
        minor = require_int(meta, "minor_issues_open", path)
        decision = meta.get("overall_decision", "revise")
        total_major += major
        total_minor += minor
        decisions.append(decision)
        rows.append(
            f"| {agent} | {decision} | {major} | {minor} | {relative_path(path)} |"
        )

    approved = all(decision == "approve" for decision in decisions) and total_major == 0
    summary = {
        "cycle": cycle,
        "total_major_issues_open": total_major,
        "total_minor_issues_open": total_minor,
        "all_approved": approved,
    }

    body = "\n".join(
        [
            f"# Review Summary: Cycle {cycle}",
            "",
            f"- `total_major_issues_open`: {total_major}",
            f"- `total_minor_issues_open`: {total_minor}",
            f"- `all_approved`: {'true' if approved else 'false'}",
            "",
            "| Agent | Decision | Major Issues | Minor Issues | Report |",
            "| --- | --- | ---: | ---: | --- |",
            *rows,
            "",
            "## Synthesis",
            "",
            "Read the underlying reports before revising. Resolve major issues first and document any disagreements explicitly.",
            "",
        ]
    )
    path = review_summary_path(run_id, cycle)
    write_text(path, body)
    return path, summary


def submit(args: argparse.Namespace) -> int:
    run_id = resolve_run_id(getattr(args, "run", None))
    state = load_state(run_id)
    config = load_toml(CONFIG_PATH)
    artifact = (ROOT / args.artifact).resolve() if not Path(args.artifact).is_absolute() else Path(args.artifact)
    if not artifact.exists():
        raise SystemExit(f"Artifact not found: {artifact}")

    stage = state["stage"]
    meta = parse_frontmatter(artifact)

    if stage == "planning":
        require_stage(meta, "planning", artifact)
        status = meta.get("status")
        minimum = load_toml(QUALITY_PATH)["thresholds"]["minimum_plan_status"]
        if status != minimum:
            raise SystemExit(f"Plan must have `status: {minimum}` before writing can begin.")
        canonical = plan_stub_path(run_id)
        copy_if_needed(artifact, canonical)
        state["artifacts"]["plan"] = relative_path(canonical)
        state["stage"] = "writing"
        state["history"].append({"timestamp": now_iso(), "event": "plan-approved", "stage": "writing"})
        save_state(run_id, state)
        print(f"Accepted plan. Next stage: writing ({run_id}).")
        return 0

    if stage == "writing":
        require_stage(meta, "writing", artifact)
        canonical = draft_stub_path(run_id, state["cycle"])
        copy_if_needed(artifact, canonical)
        state["artifacts"]["drafts"].append(relative_path(canonical))
        state["stage"] = "review"
        state["history"].append(
            {
                "timestamp": now_iso(),
                "event": "draft-submitted",
                "stage": "review",
                "cycle": state["cycle"],
            }
        )
        save_state(run_id, state)
        print(f"Accepted draft. Next stage: review cycle {state['cycle']}.")
        return 0

    if stage == "review":
        agent = args.agent or meta.get("agent")
        if not agent:
            raise SystemExit("Review submission requires `--agent` or `agent:` frontmatter.")
        if agent not in state["required_reviewers"]:
            raise SystemExit(f"`{agent}` is not a configured reviewer.")
        require_stage(meta, "review", artifact)
        if meta.get("agent") and meta["agent"] != agent:
            raise SystemExit("`--agent` does not match the artifact frontmatter.")
        require_int(meta, "major_issues_open", artifact)
        require_int(meta, "minor_issues_open", artifact)
        if meta.get("overall_decision") not in {"approve", "revise", "reject"}:
            raise SystemExit("Review reports must set `overall_decision` to approve, revise, or reject.")

        canonical = review_stub_path(run_id, state["cycle"], agent)
        copy_if_needed(artifact, canonical)
        state["artifacts"]["reviews"].setdefault(str(state["cycle"]), {})[agent] = relative_path(canonical)
        state["history"].append(
            {
                "timestamp": now_iso(),
                "event": "review-submitted",
                "stage": "review",
                "cycle": state["cycle"],
                "agent": agent,
            }
        )

        submitted = state["artifacts"]["reviews"][str(state["cycle"])]
        missing = [name for name in state["required_reviewers"] if name not in submitted]
        if missing:
            save_state(run_id, state)
            print("Review accepted. Still missing: " + ", ".join(missing))
            return 0

        summary_file, summary = synthesize_reviews(run_id, state)
        state["artifacts"]["review_summaries"].append(relative_path(summary_file))
        refinements_done = len(state["artifacts"]["refinements"])
        if refinements_done == 0:
            state["stage"] = "refinement"
            next_stage = "refinement"
        elif summary["all_approved"]:
            state["stage"] = "complete"
            next_stage = "complete"
        elif refinements_done >= state["max_refinement_rounds"]:
            state["stage"] = "blocked"
            next_stage = "blocked"
        else:
            state["stage"] = "refinement"
            next_stage = "refinement"

        state["history"].append(
            {
                "timestamp": now_iso(),
                "event": "review-cycle-closed",
                "stage": next_stage,
                "cycle": state["cycle"],
                "summary": summary,
            }
        )
        save_state(run_id, state)
        print(f"Review cycle {state['cycle']} closed. Next stage: {next_stage}.")
        return 0

    if stage == "refinement":
        require_stage(meta, "refinement", artifact)
        require_int(meta, "resolved_major_issues", artifact)
        require_int(meta, "unresolved_major_issues", artifact)
        canonical = revision_stub_path(run_id, state["cycle"])
        copy_if_needed(artifact, canonical)
        state["artifacts"]["refinements"].append(relative_path(canonical))
        state["cycle"] += 1
        state["stage"] = "review"
        state["history"].append(
            {
                "timestamp": now_iso(),
                "event": "refinement-submitted",
                "stage": "review",
                "cycle": state["cycle"],
            }
        )
        save_state(run_id, state)
        print(f"Accepted refinement. Next stage: review cycle {state['cycle']}.")
        return 0

    raise SystemExit(f"Cannot submit while run is in `{stage}`.")


def status(args: argparse.Namespace) -> int:
    run_id = resolve_run_id(getattr(args, "run", None))
    state = load_state(run_id)
    print(f"run_id: {run_id}")
    print(f"title: {state['title']}")
    print(f"stage: {state['stage']}")
    print(f"cycle: {state['cycle']}")
    print(f"required_reviewers: {', '.join(state['required_reviewers'])}")

    if state["stage"] == "review":
        submitted = state["artifacts"]["reviews"].get(str(state["cycle"]), {})
        missing = [name for name in state["required_reviewers"] if name not in submitted]
        print("missing_reviewers: " + (", ".join(missing) if missing else "none"))

    if state["artifacts"]["plan"]:
        print(f"plan: {state['artifacts']['plan']}")
    if state["artifacts"]["drafts"]:
        print(f"latest_draft: {state['artifacts']['drafts'][-1]}")
    if state["artifacts"]["review_summaries"]:
        print(f"latest_review_summary: {state['artifacts']['review_summaries'][-1]}")
    if state["artifacts"]["refinements"]:
        print(f"latest_refinement: {state['artifacts']['refinements'][-1]}")

    next_action = {
        "planning": "Run `prepare-stage`, complete the planning packet, and submit the approved plan.",
        "writing": "Run `prepare-stage`, complete the writing packet, and submit the draft.",
        "review": "Run `prepare-stage`, complete all required review packets, and submit each report.",
        "refinement": "Run `prepare-stage`, address the review summary, and submit the revision log.",
        "complete": "Optional: use `prompts/final-audit.md` with `agents/final-editor.md` to polish the approved draft.",
        "blocked": "Manual intervention required. Review the latest review summary and revision history.",
    }
    print("next_action: " + next_action[state["stage"]])
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Codex academic workflow orchestrator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_cmd = subparsers.add_parser("init-run", help="Create a new workflow run")
    init_cmd.add_argument("--title", help="Override the project title for this run")
    init_cmd.set_defaults(func=init_run)

    stage_cmd = subparsers.add_parser("prepare-stage", help="Generate prompt packets for the current stage")
    stage_cmd.add_argument("--run", help="Run identifier")
    stage_cmd.set_defaults(func=prepare_stage)

    submit_cmd = subparsers.add_parser("submit", help="Submit an artifact for the current stage")
    submit_cmd.add_argument("--run", help="Run identifier")
    submit_cmd.add_argument("--artifact", required=True, help="Path to the completed artifact")
    submit_cmd.add_argument("--agent", help="Reviewer name for review submissions")
    submit_cmd.set_defaults(func=submit)

    status_cmd = subparsers.add_parser("status", help="Show the current run status")
    status_cmd.add_argument("--run", help="Run identifier")
    status_cmd.set_defaults(func=status)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
