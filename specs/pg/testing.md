---
spec: pg.spec.md
---

## Test Plan

### Unit-ish (no database required)

- Destructive gate: SELECT is safe; DELETE/UPDATE/DROP/TRUNCATE/ALTER/GRANT/REVOKE are caught
- Destructive gate: `dropped_at` / `updated_at` columns are safe (word-boundary tokenizer)
- Destructive gate: `DELETE;`, `DELETE\nFROM`, and a bare `DROP` are caught
- Missing URL: clean error, non-zero exit, no connection attempt
- Bad `--param` syntax / name rejected
- Blocked destructive statement refused unless `--allow-destructive`

### Integration (live database)

These self-skip loudly when no test database is configured, so they
never require a running Postgres in CI. Set `PG_TEST_URL` (or run the
Docker harness) to exercise them:

- `query` returns rows as JSON / CSV / list / table
- `--param` binds values and blocks an injection attempt
- `schema` lists a created table
- `--allow-destructive` permits an UPDATE/DELETE
