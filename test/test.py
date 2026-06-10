#!/usr/bin/env python3
"""Integration tests for fledge-plugin-pg.

Spawns the plugin as a subprocess; this test script acts as the fledge
host, dispatching the plugin's exec requests against the real shell.

Two tiers:

  * Offline tests (always run) exercise the destructive-statement gate,
    the missing-URL error, and --param validation. They never touch a
    database.

  * Live tests run against a Postgres reachable via PG_TEST_URL. If
    PG_TEST_URL is unset they self-skip loudly. Set PG_TEST_DOCKER=1 to
    start a throwaway Dockerized Postgres on an ephemeral host port,
    run the live tests against it, and clean it up afterward.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import tempfile
import shutil
import time
from contextlib import closing
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent
BIN = PLUGIN_DIR / "bin" / "fledge-pg"


class PluginRunner:
    def __init__(self, work: Path, url: str | None = None):
        self.work = work
        self.url = url

    def run(self, args: list[str]) -> str:
        captured: list[str] = []
        env = dict(os.environ)
        if self.url is not None:
            env["DATABASE_URL"] = self.url
        else:
            env.pop("DATABASE_URL", None)
        proc = subprocess.Popen(
            [str(BIN)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=env,
        )
        assert proc.stdin and proc.stdout
        init = {
            "type": "init",
            "version": "fledge-v1",
            "project": {"root": str(self.work), "name": "t"},
            "plugin": {"dir": str(PLUGIN_DIR), "name": "fledge-plugin-pg"},
            "command": "pg",
            "args": args,
        }
        proc.stdin.write(json.dumps(init) + "\n")
        proc.stdin.flush()

        for line in proc.stdout:
            line = line.rstrip("\n")
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                captured.append(f"[malformed] {line}")
                continue
            mtype = msg.get("type")
            if mtype == "output":
                captured.append(msg.get("text", ""))
            elif mtype == "log":
                captured.append(f"[{msg.get('level','log')}] {msg.get('message','')}")
            elif mtype == "exec":
                self._handle_exec(msg, proc, env)
        proc.wait(timeout=30)
        return "\n".join(captured)

    def _handle_exec(self, msg: dict, proc: subprocess.Popen, env: dict) -> None:
        cmd = msg["command"]
        cwd = msg.get("cwd") or str(self.work)
        result = subprocess.run(
            ["bash", "-c", cmd],
            cwd=cwd,
            capture_output=True,
            text=True,
            env=env,
        )
        resp = {
            "type": "response",
            "id": msg["id"],
            "value": {
                "code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            },
        }
        proc.stdin.write(json.dumps(resp) + "\n")
        proc.stdin.flush()


passed = 0
failed = 0
skipped = 0


def assert_in(name: str, output: str, needle: str) -> None:
    global passed, failed
    if needle in output:
        print(f"  ok {name}")
        passed += 1
    else:
        print(f"  FAIL {name}")
        print(f"       expected substring: {needle!r}")
        print(f"       output:")
        for line in output.splitlines():
            print(f"         {line}")
        failed += 1


def assert_not_in(name: str, output: str, needle: str) -> None:
    global passed, failed
    if needle not in output:
        print(f"  ok {name}")
        passed += 1
    else:
        print(f"  FAIL {name} (unexpected substring {needle!r})")
        failed += 1


def offline_tests(work: Path) -> None:
    """Tests that never touch a database."""
    print("offline tests (no database):")
    # A runner with NO url so DATABASE_URL is unset.
    r = PluginRunner(work, url=None)

    # Destructive gate fires before the missing-URL check, so these run
    # without a database.
    out = r.run(["query", "DELETE FROM accounts"])
    assert_in("DELETE blocked", out, "Destructive operation blocked ('DELETE'")

    out = r.run(["query", "drop table t"])
    assert_in("lowercase drop blocked", out, "blocked ('DROP'")

    out = r.run(["query", "TRUNCATE logs"])
    assert_in("TRUNCATE blocked", out, "blocked ('TRUNCATE'")

    out = r.run(["query", "ALTER TABLE t ADD COLUMN x int"])
    assert_in("ALTER blocked", out, "blocked ('ALTER'")

    out = r.run(["query", "GRANT SELECT ON t TO bob"])
    assert_in("GRANT blocked", out, "blocked ('GRANT'")

    out = r.run(["query", "REVOKE ALL ON t FROM bob"])
    assert_in("REVOKE blocked", out, "blocked ('REVOKE'")

    out = r.run(["query", "UPDATE sessions SET token='x'"])
    assert_in("UPDATE blocked", out, "blocked ('UPDATE'")

    # Bare keyword at end of string, and with a trailing semicolon /
    # newline (the bypasses sql-run learned the hard way).
    out = r.run(["query", "DROP"])
    assert_in("bare DROP blocked", out, "blocked ('DROP'")
    out = r.run(["query", "DELETE;"])
    assert_in("DELETE; blocked", out, "blocked ('DELETE'")
    out = r.run(["query", "DELETE\nFROM t"])
    assert_in("DELETE-newline blocked", out, "blocked ('DELETE'")

    # Word-boundary safety: dropped_at / updated_at columns are fine.
    # These pass the gate, then fail on the missing URL, which is the
    # proof the gate did NOT fire.
    out = r.run(["query", "SELECT dropped_at FROM events"])
    assert_not_in("dropped_at not blocked", out, "Destructive operation blocked")
    assert_in("dropped_at hits URL check", out, "No Postgres URL")

    out = r.run(["query", "SELECT updated_at, mydelete, deletefoo FROM logs"])
    assert_not_in("embedded keywords not blocked", out, "Destructive operation blocked")

    # SELECT with no URL -> clean missing-URL error, no panic.
    out = r.run(["query", "SELECT 1"])
    assert_in("missing URL error", out, "No Postgres URL")

    # --param validation (fires before URL resolution? No: gate first,
    # then URL. --param parse happens during arg scan, before both.)
    out = r.run(["query", "SELECT 1", "--param", "not-a-kv-pair"])
    assert_in("bad --param syntax rejected", out, "Bad --param syntax")

    out = r.run(["query", "SELECT 1", "--param", "1bad=value"])
    assert_in("bad --param name rejected", out, "Bad --param name")

    # help works with no URL.
    out = r.run(["help"])
    assert_in("help lists query", out, "query")
    assert_in("help lists schema", out, "schema")

    # --allow-destructive lets the keyword through to the URL check.
    out = r.run(["query", "DELETE FROM t", "--allow-destructive"])
    assert_not_in("allow-destructive bypasses gate", out, "Destructive operation blocked")
    assert_in("allow-destructive then URL check", out, "No Postgres URL")


def live_tests(work: Path, url: str) -> None:
    print(f"live tests (PG_TEST_URL set):")
    r = PluginRunner(work, url=url)

    # Sanity: can we reach the DB at all?
    out = r.run(["query", "SELECT 1 AS n", "--json"])
    if "could not" in out.lower() or "Query failed" in out:
        print(f"  SKIP live tests: database not reachable at {url}")
        print(f"       {out}")
        global skipped
        skipped += 1
        return
    assert_in("select json", out, '{"n":1}')

    # Setup a table (DDL needs --allow-destructive only if it contains a
    # blocked keyword; CREATE TABLE does not).
    r.run(["query",
           "DROP TABLE IF EXISTS agents; CREATE TABLE agents (name text primary key, role text)",
           "--allow-destructive"])
    r.run(["query", "INSERT INTO agents VALUES ('Rook','security'),('Corvin','ci')"])

    out = r.run(["query", "SELECT name, role FROM agents ORDER BY name", "--json"])
    assert_in("json rows", out, '"name":"Corvin"')
    assert_in("json rows role", out, '"role":"security"')

    out = r.run(["query", "SELECT name FROM agents ORDER BY name", "--csv"])
    assert_in("csv header", out, "name")
    assert_in("csv data", out, "Rook")

    out = r.run(["query", "SELECT name FROM agents ORDER BY name", "--list"])
    assert_in("list data", out, "Corvin")

    # Parameter binding.
    out = r.run(["query", "SELECT role FROM agents WHERE name = :'name'",
                 "--param", "name=Rook", "--json"])
    assert_in("param simple", out, '"role":"security"')

    # Single quote in value.
    r.run(["query", "INSERT INTO agents VALUES (:'n', 'crow')",
           "--param", "n=O'Brien", "--allow-destructive"])
    out = r.run(["query", "SELECT role FROM agents WHERE name = :'name'",
                 "--param", "name=O'Brien", "--json"])
    assert_in("param single quote", out, '"role":"crow"')

    # Injection attempt via --param: treated as plain text, table intact.
    r.run(["query", "SELECT * FROM agents WHERE name = :'name'",
           "--param", "name=x'; DROP TABLE agents; --", "--json"])
    out = r.run(["query", "SELECT count(*) AS n FROM agents", "--json"])
    assert_in("injection blocked, table intact", out, '"n":3')

    # Empty result -> [].
    out = r.run(["query", "SELECT name FROM agents WHERE name = 'nobody'", "--json"])
    assert_in("empty result is []", out, "[]")

    # allow-destructive DELETE actually runs.
    r.run(["query", "DELETE FROM agents WHERE name = :'name'",
           "--param", "name=Corvin", "--allow-destructive"])
    out = r.run(["query", "SELECT count(*) AS n FROM agents", "--json"])
    assert_in("allow-destructive DELETE ran", out, '"n":2')

    # schema lists the table.
    out = r.run(["schema"])
    assert_in("schema lists agents table", out, "agents")

    out = r.run(["schema", "--json"])
    assert_in("schema json has agents", out, "agents")


def _free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_ready(container: str, timeout: float = 60.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        res = subprocess.run(
            ["docker", "exec", container, "pg_isready", "-U", "pg"],
            capture_output=True, text=True,
        )
        if res.returncode == 0:
            return True
        time.sleep(1)
    return False


def maybe_start_docker() -> tuple[str | None, str | None]:
    """If PG_TEST_DOCKER=1, start a throwaway Postgres. Returns
    (url, container_name) or (None, None)."""
    if os.environ.get("PG_TEST_DOCKER") != "1":
        return None, None
    if not shutil.which("docker"):
        print("  SKIP docker harness: docker not on PATH")
        return None, None
    port = _free_port()
    name = f"fledge-pg-test-{os.getpid()}"
    print(f"  starting throwaway Postgres container {name} on 127.0.0.1:{port}")
    res = subprocess.run(
        ["docker", "run", "-d", "--rm", "--name", name,
         "-e", "POSTGRES_USER=pg", "-e", "POSTGRES_PASSWORD=pg",
         "-e", "POSTGRES_DB=pgtest",
         "-p", f"127.0.0.1:{port}:5432", "postgres:16"],
        capture_output=True, text=True,
    )
    if res.returncode != 0:
        print(f"  SKIP docker harness: failed to start container: {res.stderr.strip()}")
        return None, None
    if not _wait_ready(name):
        print("  SKIP docker harness: container never became ready")
        subprocess.run(["docker", "rm", "-f", name], capture_output=True)
        return None, None
    return f"postgres://pg:pg@127.0.0.1:{port}/pgtest", name


def main() -> int:
    global skipped
    work = Path(tempfile.mkdtemp(prefix="fledge-pg-test."))
    container = None
    try:
        (work / ".fledge").mkdir()
        offline_tests(work)

        url = os.environ.get("PG_TEST_URL")
        if not url:
            url, container = maybe_start_docker()

        if url:
            live_tests(work, url)
        else:
            print()
            print("  SKIP live tests: no PG_TEST_URL and PG_TEST_DOCKER!=1.")
            print("       Offline gate/validation tests still ran above.")
            print("       Set PG_TEST_URL=postgres://... or PG_TEST_DOCKER=1 to run live.")
            skipped += 1
    finally:
        if container:
            subprocess.run(["docker", "rm", "-f", container], capture_output=True)
        shutil.rmtree(work, ignore_errors=True)

    print()
    print(f"tests: {passed} passed, {failed} failed, {skipped} skipped")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
