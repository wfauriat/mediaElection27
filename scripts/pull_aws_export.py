"""Pull every table out of the AWS RDS via the loader Lambda's export action.

    .venv/bin/python scripts/pull_aws_export.py                 # pull to exports/aws-<UTC date>/
    .venv/bin/python scripts/pull_aws_export.py --load media27_aws

Step 1 (always): invoke `export_manifest`, then page each table with
`export` until `has_more` is false. Pages are concatenated into
`<out>/<table>.csv` (one header) and the manifest is saved next to them.
Row counts are checked against the manifest before anything is loaded.

Step 2 (`--load DB`): create a fresh local database DB in the
docker Postgres, run alembic to head, and `COPY ... FROM` each CSV
in foreign-key order, then bump the id sequences. DB must not
exist yet, so this never touches the main `media27` database.
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import boto3
import psycopg
from botocore.config import Config
from psycopg import sql

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REGION = "eu-west-3"
LOADER_PREFIX = "Media27Ingest-LoaderFn"

# FK order: parents before children.
TABLES = ("sources", "candidates", "candidate_aliases", "articles", "mentions", "ingest_runs")

LOCAL_ADMIN_DSN = "postgresql://media27:media27@localhost:5432/postgres"


def _find_loader(lam: Any) -> str:
    names: list[str] = []
    for page in lam.get_paginator("list_functions").paginate():
        names += [
            f["FunctionName"]
            for f in page["Functions"]
            if f["FunctionName"].startswith(LOADER_PREFIX)
        ]
    if len(names) != 1:
        sys.exit(f"expected exactly one {LOADER_PREFIX}* function, found {names}")
    return names[0]


def _invoke(lam: Any, fn: str, payload: dict[str, Any]) -> dict[str, Any]:
    resp = lam.invoke(FunctionName=fn, Payload=json.dumps(payload).encode())
    body = json.loads(resp["Payload"].read())
    if resp.get("FunctionError") or (isinstance(body, dict) and body.get("error")):
        sys.exit(f"invoke {payload} failed: {body}")
    return body  # type: ignore[no-any-return]


def pull(out_dir: Path) -> dict[str, Any]:
    lam = boto3.client(
        "lambda",
        region_name=REGION,
        config=Config(read_timeout=300, retries={"max_attempts": 2}),
    )
    fn = _find_loader(lam)
    print(f"loader: {fn}")

    manifest = _invoke(lam, fn, {"action": "export_manifest"})
    manifest["pulled_at"] = datetime.now(UTC).isoformat()
    print(f"remote alembic revision: {manifest['alembic_version']}")

    out_dir.mkdir(parents=True, exist_ok=True)
    for table in TABLES:
        expected = manifest["tables"][table]["rows"]
        after_id, n_total, page_no = 0, 0, 0
        with (out_dir / f"{table}.csv").open("wb") as fh:
            while True:
                page = _invoke(lam, fn, {"action": "export", "table": table, "after_id": after_id})
                page_no += 1
                csv_bytes = (
                    gzip.decompress(base64.b64decode(page["csv_gz_b64"])) if page["n_rows"] else b""
                )
                if csv_bytes:
                    if n_total:  # drop the header on every page after the first
                        csv_bytes = csv_bytes.split(b"\n", 1)[1]
                    fh.write(csv_bytes)
                n_total += page["n_rows"]
                after_id = page["last_id"]
                print(
                    f"  {table:<18} page {page_no:>3}: +{page['n_rows']:>6} rows (id ≤ {after_id})"
                )
                if not page["has_more"]:
                    break
        # Rows inserted after the manifest (a cron run mid-pull) are fine;
        # fewer rows than the manifest is not.
        status = "ok" if n_total >= expected else "SHORT"
        print(f"  {table:<18} {n_total} rows (manifest {expected}) {status}")
        if n_total < expected:
            sys.exit(f"{table}: pulled {n_total} < manifest {expected}")
        manifest["tables"][table]["pulled_rows"] = n_total

    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"wrote {out_dir}")
    return manifest


def load(out_dir: Path, db: str) -> None:
    manifest = json.loads((out_dir / "manifest.json").read_text())

    with psycopg.connect(LOCAL_ADMIN_DSN, autocommit=True) as admin:
        exists = admin.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db,)).fetchone()
        if exists:
            sys.exit(f"database {db!r} already exists — drop it first or pick another name")
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db)))
    print(f"created database {db}")

    dsn_sync = f"postgresql+psycopg://media27:media27@localhost:5432/{db}"
    env = {**os.environ, "DATABASE_URL_SYNC": dsn_sync}
    subprocess.run(
        [str(PROJECT_ROOT / ".venv/bin/alembic"), "upgrade", "head"],
        cwd=PROJECT_ROOT,
        env=env,
        check=True,
    )

    with psycopg.connect(f"postgresql://media27:media27@localhost:5432/{db}") as conn:
        local_rev = conn.execute("SELECT version_num FROM alembic_version").fetchone()
        if local_rev is None or local_rev[0] != manifest["alembic_version"]:
            sys.exit(f"alembic mismatch: local {local_rev} vs remote {manifest['alembic_version']}")
        with conn.cursor() as cur:
            for table in TABLES:
                path = out_dir / f"{table}.csv"
                with path.open("rb") as fh:
                    header = fh.readline().decode().strip().split(",")
                    fh.seek(0)
                    cols = sql.SQL(", ").join(sql.Identifier(c) for c in header)
                    stmt = sql.SQL("COPY {} ({}) FROM STDIN WITH (FORMAT csv, HEADER true)").format(
                        sql.Identifier(table), cols
                    )
                    with cur.copy(stmt) as copy:
                        while chunk := fh.read(1 << 20):
                            copy.write(chunk)
                n = cur.execute(
                    sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier(table))
                ).fetchone()
                print(f"  loaded {table:<18} {n[0] if n else 0}")
                # Keep serial sequences ahead of the imported ids.
                cur.execute("SELECT pg_get_serial_sequence(%s, 'id')", (table,))
                seq = cur.fetchone()
                if seq and seq[0]:
                    cur.execute(
                        sql.SQL(
                            "SELECT setval(%s, (SELECT coalesce(max(id), 0) + 1 FROM {}), false)"
                        ).format(sql.Identifier(table)),
                        (seq[0],),
                    )
        conn.commit()
    print(f"loaded into {db}")


def main() -> None:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    stamp = datetime.now(UTC).strftime("%Y-%m-%d")
    p.add_argument("--out", type=Path, default=PROJECT_ROOT / "exports" / f"aws-{stamp}")
    p.add_argument(
        "--load", metavar="DB", help="also load into a NEW local database with this name"
    )
    p.add_argument("--skip-pull", action="store_true", help="reuse CSVs already in --out")
    args = p.parse_args()

    if not args.skip_pull:
        pull(args.out)
    if args.load:
        load(args.out, args.load)


if __name__ == "__main__":
    main()
