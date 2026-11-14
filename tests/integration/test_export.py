"""Round-trip checks for app.ingest.export against the local dev DB (read-only)."""

from __future__ import annotations

import base64
import csv
import gzip
import io

from sqlalchemy import text

from app.db.engine import get_sync_engine
from app.ingest.export import export_manifest, export_page


def _rows(page: dict[str, object]) -> list[dict[str, str]]:
    raw = gzip.decompress(base64.b64decode(str(page["csv_gz_b64"])))
    return list(csv.DictReader(io.StringIO(raw.decode())))


def test_manifest_matches_counts() -> None:
    m = export_manifest()
    with get_sync_engine().connect() as conn:
        n = conn.execute(text("SELECT count(*) FROM articles")).scalar_one()
    assert m["tables"]["articles"]["rows"] == n
    assert m["alembic_version"]


def test_paging_covers_every_row_exactly_once() -> None:
    after, ids = 0, []
    while True:
        page = export_page("sources", after_id=after, limit=4)
        ids += [int(r["id"]) for r in _rows(page)] if page["n_rows"] else []
        after = int(page["last_id"])
        if not page["has_more"]:
            break
    with get_sync_engine().connect() as conn:
        expected = list(conn.execute(text("SELECT id FROM sources ORDER BY id")).scalars())
    assert ids == expected


def test_limit_halves_until_payload_fits() -> None:
    page = export_page("articles", after_id=0, limit=1000, max_b64_bytes=50_000)
    assert len(str(page["csv_gz_b64"])) <= 50_000
    assert int(page["limit_used"]) < 1000
    assert len(_rows(page)) == page["n_rows"]
    # bytea round-trips as Postgres hex text
    assert _rows(page)[0]["content_hash"].startswith("\\x")


def test_unknown_table_rejected() -> None:
    assert "error" in export_page("alembic_version; DROP TABLE x")
