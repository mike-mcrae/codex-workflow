# Review Packet

Read the following inputs:

- Agent definition: `{agent_definition_path}`
- Workflow rules: `{workflow_spec_path}`
- Memory protocol: `{memory_protocol_path}`
- Quality gates: `{quality_gates_path}`
- Curated memory: `{memory_path}`
- Topic memory index: `{memory_topics_path}`
- Session log: `{session_log_path}`
- Decision index: `{decisions_index_path}`
- Current draft: `{draft_path}`
- Approved plan: `{plan_path}`
- Project brief: `{project_brief_path}`

Task:

- Produce a full review report at `{output_path}` using `{review_template_path}`.
- Fill in machine-readable frontmatter completely.
- Distinguish major issues from minor issues.
- Recommend `approve`, `revise`, or `reject`.
- Tie comments to concrete sections and repair actions.
- Respect the memory protocol: use Layer 1 and the latest 3 to 5 Layer 3 entries for context, Layer 2 only for settled prior rationale, and Layer 4 only for exact retrieval.
