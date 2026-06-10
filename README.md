# fledge-plugin-pg

Postgres database management plugin for [fledge](https://github.com/CorvidLabs/fledge). Run queries with multiple output formats and inspect schema, with a destructive-statement gate on by default. Sibling of [fledge-plugin-sql](https://github.com/CorvidLabs/fledge-plugin-sql), which targets SQLite.

## Install

```bash
fledge plugin install CorvidLabs/fledge-plugin-pg --yes
```

## Connection

The connection string is resolved with this precedence:

1. An explicit `--url <conn>`.
2. The `DATABASE_URL` environment variable.

If neither is set, the plugin exits with a clear error and never attempts a connection.

```bash
export DATABASE_URL=postgres://user:pass@localhost:5432/app
```

## Commands

### `fledge pg query <sql> [--url <conn>] [--json | --csv | --list] [--param name=value]... [--allow-destructive]`

Execute a SQL statement and display results. Defaults to an aligned table.

```
$ fledge pg query "SELECT name, role FROM agents" --json
[{"name":"Rook","role":"security"},{"name":"Corvin","role":"ci"}]

$ fledge pg query "SELECT * FROM agents" --csv
name,role
Rook,security
Corvin,ci

$ fledge pg query "INSERT INTO agents VALUES ('Magpie', 'scout')"
OK
```

#### Parameter binding

For untrusted values, use `--param name=value` instead of interpolating into the SQL string. Bound values are passed to `psql` via `--set` and referenced as `:'name'`, which interpolates them as quoted, escaped string literals, so they cannot inject SQL even if the value contains quotes, semicolons, or `DROP TABLE`.

```
$ fledge pg query "SELECT * FROM agents WHERE name = :'name'" --param "name=O'Brien" --json
[{"name":"O'Brien","role":"crow"}]

# Injection attempt: value treated as plain text, no rows returned, table intact:
$ fledge pg query "SELECT * FROM agents WHERE name = :'name'" \
    --param "name=x'; DROP TABLE agents; --"
(no results)
```

Parameter names must match `[A-Za-z_][A-Za-z0-9_]*`. Repeat `--param` to bind multiple values.

### `fledge pg schema [--url <conn>] [--json]`

Dump the tables, views, and indexes in the current database's user schemas (excludes `pg_catalog` and `information_schema`).

```
$ fledge pg schema
TABLE public.agents
CREATE UNIQUE INDEX agents_pkey ON public.agents USING btree (name)

$ fledge pg schema --json
[{"type":"index","schema":"public","name":"agents_pkey","definition":"CREATE UNIQUE INDEX ..."}]
```

## Safety

Destructive statements are refused by default and require an explicit `--allow-destructive` to run:

```
$ fledge pg query "DELETE FROM agents"
[error] Destructive operation blocked ('DELETE' in SQL). Pass --allow-destructive to override.

$ fledge pg query "DELETE FROM agents WHERE name = :'name'" --param name=Rook --allow-destructive
OK
```

The blocked keyword set is `DELETE`, `UPDATE`, `DROP`, `TRUNCATE`, `REPLACE`, `ALTER`, plus the Postgres access-control mutators `GRANT` and `REVOKE`. Detection tokenizes on word boundaries, so a column named `dropped_at` is safe, but `DELETE;`, `DELETE\nFROM`, and a bare `DROP` are all caught. Matching is case-insensitive; `SELECT` is never blocked.

This mirrors the SQLite `fledge-plugin-sql` and the Merlin-internal `pgrun` plugin. Unlike the Merlin-internal one, this standalone public plugin keeps **no audit log**: a clear refusal message plus a non-zero exit is the contract.

### Shell safety

The connection URL and SQL are shell-escaped (via `printf '%q'`) before being piped to `psql`, which prevents *shell* injection. **Use `--param` for untrusted values** (see above). If you compose SQL by interpolating values into the query string yourself, **you** are responsible for the escaping.

### `init` and `migrate` are intentionally omitted

A Postgres server is provisioned out of band (managed service, Docker, `createdb`), not by this CLI, so there is nothing for an `init` to create. `migrate` is omitted because migration files almost always contain `ALTER`/`DROP`/`UPDATE`, which the destructive gate refuses by default. Run schema changes with `query --allow-destructive`, or use a dedicated migration tool.

## Tests

```bash
python3 test/test.py
```

The destructive-gate, missing-URL, and `--param`-validation tests run with no database. The live-database tests self-skip loudly unless a test Postgres is configured via `PG_TEST_URL`. To exercise the live path with a throwaway Dockerized Postgres:

```bash
PG_TEST_DOCKER=1 python3 test/test.py
```

## Prerequisites

- `psql` (the PostgreSQL client) on PATH
- `jq` on PATH

## Development

```bash
fledge plugins validate .
fledge spec check
bash -n bin/fledge-pg
shellcheck bin/fledge-pg
```

## License

MIT
