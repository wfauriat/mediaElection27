"""AWS Lambda entrypoint for the loader stage.

Triggered by S3 ObjectCreated on the raw bucket. For each record:
parse the XML body, dedup, insert into `articles`, and write an
`ingest_runs` audit row. Reuses `_persist_articles` and `_record_run`
from app.ingest.run so persistence logic lives in one place.

DB credentials come from Secrets Manager. The Lambda resolves them
once on cold start and mutates `settings.database_url_sync` before
any SQLAlchemy engine is built.
"""

from __future__ import annotations

import json
import os
import urllib.parse
from datetime import UTC, datetime
from typing import Any

import boto3


def _configure_db_url_from_secrets() -> None:
    """Cold-start hook: build the sync DSN before the engine is created.

    Only runs inside the Lambda runtime (detected via AWS_LAMBDA_FUNCTION_NAME)
    so local imports of this module don't try to call Secrets Manager.
    """
    if "AWS_LAMBDA_FUNCTION_NAME" not in os.environ:
        return

    from app.config import settings

    sm = boto3.client("secretsmanager")
    raw = sm.get_secret_value(SecretId=os.environ["DB_SECRET_ARN"])["SecretString"]
    secret = json.loads(raw)
    user = urllib.parse.quote(secret["username"], safe="")
    pwd = urllib.parse.quote(secret["password"], safe="")
    host = os.environ["DB_HOST"]
    port = os.environ.get("DB_PORT", "5432")
    name = os.environ["DB_NAME"]
    settings.database_url_sync = (
        f"postgresql+psycopg://{user}:{pwd}@{host}:{port}/{name}"
    )


_configure_db_url_from_secrets()

# Imports below trigger the engine module — must be after the DSN is fixed.
from sqlalchemy import select  # noqa: E402

from app.db.engine import get_sync_sessionmaker  # noqa: E402
from app.db.models import Source  # noqa: E402
from app.ingest.fetcher import FetchResult  # noqa: E402
from app.ingest.run import _persist_articles, _record_run  # noqa: E402

_s3 = boto3.client("s3")


def _process_record(bucket: str, key: str) -> dict[str, Any]:
    # Key format: feeds/YYYY-MM-DD/{slug}.xml
    slug = key.rsplit("/", 1)[-1].removesuffix(".xml")

    sm = get_sync_sessionmaker()

    with sm() as session:
        source = session.execute(
            select(Source).where(Source.slug == slug)
        ).scalar_one_or_none()

    if source is None:
        return {"slug": slug, "error": f"unknown source slug: {slug}"}

    body = _s3.get_object(Bucket=bucket, Key=key)["Body"].read()

    fetch = FetchResult(
        source_id=source.id,
        slug=source.slug,
        url=source.feed_url,
        status=200,
        body=body,
        etag=None,
        last_modified=None,
        elapsed_ms=0,
        error=None,
    )

    started = datetime.now(UTC)
    n_items = n_inserted = n_skipped = 0
    error: str | None = None
    try:
        with sm() as session, session.begin():
            n_items, n_inserted, n_skipped = _persist_articles(
                session, source.id, body
            )
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"

    with sm() as session, session.begin():
        _record_run(
            session,
            source_id=source.id,
            started_at=started,
            fetch=fetch,
            n_items=n_items,
            n_inserted=n_inserted,
            n_skipped=n_skipped,
            error=error,
        )

    return {
        "slug": slug,
        "n_items": n_items,
        "n_inserted": n_inserted,
        "n_skipped": n_skipped,
        "error": error,
    }


def handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])
        results.append(_process_record(bucket, key))
    return {"processed": len(results), "items": results}
