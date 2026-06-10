---
spec: pg.spec.md
---

## Context

Postgres sibling of `fledge-plugin-sql`. Where the sql plugin wraps the
`sqlite3` CLI against a project-local file, this plugin wraps the `psql`
CLI against a server reached by a connection URL. The destructive-op
gate and parameter-binding design are ported from the Merlin-internal
`pgrun` plugin (Rust, `tokio-postgres`), but this public plugin is a
zero-compile bash script and keeps no audit log.

## Related Modules

- fledge-plugin-sql (SQLite analog: `init`, `migrate`, `query`, `schema`)

## Design Decisions

- Shell script wrapping the `psql` CLI rather than a compiled binary -
  keeps the plugin zero-dependency and immediately editable.
- Connection via `--url` or `DATABASE_URL` rather than a stored path -
  Postgres is a server, not a file, so there is no project-local path to
  persist the way the sql plugin stores its db path.
- Destructive gate tokenizes on word boundaries (a column named
  `dropped_at` is safe; a bare `DROP` is caught): same approach the
  pgrun reference adopted from sql-run's hard-won lesson.
- `init` and `migrate` are omitted: a Postgres server is provisioned out
  of band, and migration files trip the destructive gate. See the spec.
- No audit log: the Merlin-internal pgrun writes to
  `destructive_op_audit`; a standalone public plugin uses a clear
  refusal message and a non-zero exit instead.
