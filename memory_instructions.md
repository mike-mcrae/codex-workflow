Here's a question people ask once they start using AI agents like Claude or ChatGPT for real work: the AI forgets everything between conversations, so how do you give it a memory that persists across sessions?

The standard answer, and the one I started with, is simple: keep a markdown file called something like MEMORY.md in the project folder, and tell the AI to read it at the start of every session. Everything the AI should know goes in that one file. Decisions, facts, open tasks, context on the project, reminders of your preferences. One place, easy to find, easy to edit.

It works for a while. Then it breaks. One file conflates four different questions with four different access costs. It bloats the context with history that doesn't belong there. You re-litigate settled decisions because the rationale isn't written down anywhere. You lose track of what shipped last week. The long tail of specific commands, error messages, and user quotes from past sessions is gone entirely. One file answers none of these questions well.

I now run four layers. Each one does something the other three cannot do cheaply. Remove any of them and a specific class of work breaks.

Layer 1, curated fact auto-loaded into every session, at two scopes. Global rules live in ~/.claude/CLAUDE.md and apply across every project (the email-approval rule below, editorial preferences, always-on safety rules). Project-specific facts live in MEMORY.md with detail spilled into memory/*.md topic files. Both are subject to a rough 200-line soft limit because anything past that truncates or costs tokens every session. Everything here has to earn its place. Stale facts are worse than missing ones.

Layer 2, decisions/YYYY-MM-DD-topic.md: append-only, dated, one file per decision. Each file has the choice made, the rationale, and the alternatives considered and rejected. It is never auto-loaded. I cite it on demand when a settled question resurfaces. Without this, the same tradeoff gets re-litigated.

Layer 3, session-log.md: structured entries written at session end (summary, inputs, outputs, open items). Read at session start. Prevents the "where did we leave off" problem on resume. Not curated for permanence; a rolling window.

Layer 4, QMD sessions-md (raw transcripts): every session exports automatically via a SessionEnd hook. Searchable via BM25 and vector index. This is where I look when I say "we did this before" and I need the exact command or error string. Noisy and complete. Never in context; always retrievable.

Four examples, one per layer, across different workflows.

Layer 1: A rule I want to apply every time I work with any of my assistants: never send an email without showing me the draft first and waiting for my approval. Show me the text in the conversation, let me approve or edit, then send. Never send without approval; never make me leave the session to hit send from somewhere else. That rule has to fire automatically, every session, without me having to invoke it or remember it. It lives in Layer 1. If it lived in Layer 4 I would have to remember to search for it before every email-related task, which defeats the point. Remembering is precisely the thing agents are bad at.

Layer 2: I have a separate assistant that handles tech-support tickets (broken MCP servers, failed hooks, tool errors across my other projects). Architectural choices I made months ago get questioned when something breaks and the alternatives start looking better than I remember. Layer 2 preserves the rejected alternatives and the reasoning. When I start to re-propose something we ruled out, two minutes of re-reading settles it.

Layer 3: I draft long-form analysis memos in sessions that stretch across days, because data pulls take hours and the argument evolves as the numbers come in. Layer 3's structured entries capture what I shipped, what inputs I used, and what is still open. The next morning I read the last entry and I know where to pick up, without re-reading a day of back-and-forth.

Layer 4: A background script on one of my projects started silently failing last month. I remembered hitting a similar error earlier but could not remember the fix. The raw transcript archive had the exact error string and the shell command that had unblocked it, detail nobody thought to curate. Without Layer 4 I would have debugged from scratch.

The differentiator is access pattern, not content. Layer 1 is always in context (zero discovery cost, real bloat risk). Layer 2 is cited on demand. Layer 3 is read at session start. Layer 4 is searched on demand. I don't think you can collapse these: you either pollute the context or lose retrieval.

Before defending the overhead, I should say this is more structure than most people want. But I have actually hit each failure mode: context bloat from over-logging, re-litigated decisions, lost resume state, gone long tail. The index update and session log are handled by /memory, /log, and /mexit skills. The transcript export is automatic. Pruning the index is manual and ongoing, not a one-time setup.