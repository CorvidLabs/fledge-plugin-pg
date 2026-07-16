---
id: CHG-0001-adopt-specsync-5-0-1-and-trust-1-0-0-governance-for-the-postgres-fledge-plugin
state: archived
type: migration
base_commit: 84c638c4b7c118df30ab1ae1711497f69df38419
---

# Adopt SpecSync 5.0.1 and Trust 1.0.0 governance for the Postgres Fledge plugin

## Intent

Adopt SpecSync 5.0.1 and Trust 1.0.0 governance for the Postgres Fledge plugin

## Affected Canonical Specs

- `pg`

## Acceptance Criteria

- SpecSync strict checks pass at explicit advisory threshold 0 for the extensionless Bash executable.
- Existing requirements have deterministic IDs.
- All four integrations are installed.
- Trust doctor and verification pass.
- ShellCheck, syntax, 20 offline gate tests, hosted Postgres integration tests, and manifest validation remain green.

## No-spec Rationale

Not applicable
