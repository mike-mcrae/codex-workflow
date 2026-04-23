# Code Audit Packet

Read the following inputs:

- Agent definition: `{agent_definition_path}`
- Workflow rules: `{workflow_spec_path}`
- Quality gates: `{quality_gates_path}`
- Memory protocol: `{memory_protocol_path}`
- Curated memory: `{memory_path}`
- Session log: `{session_log_path}`
- Decision index: `{decisions_index_path}`
- Target file: `{target_file_path}`

Task:

- Audit the target code file and write the report at `{output_path}` using `{report_template_path}`.
- Focus on correctness, reproducibility, and research workflow risks.
- Use language-specific standards for `{language}`.
- Distinguish critical, major, and minor issues.
- Recommend `approve`, `revise`, or `reject`.
