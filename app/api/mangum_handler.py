"""AWS Lambda entry point. The CDK stack will point its function handler
at `app.api.mangum_handler.handler`."""

from __future__ import annotations

from mangum import Mangum

from app.api.main import app

handler = Mangum(app, lifespan="off")
