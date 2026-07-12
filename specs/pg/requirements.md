---
spec: pg.spec.md
---

## User Stories

- As a developer, I want to run ad-hoc queries against a Postgres database with a single command
- As a developer, I want query results in JSON, CSV, list, or table form
- As a developer, I want to bind untrusted values without risking SQL injection
- As an AI agent, I want destructive statements refused by default so I cannot silently destroy data

## Acceptance Criteria

### REQ-pg-001

`fledge pg query` executes SQL and returns the selected table, JSON, CSV, or list format.

### REQ-pg-002

`fledge pg schema` shows tables, views, and indexes for user schemas.

### REQ-pg-003

Connection resolution uses explicit `--url` before `DATABASE_URL` and fails before execution when neither exists.

### REQ-pg-004

Destructive statements are refused unless `--allow-destructive` is passed.

### REQ-pg-005

`--param name=value` binds values safely and rejects invalid names or injection attempts.

### REQ-pg-006

All commands use the fledge-v1 protocol for input, output, and host execution.

## Constraints

- Must work without any dependencies beyond `psql` and `jq`
- Shell script implementation (no compile step)
- No OS keychain or external state beyond the target database

## Out of Scope

- GUI or TUI interfaces
- Database/server provisioning (`init`) and migration tracking (`migrate`)
- An audit log (the Merlin-internal pgrun keeps one; this plugin does not)
- Replication or backup
