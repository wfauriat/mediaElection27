# mediaElection27

Tracking how often each 2027 French presidential candidate is mentioned in the major French media outlets.

A daily RSS ingest pipeline pulls headlines from ~14 French national outlets covering the political spectrum, normalises them into Postgres, runs candidate-mention detection, and serves an interactive dashboard showing mention trends per candidate per outlet over time.

## Architecture

```
EventBridge (cron 4×/day)
   │
   ▼
ingest Lambda (no VPC, has internet)  →  S3: raw XML  →  loader Lambda (in VPC)  →  RDS Postgres
                                                                                           ▲
                                                                                           │
                                                                          API Lambda (FastAPI via Mangum)
                                                                                           ▲
                                                                                  API Gateway HTTP API
                                                                                           ▲
                                                                                           │
                                                                       CloudFront ◀ S3 (static React SPA)
```

The full design lives in [`PLAN-v1.md`](./PLAN-v1.md).

## Local development

Requires Python 3.12 and Docker.

```bash
make install     # creates .venv and installs project + dev deps
make db-up       # starts Postgres in docker
make migrate     # applies alembic migrations
make seed        # loads candidates.yaml + sources.yaml
make ingest-once # fetches all RSS feeds once
make api         # starts FastAPI on http://localhost:8000
```

`make help` lists all targets.

## Status

Pre-MVP — Week 1 of the timeline in `PLAN-v1.md`. Public deploy targeted for 2026-06-19.
