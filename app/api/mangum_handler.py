"""AWS Lambda entry point for the FastAPI app.

The CDK stack points this function's handler at
`app.api.mangum_handler.handler`.

Cold-start hook (`_configure_db_url_from_secrets`) resolves the RDS
credentials from Secrets Manager once and mutates
`settings.database_url` (async) before any SQLAlchemy engine is built.
Gated on AWS_LAMBDA_FUNCTION_NAME so local imports skip Secrets Manager.
"""

from __future__ import annotations

import json
import os
import urllib.parse

import boto3


def _configure_db_url_from_secrets() -> None:
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
    settings.database_url = (
        f"postgresql+asyncpg://{user}:{pwd}@{host}:{port}/{name}"
    )


_configure_db_url_from_secrets()

from mangum import Mangum  # noqa: E402

from app.api.main import app  # noqa: E402

handler = Mangum(app, lifespan="off")
