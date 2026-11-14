"""Shared data access and reference metadata for the analysis layers.

Runs with the shared data-science venv (/opt/venvs/pyDS: numpy, pandas,
scipy, anthropic), which has no Postgres driver. Data is therefore read
through `psql` inside the docker container (`COPY ... TO STDOUT CSV`) and
frozen as a dated CSV snapshot under analysis/data/, so every report is
tied to a reproducible input.
"""

from __future__ import annotations

import io
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"
FINDINGS_DIR = ROOT / "findings"

PG_CONTAINER = "media27-postgres"
PG_USER = "media27"
PG_DB = "media27"

SCOPE_START = "2026-05-15"  # first local ingest; earlier pubdates are back-catalogue

# Lean axis used for "coverage position". Outlets labelled public /
# sovereigntist have no position on it and are only used for ordering.
LEAN_POSITION: dict[str, int] = {
    "hard-left": -3,
    "left": -2,
    "centre-left": -1,
    "centre": 0,
    "centre-right": 1,
    "right": 2,
    "hard-right": 3,
}
BLOCS = list(LEAN_POSITION)

# Display order for outlets: declared lean, left to right, then the rest.
OUTLET_LEAN_ORDER = [
    "hard-left",
    "left",
    "centre-left",
    "centre",
    "public",
    "centre-right",
    "right",
    "sovereigntist",
]

QUERIES: dict[str, str] = {
    "sources": "SELECT id AS source_id, slug, outlet, section, lean FROM sources",
    "candidates": (
        "SELECT id AS candidate_id, slug, display_name, party, lean, eligible FROM candidates"
    ),
    "articles": f"""
        SELECT a.id AS article_id, a.source_id, a.url, a.published_at, a.title, a.summary
        FROM articles a
        WHERE a.published_at >= '{SCOPE_START}' AND a.published_at <= now()
    """,
    "pairs": """
        SELECT m.article_id, m.candidate_id, bool_or(m.field = 'title') AS in_title
        FROM mentions m
        WHERE m.extractor = 'keyword'
        GROUP BY 1, 2
    """,
}


def _psql_csv(query: str) -> pd.DataFrame:
    sql = f"COPY ({' '.join(query.split())}) TO STDOUT WITH (FORMAT csv, HEADER true)"
    out = subprocess.run(
        ["docker", "exec", "-i", PG_CONTAINER, "psql", "-U", PG_USER, "-d", PG_DB, "-c", sql],
        check=True,
        capture_output=True,
    ).stdout
    return pd.read_csv(io.BytesIO(out), keep_default_na=False, na_values=[""])


def snapshot(tag: str | None = None) -> Path:
    """Dump the analysis inputs to analysis/data/<tag>/ and return the dir."""
    tag = tag or datetime.now(UTC).strftime("%Y-%m-%d")
    out = DATA_DIR / tag
    out.mkdir(parents=True, exist_ok=True)
    for name, q in QUERIES.items():
        _psql_csv(q).to_csv(out / f"{name}.csv", index=False)
    (out / "SNAPSHOT_AT").write_text(datetime.now(UTC).isoformat(timespec="seconds") + "\n")
    return out


def latest_snapshot() -> Path:
    dirs = sorted(p for p in DATA_DIR.glob("*") if (p / "SNAPSHOT_AT").exists())
    if not dirs:
        raise SystemExit("no snapshot yet: run with --snapshot")
    return dirs[-1]


class Dataset:
    """Analysis-ready tables, with France Info's two feeds merged into one outlet."""

    def __init__(self, snap_dir: Path) -> None:
        self.snap_dir = snap_dir
        self.snapshot_at = (snap_dir / "SNAPSHOT_AT").read_text().strip()
        sources = pd.read_csv(snap_dir / "sources.csv")
        cands = pd.read_csv(snap_dir / "candidates.csv")
        arts = pd.read_csv(snap_dir / "articles.csv", parse_dates=["published_at"])
        pairs = pd.read_csv(snap_dir / "pairs.csv")

        arts = arts.merge(sources[["source_id", "outlet"]], on="source_id")
        # One outlet = one editorial voice: merge feeds, then drop the same
        # URL appearing in two feeds of one outlet (keep the first seen).
        n_before = len(arts)
        arts = arts.sort_values("article_id").drop_duplicates(["outlet", "url"])
        self.n_dup_dropped = n_before - len(arts)
        arts["week"] = (
            arts["published_at"].dt.tz_convert("UTC").dt.tz_localize(None).dt.to_period("W-SUN")
        ).dt.start_time
        self.articles = arts

        pairs = pairs[pairs["article_id"].isin(arts["article_id"])]
        pairs["in_title"] = pairs["in_title"].astype(str).str.lower().isin(["t", "true"])
        self.pairs = pairs.merge(arts[["article_id", "outlet", "week"]], on="article_id")

        # Inactive feeds with no article in scope (La Croix, Les Échos) drop out here.
        outlet_lean = (
            sources[sources["outlet"].isin(arts["outlet"])].groupby("outlet")["lean"].first()
        )
        order = sorted(
            outlet_lean.index,
            key=lambda o: (OUTLET_LEAN_ORDER.index(outlet_lean[o]), o),
        )
        self.outlets: list[str] = order
        self.outlet_lean: dict[str, str] = outlet_lean.to_dict()
        self.outlet_feeds: dict[str, list[str]] = (
            sources.groupby("outlet")["slug"].apply(sorted).to_dict()
        )

        cands["eligible"] = cands["eligible"].astype(str).str.lower().isin(["t", "true"])
        cands["position"] = cands["lean"].map(LEAN_POSITION)
        cands = cands.sort_values(
            ["eligible", "position", "display_name"], ascending=[False, True, True]
        )
        self.candidates = cands.reset_index(drop=True)
        self.no_summary_outlets = [
            o
            for o, g in arts.groupby("outlet")
            if (g["summary"].fillna("").str.len() > 20).mean() < 0.5
        ]
