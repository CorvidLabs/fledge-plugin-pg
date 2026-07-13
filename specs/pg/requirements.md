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

Acceptance Criteria

- Against a database containing a user table, text and JSON schema output identify that table.
- Schema queries exclude `pg_catalog` and `information_schema` objects.

### REQ-pg-003

Connection resolution SHALL use explicit `--url` before `DATABASE_URL` and SHALL fail before execution when neither exists.

Acceptance Criteria

- When both sources are present, the generated `psql` command uses the explicit `--url` value.
- When neither source is present, the command emits the missing-URL error without requesting host execution.

### REQ-pg-004

Destructive statements SHALL be refused unless `--allow-destructive` is passed.

Acceptance Criteria

- Standalone destructive SQL keywords are blocked case-insensitively across whitespace and punctuation boundaries.
- Embedded substrings such as `dropped_at` remain allowed, and `--allow-destructive` permits the guarded statement to execute.

### REQ-pg-005

`--param name=value` SHALL bind values safely and reject invalid names or injection attempts.

Acceptance Criteria

- Parameter names outside `[A-Za-z_][A-Za-z0-9_]*` and arguments without `=` are rejected before execution.
- Values containing quotes or SQL text remain data, and an injection-shaped value cannot change the database schema.

### REQ-pg-006

All commands SHALL use the fledge-v1 protocol for input, output, and host execution.

Acceptance Criteria

- The plugin consumes an `init` message and emits structured `exec`, `output`, and `log` messages.
- Database commands are requested through `exec`; the plugin does not invoke `psql` directly.

## Constraints

- Must work without any dependencies beyond `psql` and `jq`
- Shell script implementation (no compile step)
- No OS keychain or external state beyond the target database

## Out of Scope

- GUI or TUI interfaces
- Database/server provisioning (`init`) and migration tracking (`migrate`)
- An audit log (the Merlin-internal pgrun keeps one; this plugin does not)
- Replication or backup
