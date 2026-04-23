# Refinement Packet

Read the following inputs:

- Workflow rules: `{workflow_spec_path}`
- Memory protocol: `{memory_protocol_path}`
- Curated memory: `{memory_path}`
- Topic memory index: `{memory_topics_path}`
- Session log: `{session_log_path}`
- Decision index: `{decisions_index_path}`
- Current draft: `{draft_path}`
- Review summary: `{review_summary_path}`
- Underlying review reports:
{review_report_list}

Task:

- Write the revision log at `{output_path}` using `{revision_template_path}`.
- Resolve major issues first, then minor issues.
- Explain what changed, what remains unresolved, and why.
- Update the manuscript directly where appropriate and record the resulting revised text in the log.
- Do not silently ignore objections from any reviewer.
- If a review challenge conflicts with a settled design choice, cite Layer 2 instead of silently overturning it.
- Read Layer 1 and the latest 3 to 5 Layer 3 entries before revising.
