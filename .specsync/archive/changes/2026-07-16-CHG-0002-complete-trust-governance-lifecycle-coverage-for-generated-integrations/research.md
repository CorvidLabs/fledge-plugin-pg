---
change: CHG-0002-complete-trust-governance-lifecycle-coverage-for-generated-integrations
artifact: research
---

# Research

The failed hosted Trust run executed ShellCheck, Bash syntax, manifest validation,
20 offline cases, and 13 PostgreSQL-backed cases for a total of 33 passing tests.
Its contract phase then reported the generated integrations, `.attest.json`,
`.augur.toml`, and `AGENTS.md` as meaningful paths without active-change
coverage. The failure is therefore a lifecycle-scope defect rather than a plugin
or database-test failure.

SpecSync 5.0.1 reports 100% coverage for this extensionless Bash repository as
0 of 0 discoverable files while the committed Trust threshold remains advisory
zero with native ShellCheck, syntax, manifest, and integration checks blocking.
