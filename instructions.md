You are tasked with building a complete repository for a multi-agent academic writing workflow using Codex.

REFERENCE:
First, study and understand the structure, logic, and workflow of:
https://github.com/pedrohcgs/claude-code-my-workflow

You must NOT copy it directly. You must extract the underlying architecture:
- multi-agent system
- plan → execute → review → refine loop
- strict workflow rules
- persistent memory via files

---

PHASE 1: PLANNING (MANDATORY)

Enter planning mode.

- Analyse the reference repository
- Identify all core components (agents, workflow, memory, orchestration)
- Design an equivalent system adapted for Codex (no Claude-specific features)
- Define:
  - repository structure
  - agent roles
  - workflow rules
  - prompt templates
  - orchestration logic

Do NOT generate any files yet.
Do NOT output anything to the user.

---

PHASE 2: BUILD

After planning is complete, build the full repository.

Requirements:
- Create a clean, modular repo for academic writing workflows
- Include:
  - agent definitions (planner, writer, reviewer, adversarial reviewer, etc.)
  - workflow specification enforcing plan → write → review → refine
  - prompt templates for each stage
  - a simple orchestrator script (Python)
  - LaTeX-ready output structure
- Ensure the system is reusable and extensible

---

CRITICAL RULES

- The system must enforce:
  - planning before writing
  - mandatory review stages
  - iterative refinement
- The design should reflect high-level academic standards (economics papers, rigorous reasoning)

---

FINAL OUTPUT

Only output the final repository.

Do NOT include:
- planning notes
- analysis of the reference repo
- intermediate reasoning
- explanations

The output should be a clean, ready-to-use repository that can be pushed directly to GitHub.

