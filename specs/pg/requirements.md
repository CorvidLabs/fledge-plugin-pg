---
spec: pg.spec.md
---

## User Stories

- As a developer, I want to run ad-hoc queries against a Postgres database with a single command
- As a developer, I want query results in JSON, CSV, list, or table form
- As a developer, I want to bind untrusted values without risking SQL injection
- As an AI agent, I want destructive statements refused by default so I cannot silently destroy data

## Acceptance Criteria

- `fledge pg query` executes SQL and returns formatted results
- `fledge pg schema` shows tables, views, and indexes for user schemas
- Connection resolves from `--url` first, then `DATABASE_URL`
- Destructive statements are refused unless `--allow-destructive` is passed
- `--param name=value` binds values safely and rejects injection attempts
- All commands use the fledge-v1 protocol for I/O

## Constraints

- Must work without any dependencies beyond `psql` and `jq`
- Shell script implementation (no compile step)
- No OS keychain or external state beyond the target database

## Out of Scope

- GUI or TUI interfaces
- Database/server provisioning (`init`) and migration tracking (`migrate`)
- An audit log (the Merlin-internal pgrun keeps one; this plugin does not)
- Replication or backup
