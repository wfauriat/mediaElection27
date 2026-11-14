# 2026-11-14 — AWS data archived and merged into local Postgres

Why: AWS free plan (account 669880793306) expires **2026-11-16 21:32 UTC**
($50.46 credit left). Everything the cloud pipeline collected since
2026-05-17 had to come home before then.

## What was done

1. **Export path out of the VPC** (commit `45edcf6`, deployed via CI).
   RDS is in PRIVATE_ISOLATED subnets with no public endpoint, so the
   loader Lambda got two admin actions: `export_manifest` (row counts,
   max ids, alembic revision) and `export` (one keyset page of a table as
   gzipped `COPY ... CSV`, base64 in the invoke response, halved until it
   fits Lambda's 6 MB response cap). Not via S3: the raw bucket's
   ObjectCreated trigger has no prefix filter. Puller:
   `scripts/pull_aws_export.py [--load DB]`.
2. **Pulled** all 6 tables into `exports/aws-2026-11-14/` (CSV +
   `manifest.json`, gitignored), counts identical to the manifest:
   28,647 articles · 19,911 mentions · 10,883 ingest_runs · 17 sources ·
   14 candidates · 35 aliases. Loaded verbatim into a scratch DB `media27_aws`.
3. **Diffed** against local `media27` (22,020 articles) on
   (source, guid). Local was *not* a strict subset:
   - 6,887 articles AWS-only (every month; ~half bfmtv-politique, a
     fast-rotating feed)
   - 260 local-only (mostly 2026-05-15, before AWS went live, plus bfmtv
     items the AWS 4×/day cadence missed)
   - sources/candidates identical; aliases identical except surrogate ids
   - ~1,000 shared articles differ in title (outlet edits; first fetcher wins)
4. **Merged** into `media27` in one transaction with count assertions:
   - +6,887 articles (new local ids), +6,225 mentions re-pointed to them
   - +10,883 ingest_runs, tagged `meta.origin = "aws"` + `meta.aws_id`
   - shared articles keep the local version
   - result: **28,907 articles · 20,193 mentions · 15,812 ingest_runs**
   - post-checks: 0 AWS articles missing; `run_extract` found 0 new
     mentions; 39/39 tests pass; a cron ingest run afterwards inserted
     normally (sequences fine)
   - pre-merge backup: `exports/media27-pre-merge-2026-11-14.dump`
     (`pg_restore --clean -d media27` to undo)
5. **S3 raw XML** (2,730 files, 261 MB) downloaded and merged into `raw/`.
   S3 keys are `feeds/{date}/{slug}.xml`, overwritten by each of the 4
   daily runs, so S3 held only the last (18:00 UTC) snapshot per day.
   - 929 files filled days the local cron was off → `raw/` now covers
     every day 2026-05-15 … 2026-11-14 (184 days, 430 MB)
   - 191 byte-identical to local, skipped
   - 1,625 differing snapshots (or today's, which local cron keeps
     overwriting) saved alongside as `{slug}.aws.xml`
6. **Cleanup**: dropped `media27_aws`; removed the downloaded S3 copy
   after checking every file is byte-identical to something in `raw/`.

## Still open

- AWS keeps ingesting until the plan expires; the local cron overlaps
  that window, so at most a few items of 2026-11-14 … 16 are missed.
- Tear-down or account upgrade decision before 2026-11-16 21:32 UTC.
