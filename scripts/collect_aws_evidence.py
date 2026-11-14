"""Collect evidence that the pipeline ran on AWS, before the account closes.

    .venv/bin/python scripts/collect_aws_evidence.py            # -> exports/aws-evidence-<date>/
    .venv/bin/python scripts/collect_aws_evidence.py --summarize # -> dev/aws-evidence/ (sanitised)

Collect (private, gitignored, read-only API calls only):
  metrics/   CloudWatch hourly series since 2026-05-15: EventBridge rule, every
             Lambda (current and replaced), API Gateway, CloudFront, RDS, S3
  s3/        full object listings of the raw and frontend buckets (key, size,
             LastModified, ETag)
  infra/     CloudFormation stacks, events and templates; Lambda, EventBridge,
             RDS, API Gateway, CloudFront configurations (env vars redacted)
  audit/     CloudTrail event history (90 days of management events)
  logs/      the CloudWatch log lines still retained (7 days)
  billing/   Cost Explorer monthly cost and usage per service and usage type
  github/    GitHub Actions run history
  live/      live HTTP responses (headers + bodies) of the dashboard and API

Summarize (public, committed): daily aggregates, the S3 manifest cross-checked
against the local raw/ archive by MD5, stack timeline and deploy history, with
account ids, ARNs and IP addresses left out.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import time
import urllib.request
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import boto3

ROOT = Path(__file__).resolve().parent.parent
REGION = "eu-west-3"
START = datetime(2026, 5, 15, tzinfo=UTC)
PREFIX = "Media27"
DASHBOARD = "https://d2h6mx4fzeshbf.cloudfront.net"
SECTIONS = ("metrics", "s3", "infra", "audit", "logs", "billing", "github", "live")


def dump(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, default=str, ensure_ascii=False))


def redact_env(cfg: dict[str, Any]) -> dict[str, Any]:
    env = cfg.get("Environment", {}).get("Variables")
    if env:
        cfg["Environment"]["Variables"] = {k: "<redacted>" for k in env}
    return cfg


# ---------------------------------------------------------------- collect


def metric_queries(sess: boto3.Session) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """(eu-west-3 queries, us-east-1 queries) as GetMetricData specs."""
    logs = sess.client("logs", region_name=REGION)
    fns = sorted(
        {
            g["logGroupName"].split("/")[-1]
            for p in logs.get_paginator("describe_log_groups").paginate(
                logGroupNamePrefix=f"/aws/lambda/{PREFIX}"
            )
            for g in p["logGroups"]
            if any(k in g["logGroupName"] for k in ("IngestFn", "LoaderFn", "ApiFn"))
        }
    )
    events = sess.client("events", region_name=REGION)
    rule = next(r["Name"] for r in events.list_rules(NamePrefix=f"{PREFIX}Ingest")["Rules"])
    apigw = sess.client("apigatewayv2", region_name=REGION)
    api_ids = [
        a["ApiId"]
        for a in apigw.get_apis()["Items"]
        if a["Name"].lower().startswith(PREFIX.lower())
    ]
    rds = sess.client("rds", region_name=REGION)
    dbs = [d["DBInstanceIdentifier"] for d in rds.describe_db_instances()["DBInstances"]]
    s3 = sess.client("s3")
    buckets = [b["Name"] for b in s3.list_buckets()["Buckets"] if b["Name"].startswith("media27")]
    cf = sess.client("cloudfront")
    dists = [
        d["Id"]
        for d in cf.list_distributions()["DistributionList"].get("Items", [])
        if DASHBOARD.split("//")[1] == d["DomainName"]
    ]

    ids = iter(range(10_000))

    def q(
        label: str, ns: str, name: str, dims: dict[str, str], stat: str, period: int = 3600
    ) -> dict[str, Any]:
        return {
            "Id": f"m{next(ids)}",
            "Label": label,
            "MetricStat": {
                "Metric": {
                    "Namespace": ns,
                    "MetricName": name,
                    "Dimensions": [{"Name": k, "Value": v} for k, v in dims.items()],
                },
                "Period": period,
                "Stat": stat,
            },
        }

    eu: list[dict[str, Any]] = []
    for m in ("TriggeredRules", "Invocations", "FailedInvocations"):
        eu.append(q(f"events|{m}|{rule}", "AWS/Events", m, {"RuleName": rule}, "Sum"))
    for fn in fns:
        for m, stat in (
            ("Invocations", "Sum"),
            ("Errors", "Sum"),
            ("Throttles", "Sum"),
            ("Duration", "Average"),
        ):
            eu.append(q(f"lambda|{m}|{fn}", "AWS/Lambda", m, {"FunctionName": fn}, stat))
    for api in api_ids:
        for m in ("Count", "4xx", "5xx"):
            eu.append(q(f"apigw|{m}|{api}", "AWS/ApiGateway", m, {"ApiId": api}, "Sum"))
    for db in dbs:
        for m in ("CPUUtilization", "DatabaseConnections", "FreeStorageSpace"):
            eu.append(q(f"rds|{m}|{db}", "AWS/RDS", m, {"DBInstanceIdentifier": db}, "Average"))
    for b in buckets:
        eu.append(
            q(
                f"s3|NumberOfObjects|{b}",
                "AWS/S3",
                "NumberOfObjects",
                {"BucketName": b, "StorageType": "AllStorageTypes"},
                "Average",
                86400,
            )
        )
        for st in ("StandardStorage", "GlacierInstantRetrievalStorage"):
            eu.append(
                q(
                    f"s3|BucketSizeBytes-{st}|{b}",
                    "AWS/S3",
                    "BucketSizeBytes",
                    {"BucketName": b, "StorageType": st},
                    "Average",
                    86400,
                )
            )
    us: list[dict[str, Any]] = []
    for d in dists:
        for m in ("Requests", "BytesDownloaded", "4xxErrorRate"):
            stat = "Average" if "Rate" in m else "Sum"
            us.append(
                q(
                    f"cloudfront|{m}|{d}",
                    "AWS/CloudFront",
                    m,
                    {"DistributionId": d, "Region": "Global"},
                    stat,
                )
            )
    return eu, us


def get_metrics(client: Any, queries: list[dict[str, Any]], end: datetime) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    labels = {qq["Id"]: qq["Label"] for qq in queries}
    for i in range(0, len(queries), 100):
        kwargs: dict[str, Any] = {
            "MetricDataQueries": queries[i : i + 100],
            "StartTime": START,
            "EndTime": end,
        }
        while True:
            r = client.get_metric_data(**kwargs)
            for res in r["MetricDataResults"]:
                for ts, v in zip(res["Timestamps"], res["Values"], strict=True):
                    rows.append(
                        {"series": labels[res["Id"]], "timestamp": ts.isoformat(), "value": v}
                    )
            if "NextToken" not in r:
                break
            kwargs["NextToken"] = r["NextToken"]
    return rows


def collect(out: Path, sections: set[str]) -> None:
    sess = boto3.Session()
    now = datetime.now(UTC)
    print(f"collecting into {out}")

    if "metrics" in sections:
        eu_q, us_q = metric_queries(sess)
        rows = get_metrics(sess.client("cloudwatch", region_name=REGION), eu_q, now)
        rows += get_metrics(sess.client("cloudwatch", region_name="us-east-1"), us_q, now)
        (out / "metrics").mkdir(parents=True, exist_ok=True)
        with (out / "metrics" / "hourly.csv").open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["series", "timestamp", "value"])
            w.writeheader()
            w.writerows(sorted(rows, key=lambda r: (r["series"], r["timestamp"])))
        dump(out / "metrics" / "queries.json", eu_q + us_q)
        print(f"  metrics: {len(eu_q) + len(us_q)} series, {len(rows)} datapoints")

    if "s3" in sections:
        s3 = sess.client("s3")
        for b in [
            b["Name"] for b in s3.list_buckets()["Buckets"] if b["Name"].startswith("media27")
        ]:
            objs = [
                {
                    "key": o["Key"],
                    "size": o["Size"],
                    "last_modified": o["LastModified"].isoformat(),
                    "etag": o["ETag"].strip('"'),
                    "storage_class": o.get("StorageClass"),
                }
                for p in s3.get_paginator("list_objects_v2").paginate(Bucket=b)
                for o in p.get("Contents", [])
            ]
            kind = "raw" if "rawbucket" in b else "frontend"
            dump(
                out / "s3" / f"{kind}_bucket_listing.json",
                {"bucket": b, "listed_at": now, "objects": objs},
            )
            print(f"  s3 {kind}: {len(objs)} objects")

    if "infra" in sections:
        cfn = sess.client("cloudformation", region_name=REGION)
        stacks = [
            s
            for s in cfn.describe_stacks()["Stacks"]
            if s["StackName"].startswith((PREFIX, "CDKToolkit"))
        ]
        for s in stacks:
            name = s["StackName"]
            events = [
                e
                for p in cfn.get_paginator("describe_stack_events").paginate(StackName=name)
                for e in p["StackEvents"]
            ]
            tpl = cfn.get_template(StackName=name, TemplateStage="Original")["TemplateBody"]
            dump(
                out / "infra" / "cloudformation" / f"{name}.json",
                {"stack": s, "events": events, "template": tpl},
            )
        print(f"  cloudformation: {len(stacks)} stacks")

        lam = sess.client("lambda", region_name=REGION)
        fns = [
            redact_env(f)
            for p in lam.get_paginator("list_functions").paginate()
            for f in p["Functions"]
            if f["FunctionName"].startswith(PREFIX)
        ]
        dump(out / "infra" / "lambda_functions.json", fns)
        ev = sess.client("events", region_name=REGION)
        rules = []
        for r in ev.list_rules(NamePrefix=PREFIX)["Rules"]:
            rules.append(
                {
                    "rule": ev.describe_rule(Name=r["Name"]),
                    "targets": ev.list_targets_by_rule(Rule=r["Name"])["Targets"],
                }
            )
        dump(out / "infra" / "eventbridge_rules.json", rules)
        rds = sess.client("rds", region_name=REGION)
        dump(
            out / "infra" / "rds.json",
            {
                "instances": rds.describe_db_instances()["DBInstances"],
                "events_14d": rds.describe_events(Duration=14 * 24 * 60)["Events"],
            },
        )
        apigw = sess.client("apigatewayv2", region_name=REGION)
        apis = [
            a for a in apigw.get_apis()["Items"] if a["Name"].lower().startswith(PREFIX.lower())
        ]
        dump(
            out / "infra" / "apigateway.json",
            [{"api": a, "stages": apigw.get_stages(ApiId=a["ApiId"])["Items"]} for a in apis],
        )
        cf = sess.client("cloudfront")
        dump(
            out / "infra" / "cloudfront.json",
            cf.list_distributions()["DistributionList"].get("Items", []),
        )
        print(f"  configs: {len(fns)} functions, {len(rules)} rules, {len(apis)} APIs")

    if "audit" in sections:
        ct = sess.client("cloudtrail", region_name=REGION)
        n = 0
        (out / "audit").mkdir(parents=True, exist_ok=True)
        with (out / "audit" / "cloudtrail_events.jsonl").open("w") as fh:
            for p in ct.get_paginator("lookup_events").paginate(
                StartTime=now - timedelta(days=90), EndTime=now
            ):
                for e in p["Events"]:
                    fh.write(json.dumps(e, default=str) + "\n")
                    n += 1
                time.sleep(0.5)  # lookup_events is limited to 2 requests/s
        print(f"  cloudtrail: {n} management events")

    if "logs" in sections:
        logs = sess.client("logs", region_name=REGION)
        groups = [
            g["logGroupName"]
            for p in logs.get_paginator("describe_log_groups").paginate(
                logGroupNamePrefix=f"/aws/lambda/{PREFIX}"
            )
            for g in p["logGroups"]
            if g.get("storedBytes", 0) > 0
        ]
        for g in groups:
            evs = [
                e
                for p in logs.get_paginator("filter_log_events").paginate(logGroupName=g)
                for e in p["events"]
            ]
            dump(out / "logs" / f"{g.split('/')[-1]}.json", evs)
        print(f"  logs: {len(groups)} non-empty groups")

    if "billing" in sections:
        ce = sess.client("ce", region_name="us-east-1")
        period = {"Start": "2026-05-01", "End": (now + timedelta(days=1)).strftime("%Y-%m-%d")}
        for key in ("SERVICE", "USAGE_TYPE"):
            r = ce.get_cost_and_usage(
                TimePeriod=period,
                Granularity="MONTHLY",
                Metrics=["UnblendedCost", "UsageQuantity"],
                GroupBy=[{"Type": "DIMENSION", "Key": key}],
            )
            dump(out / "billing" / f"cost_and_usage_by_{key.lower()}.json", r["ResultsByTime"])
        print("  billing: cost and usage by service and usage type")

    if "github" in sections:
        gh = subprocess.run(
            [
                "gh",
                "run",
                "list",
                "--limit",
                "500",
                "--json",
                "databaseId,workflowName,displayTitle,event,status,conclusion,createdAt,updatedAt,headSha,url",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        dump(out / "github" / "actions_runs.json", json.loads(gh))
        print(f"  github: {len(json.loads(gh))} workflow runs")

    if "live" in sections:
        live = {}
        apigw = sess.client("apigatewayv2", region_name=REGION)
        api_url = next(
            a["ApiEndpoint"]
            for a in apigw.get_apis()["Items"]
            if a["Name"].lower().startswith(PREFIX.lower())
        )
        for name, url in (
            ("dashboard", DASHBOARD + "/"),
            ("api_stats", api_url + "/stats"),
            ("api_health", api_url + "/healthz"),
        ):
            req = urllib.request.Request(url, headers={"User-Agent": "media27-evidence/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read()
                live[name] = {
                    "url": url,
                    "status": resp.status,
                    "headers": dict(resp.headers),
                    "fetched_at": datetime.now(UTC),
                }
            (out / "live").mkdir(parents=True, exist_ok=True)
            (out / "live" / f"{name}.body").write_bytes(body)
        dump(out / "live" / "responses.json", live)
        print("  live: dashboard + API responses saved")
    manifest = out / "MANIFEST.json"
    prev = json.loads(manifest.read_text()) if manifest.exists() else {}
    runs = {**prev.get("sections", {}), **{name: now for name in sections}}
    dump(
        manifest,
        {
            "collected_at": prev.get("collected_at", now),
            "region": REGION,
            "start": START,
            "sections": runs,
        },
    )


# ---------------------------------------------------------------- summarize


def summarize(src: Path, dst: Path) -> None:
    """Sanitised, public subset: no account ids, ARNs, IPs, request ids or costs."""
    dst.mkdir(parents=True, exist_ok=True)
    collected_at = json.loads((src / "MANIFEST.json").read_text())["collected_at"]

    # Daily aggregates per metric family (resource ids replaced by roles).
    def role(series: str) -> str | None:
        kind, metric, res = series.split("|")
        if kind == "lambda":
            for k in ("IngestFn", "LoaderFn", "ApiFn"):
                if k in res:
                    return f"lambda_{k[:-2].lower()}_{metric.lower()}"
        if kind == "s3":
            return f"s3_{'raw' if 'rawbucket' in res else 'frontend'}_{metric.lower()}"
        return f"{kind}_{metric.lower()}"

    daily: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    with (src / "metrics" / "hourly.csv").open() as fh:
        for r in csv.DictReader(fh):
            col = role(r["series"])
            if col is None:
                continue
            day = r["timestamp"][:10]
            daily[day][col] += float(r["value"])
            counts[day][col] += 1
    # Averages (duration, RDS, S3 size/objects, rates) are averaged, not summed, per day.
    avg_cols = {
        c
        for d in daily.values()
        for c in d
        if any(k in c for k in ("duration", "rds_", "s3_", "rate"))
    }
    cols = sorted({c for d in daily.values() for c in d})
    with (dst / "daily_metrics.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["date", *cols])
        for day in sorted(daily):
            w.writerow(
                [
                    day,
                    *[
                        ""
                        if c not in daily[day]
                        else round(daily[day][c] / counts[day][c], 3)
                        if c in avg_cols
                        else round(daily[day][c], 3)
                        for c in cols
                    ],
                ]
            )

    # S3 manifest cross-checked against the local archive (single-part ETag = MD5).
    listing = json.loads((src / "s3" / "raw_bucket_listing.json").read_text())
    verified = 0
    with (dst / "s3_raw_manifest.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["key", "size", "last_modified", "etag_md5", "local_copy_md5_match"])
        for o in listing["objects"]:
            rel = o["key"].removeprefix("feeds/")
            match = ""
            for cand in (ROOT / "raw" / rel.replace(".xml", ".aws.xml"), ROOT / "raw" / rel):
                if cand.exists() and hashlib.md5(cand.read_bytes()).hexdigest() == o["etag"]:
                    match = cand.name
                    break
            verified += bool(match)
            w.writerow([o["key"], o["size"], o["last_modified"], o["etag"], match])

    # Stack timeline (names and dates only).
    stacks = []
    for f in sorted((src / "infra" / "cloudformation").glob("*.json")):
        d = json.loads(f.read_text())
        ev = d["events"]
        stacks.append(
            {
                "stack": d["stack"]["StackName"],
                "created": d["stack"]["CreationTime"],
                "last_updated": d["stack"].get("LastUpdatedTime", ""),
                "status": d["stack"]["StackStatus"],
                "n_events": len(ev),
                "first_event": min(e["Timestamp"] for e in ev) if ev else "",
            }
        )
    with (dst / "stacks.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(stacks[0]))
        w.writeheader()
        w.writerows(stacks)

    runs = json.loads((src / "github" / "actions_runs.json").read_text())
    with (dst / "github_actions_runs.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["created_at", "workflow", "conclusion", "commit", "title", "url"])
        for r in sorted(runs, key=lambda r: r["createdAt"]):
            w.writerow(
                [
                    r["createdAt"],
                    r["workflowName"],
                    r["conclusion"],
                    r["headSha"][:7],
                    r["displayTitle"],
                    r["url"],
                ]
            )

    live = json.loads((src / "live" / "responses.json").read_text())
    keep = (
        "date",
        "content-type",
        "server",
        "x-cache",
        "via",
        "x-amz-cf-pop",
        "apigw-requestid",
        "last-modified",
    )
    live_pub = {
        k: {
            "status": v["status"],
            "fetched_at": v["fetched_at"],
            "headers": {h: x for h, x in v["headers"].items() if h.lower() in keep},
        }
        for k, v in live.items()
    }
    dump(dst / "live_responses.json", live_pub)

    summary = {
        "collected_at": collected_at,
        "days_with_metrics": len(daily),
        "s3_raw_objects": len(listing["objects"]),
        "s3_objects_md5_verified_locally": verified,
        "stacks": len(stacks),
        "github_runs": len(runs),
    }
    dump(dst / "summary.json", summary)
    print(json.dumps(summary, indent=1))


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    stamp = datetime.now(UTC).strftime("%Y-%m-%d")
    ap.add_argument("--out", type=Path, default=ROOT / "exports" / f"aws-evidence-{stamp}")
    ap.add_argument("--summarize", action="store_true", help="write the sanitised public subset")
    ap.add_argument(
        "--sections",
        default=",".join(SECTIONS),
        help="comma-separated subset of " + ",".join(SECTIONS),
    )
    ap.add_argument("--public", type=Path, default=ROOT / "dev" / "aws-evidence")
    args = ap.parse_args()
    if args.summarize:
        summarize(args.out, args.public)
    else:
        collect(args.out, set(args.sections.split(",")))


if __name__ == "__main__":
    main()
