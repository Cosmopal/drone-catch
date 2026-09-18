---
tags:
  - agent-loop
---

# Memory mirror — machine-local session memory, committed

Snapshot (2026-09-19) of the meta-observer session's machine-local memory dir
(`~/.claude/projects/<project-key>/memory/`), which is auto-loaded into Claude
Code sessions but NOT otherwise in git. On a new machine, copy these files
into that directory (see [[team-workflow|team-workflow.md]] §3 step 4), then
keep the mirror in sync when memories change. `MEMORY.md` is the index the
session loads; the other files are one durable fact each, with frontmatter.
