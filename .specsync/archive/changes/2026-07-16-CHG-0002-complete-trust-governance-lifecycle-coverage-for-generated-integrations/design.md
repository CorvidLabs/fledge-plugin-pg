---
change: CHG-0002-complete-trust-governance-lifecycle-coverage-for-generated-integrations
artifact: design
---

# Design

Use a no-spec lifecycle record whose affected paths exactly cover `.attest.json`,
`.augur.toml`, `.claude/`, `.codex/`, `.cursor/`, `.gemini/`, and `AGENTS.md`.
The record contains no semantic delta because those files configure governance
and agent guidance; they do not alter the `pg` command contract.

Keep CHG-0001 and its prior approvals, reopening, and verification evidence
intact. The unified Trust workflow and PostgreSQL test service remain unchanged.
