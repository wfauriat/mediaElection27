"""Table export for getting data out of the in-VPC RDS.

The RDS instance lives in PRIVATE_ISOLATED subnets with no public
endpoint, so the only things that can read it are the in-VPC Lambdas.
This module backs the loader Lambda's `{"action": "export"}` admin
action: it streams one page of a table through Postgres `COPY ... TO
STDOUT (FORMAT csv)`, gzips it, and returns it base64-encoded inside
the invoke response.

Why the invoke response rather than an S3 object: the raw bucket's
ObjectCreated notification has no prefix filter, so any object
written there would re-trigger the loader. Returning the payload
inline also needs no new IAM grant.

Why COPY CSV: it is Postgres' own lossless text form for every
column type in the schema (bytea as `\\x...` hex, jsonb, timestamptz
with offset), and `COPY ... FROM` on the receiving side reads it
back byte-for-byte.

Synchronous Lambda responses are capped at 6 MB, so pages are cut
by primary key (`id > after_id ORDER BY id LIMIT n`) and the row
limit is halved until the encoded page fits under `max_b64_bytes`.
"""

from __future__ import annotations

import base64
import gzip
from typing import Any

from psycopg import sql
from sqlalchemy import text

from app.db.engine import get_sync_engine

# Every exportable table has a monotonically increasing integer `id`
# primary key, which is what makes keyset paging possible.
EXPORT_TABLES: tuple[str, ...] = (
    "sources",
    "candidates",
    "candidate_aliases",
    "articles",
    "mentions",
    "ingest_runs",
)

# Lambda's synchronous response limit is 6 MB (6,291,456 bytes) for the
# whole JSON document; leave headroom for the envelope fields.
DEFAULT_MAX_B64_BYTES = 5_000_000
DEFAULT_LIMIT = 50_000


def export_manifest() -> dict[str, Any]:
    """Row count and max id per table, plus the alembic revision.

    Used by the puller to know how many pages to expect and to verify
    the local copy once every page has landed.
    """
    tables: dict[str, dict[str, int]] = {}
    with get_sync_engine().connect() as conn:
        for table in EXPORT_TABLES:
            n, max_id = conn.execute(
                text(f"SELECT count(*), coalesce(max(id), 0) FROM {table}")  # fixed allow-list
            ).one()
            tables[table] = {"rows": int(n), "max_id": int(max_id)}
        revision = conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    return {"action": "export_manifest", "alembic_version": revision, "tables": tables}


def _copy_page(table: str, after_id: int, limit: int) -> tuple[bytes, int, int]:
    """Return (csv_bytes, n_rows, last_id) for one keyset page."""
    engine = get_sync_engine()
    raw = engine.raw_connection()
    try:
        conn = raw.driver_connection  # psycopg.Connection
        assert conn is not None
        ident = sql.Identifier(table)
        with conn.cursor() as cur:
            cur.execute(
                sql.SQL(
                    "SELECT count(*), coalesce(max(id), %s) FROM "
                    "(SELECT id FROM {} WHERE id > %s ORDER BY id LIMIT %s) page"
                ).format(ident),
                (after_id, after_id, limit),
            )
            row = cur.fetchone()
            assert row is not None
            n_rows, last_id = int(row[0]), int(row[1])
            if n_rows == 0:
                return b"", 0, after_id

            # Bound the COPY by the id range just measured so the page is
            # exactly the rows counted above, even if inserts land meanwhile.
            copy_stmt = sql.SQL(
                "COPY (SELECT * FROM {} WHERE id > {} AND id <= {} ORDER BY id) "
                "TO STDOUT WITH (FORMAT csv, HEADER true)"
            ).format(ident, sql.Literal(after_id), sql.Literal(last_id))
            buf = bytearray()
            with cur.copy(copy_stmt) as copy:
                for chunk in copy:
                    buf += chunk
        conn.rollback()
        return bytes(buf), n_rows, last_id
    finally:
        raw.close()


def export_page(
    table: str,
    after_id: int = 0,
    limit: int = DEFAULT_LIMIT,
    max_b64_bytes: int = DEFAULT_MAX_B64_BYTES,
) -> dict[str, Any]:
    """Export rows of `table` with `id > after_id`, as gzipped CSV in base64.

    The response says `has_more`; the caller re-invokes with
    `after_id = last_id` until it is false.
    """
    if table not in EXPORT_TABLES:
        return {"action": "export", "error": f"table not exportable: {table!r}"}
    after_id = int(after_id)
    limit = max(1, int(limit))

    while True:
        csv_bytes, n_rows, last_id = _copy_page(table, after_id, limit)
        payload = base64.b64encode(gzip.compress(csv_bytes, compresslevel=9)).decode("ascii")
        if len(payload) <= max_b64_bytes or limit == 1:
            break
        limit = max(1, limit // 2)

    if len(payload) > max_b64_bytes:
        return {
            "action": "export",
            "table": table,
            "error": f"single row id>{after_id} exceeds {max_b64_bytes} bytes encoded",
        }

    with get_sync_engine().connect() as conn:
        has_more = bool(
            conn.execute(
                text(f"SELECT EXISTS (SELECT 1 FROM {table} WHERE id > :last)"),  # allow-listed
                {"last": last_id},
            ).scalar_one()
        )

    return {
        "action": "export",
        "table": table,
        "after_id": after_id,
        "last_id": last_id,
        "n_rows": n_rows,
        "limit_used": limit,
        "has_more": has_more,
        "csv_gz_b64": payload,
    }
