---
change: CHG-0001-adopt-specsync-5-0-1-and-trust-1-0-0-governance-for-the-postgres-fledge-plugin
artifact: testing
---

# Testing

Local acceptance requires ShellCheck, syntax, 20 offline gate cases, manifest validation, strict SpecSync checks at threshold 0, four integrations, healthy Trust doctor, and a clean diff.

Hosted acceptance additionally requires the Postgres 16-backed query, format, parameter, injection, schema, and destructive-override cases in both the existing test job and unified Trust gate.
