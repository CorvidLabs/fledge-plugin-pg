---
module: pg
version: 1
status: active
files:
  - bin/fledge-pg

db_tables: []
depends_on: []
---

# Pg

## Purpose

Postgres database management for fledge projects. Provides ad-hoc queries with multiple output formats, schema inspection, and a destructive-statement gate. Wraps the `psql` CLI via the fledge-v1 protocol's `exec` capability. Sibling of `fledge-plugin-sql`, which targets SQLite.

## Public API

### Commands

| Command | Args | Description |
|---------|------|-------------|
| `query` | `<sql>` `[--url <conn>]` `[--json\|--list\|--csv]` `[--param name=value]...` `[--allow-destructive]` | Execute SQL against Postgres, display results as a table (default), JSON, list, or CSV. |
| `schema` | `[--url <conn>]` `[--json]` | Dump tables, views, and indexes for user schemas (excludes `pg_catalog` / `information_schema`). |
| `help` | | Show usage. |

### Connection resolution

The connection string is resolved with this precedence:

1. An explicit `--url <conn>`.
2. The `DATABASE_URL` environment variable.

When neither is set the plugin exits non-zero with a clear message and never attempts a connection.

### Protocol Messages Used

| Message Type | Direction | Purpose |
|-------------|-----------|---------|
| `init` | inbound | Receive project context and args |
| `exec` | outbound | Run `psql` commands |
| `output` | outbound | Display results to the user |
| `log` | outbound | Diagnostic / error messages |

### Migrate is intentionally omitted

`fledge-plugin-sql` ships a `migrate` command that applies `*.sql` files and tracks them in a `_migrations` table inside the same SQLite file. There is no clean `psql`-only analog: migration files almost always contain `ALTER`/`DROP`/`UPDATE`, which the destructive gate refuses by default, and tracking would need server-side state that conflicts with the read-mostly contract of this plugin. `init` is also omitted: a Postgres database/server is provisioned out of band (managed service, Docker, `createdb`), not by this CLI, so there is nothing for the plugin to create. Use `query --allow-destructive` for schema changes and run migrations with a dedicated migration tool.

## Invariants

1. Connection precedence is `--url <conn>` first, then the `DATABASE_URL` environment variable. When neither is set the plugin exits non-zero with a clear message and never attempts a connection.
2. `--json` returns a single JSON array (server-side `json_agg`), `[]` for an empty result. `--csv` returns CSV with a header, `--list` returns pipe-separated rows with a header, and the default returns an aligned `psql` table.
3. Postgres errors are surfaced through the plugin's error log so the caller gets the parser or runtime message.
4. Destructive statements (`DELETE`, `UPDATE`, `DROP`, `TRUNCATE`, `REPLACE`, `ALTER`, `GRANT`, `REVOKE`) are refused unless `--allow-destructive` is passed. The scan tokenizes on non-alphabetic boundaries so a column named `dropped_at` is safe but `DELETE;`, `DELETE\nFROM`, and a bare `DROP` are all caught. Matching is case-insensitive. `SELECT` is never blocked.
5. Untrusted values are bound with `--param name=value`. The value is passed to `psql` via `--set` and referenced in SQL as `:'name'`, which interpolates it as a quoted, escaped string literal, so it cannot inject SQL regardless of content. Parameter names must match `[A-Za-z_][A-Za-z0-9_]*`.
6. The connection URL and SQL are shell-escaped via `printf '%q'` before reaching `psql`, preventing shell injection.
7. All `psql` invocations go through the fledge-v1 `exec` message, never direct shell execution.
8. A blocked destructive statement prints a clear refusal and exits non-zero. Unlike the Merlin-internal `pgrun` plugin (which also writes a row to `<project>/.fledge/data.db` `destructive_op_audit`), this standalone public plugin does not maintain an audit log: a clear refusal message plus a non-zero exit is the contract.

## Behavioral Examples

```
$ export DATABASE_URL=postgres://user:pass@localhost:5432/app

$ fledge pg query "SELECT 1 AS n" --json
[{"n":1}]

$ fledge pg query "SELECT name, role FROM agents" --csv
name,role
Rook,security
Corvin,ci

$ fledge pg query "SELECT * FROM agents WHERE name = :'name'" --param name=Rook --json
[{"name":"Rook","role":"security"}]

$ fledge pg query "DELETE FROM agents"
[error] Destructive operation blocked ('DELETE' in SQL). Pass --allow-destructive to override.

$ fledge pg query "DELETE FROM agents WHERE name = :'name'" --param name=Rook --allow-destructive
OK

$ fledge pg schema
TABLE public.agents
CREATE UNIQUE INDEX agents_pkey ON public.agents USING btree (name)
```

## Error Cases

| Error | When | Behavior |
|-------|------|----------|
| Missing URL | No `--url` and no `DATABASE_URL` | Clear error before any connection attempt, exit 1 |
| Unreachable DB | URL host/port not accepting connections | `Query failed: <psql detail>`, exit 1 |
| SQL error | Malformed or failing statement | Postgres error message returned verbatim, exit 1 |
| Destructive blocked | Destructive keyword without `--allow-destructive` | Refused with the matched keyword, exit 1 |
| Bad `--param` syntax | Argument is not `name=value` | `Bad --param syntax`, exit 1 |
| Bad `--param` name | Name does not match `[A-Za-z_][A-Za-z0-9_]*` | `Bad --param name`, exit 1 |

## Dependencies

- `psql` CLI (the PostgreSQL client, external, must be on PATH)
- `jq` (JSON-lines protocol marshalling)
- fledge-v1 protocol (`exec` capability)

## Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1 | 2026-06-10 | Initial spec. `pg` mirrors `sql` for Postgres: `query` (`--json`/`--list`/`--csv`/`--param`) and `schema`, connection via `--url` or `DATABASE_URL`, destructive-statement gate with `--allow-destructive` override. `init`/`migrate` omitted (no clean psql analog). No audit log (the Merlin-internal pgrun keeps one; this public plugin relies on a clear refusal + non-zero exit). |
