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

`fledge pg query` SHALL execute SQL and return the selected table, JSON, CSV, or list format.

Acceptance Criteria
- Offline and hosted query cases validate supported output formats.

### REQ-pg-002

`fledge pg schema` SHALL show tables, views, and indexes for user schemas.

### REQ-pg-003

Connection resolution SHALL use explicit `--url` before `DATABASE_URL` and SHALL fail before execution when neither exists.

### REQ-pg-004

Destructive statements SHALL be refused unless `--allow-destructive` is passed.

### REQ-pg-005

`--param name=value` SHALL bind values safely and reject invalid names or injection attempts.

### REQ-pg-006

All commands SHALL use the fledge-v1 protocol for input, output, and host execution.

## Constraints

- Must work without any dependencies beyond `psql` and `jq`
- Shell script implementation (no compile step)
- No OS keychain or external state beyond the target database

## Out of Scope

- GUI or TUI interfaces
- Database/server provisioning (`init`) and migration tracking (`migrate`)
- An audit log (the Merlin-internal pgrun keeps one; this plugin does not)
- Replication or backup
