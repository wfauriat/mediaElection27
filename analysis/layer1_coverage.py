"""Layer 1: coverage analysis (who gets covered, by whom). See analysis/PLAN.md.

    /opt/venvs/pyDS/bin/python -m analysis.layer1_coverage --snapshot   # fresh DB snapshot
    /opt/venvs/pyDS/bin/python -m analysis.layer1_coverage              # reuse latest snapshot

Writes analysis/reports/layer1-coverage.md and layer1-coverage.html
(static page, data inlined, ECharts from CDN). Hand-written findings in
analysis/findings/layer1.md are inlined into both when present.
"""

from __future__ import annotations

import argparse
import html
import json
import re
from itertools import combinations
from typing import Any

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import leaves_list, linkage
from scipy.spatial.distance import jensenshannon, squareform
from scipy.stats import spearmanr

from analysis.common import (
    BLOCS,
    FINDINGS_DIR,
    LEAN_POSITION,
    REPORTS_DIR,
    ROOT,
    Dataset,
    latest_snapshot,
    snapshot,
)

N_BOOT = 400
CI = (5, 95)  # 90% interval
SEED = 20261114
MIN_WEEK_PAIRS = 5  # an outlet-week enters the all-outlet mean only above this
MIN_EXPECTED = 5  # cells expecting fewer pairs than this at baseline are not assessed


# ---------------------------------------------------------------- helpers


def indicator(ds: Dataset, outlet: str, cols: list[int], title_only: bool = False) -> np.ndarray:
    """Article × candidate 0/1 matrix for one outlet (articles with ≥1 of `cols`)."""
    p = ds.pairs[(ds.pairs["outlet"] == outlet) & ds.pairs["candidate_id"].isin(cols)]
    if title_only:
        p = p[p["in_title"]]
    if p.empty:
        return np.zeros((0, len(cols)))
    m = pd.crosstab(p["article_id"], p["candidate_id"]).reindex(columns=cols, fill_value=0)
    return (m.to_numpy() > 0).astype(float)


def boot_shares(x: np.ndarray, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Point shares (C,) and bootstrap shares (B, C), resampling articles."""
    n = x.shape[0]
    point = x.sum(0) / x.sum()
    w = rng.multinomial(n, np.full(n, 1 / n), size=N_BOOT)  # (B, n) resample weights
    counts = w @ x
    tot = counts.sum(1, keepdims=True)
    return point, counts / np.where(tot == 0, 1, tot)


def lift_table(
    ds: Dataset, cols: list[int], rng: np.random.Generator, title_only: bool = False
) -> dict[str, Any]:
    shares, boots, ns = {}, {}, {}
    for o in ds.outlets:
        x = indicator(ds, o, cols, title_only)
        ns[o] = int(x.sum())
        shares[o], boots[o] = boot_shares(x, rng)
    base = np.mean([shares[o] for o in ds.outlets], axis=0)  # equal-weight baseline
    out: dict[str, Any] = {"baseline": base.tolist(), "rows": {}}
    for o in ds.outlets:
        lift = shares[o] / base
        lo, hi = np.percentile(boots[o] / base, CI, axis=0)
        out["rows"][o] = {
            "n_pairs": ns[o],
            "expected": (ns[o] * base).tolist(),
            "share": shares[o].tolist(),
            "lift": lift.tolist(),
            "lo": lo.tolist(),
            "hi": hi.tolist(),
        }
    return out


# ---------------------------------------------------------------- analyses


def overview(ds: Dataset) -> list[dict[str, Any]]:
    rows = []
    for o in ds.outlets:
        a = ds.articles[ds.articles["outlet"] == o]
        p = ds.pairs[ds.pairs["outlet"] == o]
        rows.append(
            {
                "outlet": o,
                "lean": ds.outlet_lean[o],
                "feeds": ", ".join(ds.outlet_feeds[o]),
                "articles": len(a),
                "with_candidate": int(p["article_id"].nunique()),
                "rate": float(p["article_id"].nunique() / max(len(a), 1)),
                "pairs": len(p),
                "has_summary": o not in ds.no_summary_outlets,
            }
        )
    return rows


def bloc_matrix(ds: Dataset) -> tuple[dict[str, np.ndarray], list[str]]:
    """Per outlet: article × bloc indicator from eligible candidates."""
    elig = ds.candidates[ds.candidates["eligible"]]
    blocs = [b for b in BLOCS if b in set(elig["lean"])]
    cid_bloc = dict(zip(elig["candidate_id"], elig["lean"], strict=True))
    out = {}
    for o in ds.outlets:
        p = ds.pairs[(ds.pairs["outlet"] == o) & ds.pairs["candidate_id"].isin(cid_bloc)].copy()
        p["bloc"] = p["candidate_id"].map(cid_bloc)
        m = pd.crosstab(p["article_id"], p["bloc"]).reindex(columns=blocs, fill_value=0)
        out[o] = (m.to_numpy() > 0).astype(float)
    return out, blocs


def bloc_lifts(ds: Dataset, rng: np.random.Generator) -> dict[str, Any]:
    mats, blocs = bloc_matrix(ds)
    shares, boots = {}, {}
    for o in ds.outlets:
        shares[o], boots[o] = boot_shares(mats[o], rng)
    base = np.mean([shares[o] for o in ds.outlets], axis=0)
    rows = {}
    for o in ds.outlets:
        lo, hi = np.percentile(boots[o] / base, CI, axis=0)
        rows[o] = {
            "n_pairs": int(mats[o].sum()),
            "expected": (mats[o].sum() * base).tolist(),
            "share": shares[o].tolist(),
            "lift": (shares[o] / base).tolist(),
            "lo": lo.tolist(),
            "hi": hi.tolist(),
        }
    return {"blocs": blocs, "baseline": base.tolist(), "rows": rows}


def coverage_position(ds: Dataset, rng: np.random.Generator) -> list[dict[str, Any]]:
    """Mean lean position of an outlet's eligible-candidate pairs, centred on the outlet mean."""
    elig = ds.candidates[ds.candidates["eligible"]]
    cols = elig["candidate_id"].tolist()
    pos = elig["position"].to_numpy(dtype=float)
    raw, boots = {}, {}
    for o in ds.outlets:
        x = indicator(ds, o, cols)
        n = x.shape[0]
        raw[o] = float((x @ pos).sum() / x.sum())
        w = rng.multinomial(n, np.full(n, 1 / n), size=N_BOOT)
        boots[o] = (w @ (x @ pos)) / (w @ x.sum(1))
    centre = float(np.mean(list(raw.values())))
    rows = []
    for o in ds.outlets:
        lo, hi = np.percentile(boots[o] - centre, CI)
        rows.append(
            {
                "outlet": o,
                "lean": ds.outlet_lean[o],
                "raw": raw[o],
                "position": raw[o] - centre,
                "lo": float(lo),
                "hi": float(hi),
            }
        )
    return rows


def prominence(ds: Dataset) -> list[dict[str, Any]]:
    rows = []
    for o in ds.outlets:
        p = ds.pairs[ds.pairs["outlet"] == o]
        rows.append(
            {
                "outlet": o,
                "in_title": float(p["in_title"].mean()) if len(p) else 0.0,
                "comparable": o not in ds.no_summary_outlets,
            }
        )
    return rows


def concentration(ds: Dataset, lifts: dict[str, Any], cols: list[int]) -> list[dict[str, Any]]:
    elig_idx = [
        i
        for i, c in enumerate(cols)
        if bool(ds.candidates.set_index("candidate_id").loc[c, "eligible"])
    ]
    rows = []
    for o in ds.outlets:
        s = np.array(lifts["rows"][o]["share"])[elig_idx]
        s = s / s.sum()
        top3 = float(np.sort(s)[::-1][:3].sum())
        rows.append({"outlet": o, "effective_n": float(1 / (s**2).sum()), "top3_share": top3})
    return rows


def co_mentions(ds: Dataset) -> list[dict[str, Any]]:
    names = ds.candidates.set_index("candidate_id")["display_name"].to_dict()
    by_art = ds.pairs.groupby("article_id")["candidate_id"].apply(lambda s: sorted(set(s)))
    n_art = len(by_art)
    single = ds.pairs.groupby("candidate_id")["article_id"].nunique().to_dict()
    pair_counts: dict[tuple[int, int], int] = {}
    for cs in by_art:
        for a, b in combinations(cs, 2):
            pair_counts[(a, b)] = pair_counts.get((a, b), 0) + 1
    rows = []
    for (a, b), n in pair_counts.items():
        expected = single[a] * single[b] / n_art
        rows.append(
            {"a": names[a], "b": names[b], "n": n, "lift": n / expected, "expected": expected}
        )
    rows.sort(key=lambda r: -r["n"])
    return rows[:20]


def similarity(ds: Dataset, lifts: dict[str, Any]) -> dict[str, Any]:
    vecs = np.array([lifts["rows"][o]["share"] for o in ds.outlets])
    k = len(ds.outlets)
    d = np.zeros((k, k))
    for i in range(k):
        for j in range(i + 1, k):
            d[i, j] = d[j, i] = jensenshannon(vecs[i], vecs[j], base=2)
    order = leaves_list(linkage(squareform(d), method="average")).tolist()
    return {
        "order": [ds.outlets[i] for i in order],
        "matrix": [[float(d[i, j]) for j in order] for i in order],
    }


def weekly(ds: Dataset, cols: list[int]) -> dict[str, Any]:
    p = ds.pairs
    weeks = sorted(p["week"].unique())
    tab = (
        p.groupby(["outlet", "week", "candidate_id"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=cols, fill_value=0)
    )
    tot = tab.sum(1)
    share = tab.div(tot, axis=0)
    per_outlet: dict[str, list[list[float | None]]] = {}
    for o in ds.outlets:
        rows: list[list[float | None]] = []
        for w in weeks:
            if (o, w) in share.index and tot[(o, w)] >= MIN_WEEK_PAIRS:
                rows.append([round(float(v), 4) for v in share.loc[(o, w)]])
            else:
                rows.append([None] * len(cols))
        per_outlet[o] = rows
    allm: list[list[float | None]] = []
    for wi in range(len(weeks)):
        vals = [per_outlet[o][wi] for o in ds.outlets if per_outlet[o][wi][0] is not None]
        allm.append(
            [round(float(np.mean([v[c] for v in vals])), 4) for c in range(len(cols))]
            if vals
            else [None] * len(cols)
        )
    pair_tot = [int(p[p["week"] == w].shape[0]) for w in weeks]
    return {
        "weeks": [pd.Timestamp(w).strftime("%Y-%m-%d") for w in weeks],
        "all": allm,
        "per_outlet": per_outlet,
        "pairs_per_week": pair_tot,
    }


def robustness(full: dict[str, Any], title: dict[str, Any], outlets: list[str]) -> dict[str, Any]:
    a = np.array([full["rows"][o]["lift"] for o in outlets], dtype=float).ravel()
    b = np.array([title["rows"][o]["lift"] for o in outlets], dtype=float).ravel()
    rho = spearmanr(a, b).statistic  # rank-based, so zeros need no special case
    return {"spearman_all_cells": float(rho)}


# ---------------------------------------------------------------- rendering


def fmt_lift(r: dict[str, Any], i: int) -> str:
    v, lo, hi = r["lift"][i], r["lo"][i], r["hi"][i]
    if r["expected"][i] < MIN_EXPECTED:
        return f"({v:.2f})"
    mark = "**" if (lo > 1 or hi < 1) else ""
    return f"{mark}{v:.2f}{mark}"


def md_table(header: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(out)


def render_md(d: dict[str, Any], findings: str) -> str:
    m = d["meta"]
    cand_names = [c["name"] + ("†" if not c["eligible"] else "") for c in d["candidates"]]
    n_elig = sum(c["eligible"] for c in d["candidates"])
    s = [
        "# Layer 1: who gets covered, by whom",
        "",
        f"Snapshot {m['snapshot_at']} · articles published {m['period'][0]} → {m['period'][1]} · "
        f"{m['n_articles']:,} articles · {m['n_with_candidate']:,} mention a tracked politician · "
        f"{m['n_pairs']:,} (article, politician) pairs · {len(d['outlets'])} outlets.",
        "",
        "Interactive version: [`layer1-coverage.html`](./layer1-coverage.html). "
        "Method: [`../PLAN.md`](../PLAN.md).",
        "",
    ]
    if findings:
        s += ["## Key findings", "", findings.strip(), ""]
    s += [
        "## How to read",
        "",
        "- **Lift** = an outlet's share of its political coverage going to X, divided by the "
        "average share across outlets (each outlet weighted equally). 1.00 = typical; 2.00 = twice "
        "the typical attention. **Bold** = the 90% bootstrap interval excludes 1.00. "
        f"(Parentheses) = fewer than {MIN_EXPECTED} pairs expected at baseline: too thin to "
        "assess.",
        "- Coverage measures **attention, not sympathy**: an outlet can cover someone a lot "
        "because it investigates them. Tone comes in layer 2.",
        "- † = tracked but not a candidate (Macron: cannot run); excluded "
        "from blocs, position and concentration.",
        "",
        "## Corpus by outlet",
        "",
        md_table(
            ["Outlet", "Declared lean", "Articles", "Mention a politician", "Rate", "Pairs"],
            [
                [
                    r["outlet"] + ("" if r["has_summary"] else " ‡"),
                    r["lean"],
                    f"{r['articles']:,}",
                    f"{r['with_candidate']:,}",
                    f"{r['rate']:.0%}",
                    f"{r['pairs']:,}",
                ]
                for r in d["overview"]
            ],
        ),
        "",
        "‡ no summaries in the feed (headline only), so fewer mentions are detectable.",
        "",
        "## Coverage position (where each outlet's attention sits, left ↔ right)",
        "",
        "Mean lean of the candidates an outlet covers (hard-left −3 … hard-right +3), minus the "
        "average outlet. Negative = attention tilted toward left-bloc candidates.",
        "",
        md_table(
            ["Outlet", "Declared lean", "Position", "90% interval"],
            [
                [
                    r["outlet"],
                    r["lean"],
                    f"{r['position']:+.2f}",
                    f"[{r['lo']:+.2f}, {r['hi']:+.2f}]",
                ]
                for r in sorted(d["position"], key=lambda r: r["position"])
            ],
        ),
        "",
        "## Bloc lift (eligible candidates grouped by lean)",
        "",
        md_table(
            ["Outlet", *d["blocs"]["blocs"]],
            [
                [o] + [fmt_lift(d["blocs"]["rows"][o], i) for i in range(len(d["blocs"]["blocs"]))]
                for o in d["outlets"]
            ],
        ),
        "",
        "Baseline share per bloc (equal-weight mean of outlets): "
        + ", ".join(
            f"{b} {v:.0%}" for b, v in zip(d["blocs"]["blocs"], d["blocs"]["baseline"], strict=True)
        )
        + ".",
        "",
        "## Politician lift",
        "",
        md_table(
            ["Outlet", *cand_names],
            [
                [o] + [fmt_lift(d["lift"]["rows"][o], i) for i in range(len(cand_names))]
                for o in d["outlets"]
            ],
        ),
        "",
        "Baseline share of voice: "
        + ", ".join(f"{n} {v:.1%}" for n, v in zip(cand_names, d["lift"]["baseline"], strict=True))
        + ".",
        "",
        f"Robustness: recomputing lifts on headline-only mentions gives a Spearman correlation of "
        f"{d['robustness']['spearman_all_cells']:.2f} with the main lifts across all "
        "outlet × politician cells.",
        "",
        "## Prominence and concentration",
        "",
        md_table(
            ["Outlet", "Name in headline", "Effective nb of candidates", "Top-3 share"],
            [
                [
                    p["outlet"],
                    f"{p['in_title']:.0%}" + ("" if p["comparable"] else " ‡"),
                    f"{c['effective_n']:.1f}",
                    f"{c['top3_share']:.0%}",
                ]
                for p, c in zip(d["prominence"], d["concentration"], strict=True)
            ],
        ),
        "",
        f"Effective number of candidates = 1 / Σ share² over eligible candidates ({n_elig} = perfectly "
        "even attention; lower = attention concentrated on a few).",
        "",
        "## Most frequent co-mentions (all outlets)",
        "",
        md_table(
            ["Pair", "Articles", "Observed / expected"],
            [[f"{r['a']} + {r['b']}", str(r["n"]), f"{r['lift']:.1f}×"] for r in d["comentions"]],
        ),
        "",
        "## Caveats",
        "",
        "- Feeds are samples of each outlet's output, not the full output, and section feeds vs "
        "front-page feeds differ (Marianne, Mediapart). All measures are within-outlet shares, "
        "which removes volume but not editorial scope.",
        '- Keyword matching misses indirect references ("le leader insoumis", "le chef de '
        "l'État\"), and the miss rate differs by politician.",
        "- Bootstrap intervals hold the baseline fixed and ignore week-to-week dependence, so "
        "they are somewhat optimistic.",
        "",
    ]
    return "\n".join(s)


def md_inline_to_html(text: str) -> str:
    """Tiny Markdown subset for the findings block: paragraphs, '- ' bullets, **bold**."""
    out, in_list = [], False
    for line in text.strip().splitlines():
        line = html.escape(line)
        line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
        line = re.sub(r"\*(.+?)\*", r"<em>\1</em>", line)
        line = re.sub(r"`(.+?)`", r"<code>\1</code>", line)
        if line.startswith("- "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{line[2:]}</li>")
        elif line.startswith("  ") and in_list and out:
            out[-1] = out[-1].removesuffix("</li>") + " " + line.strip() + "</li>"
        else:
            if in_list:
                out.append("</ul>")
                in_list = False
            if line.strip():
                out.append(f"<p>{line}</p>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


# ---------------------------------------------------------------- main


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", action="store_true", help="take a fresh DB snapshot first")
    args = ap.parse_args()

    snap = snapshot() if args.snapshot else latest_snapshot()
    ds = Dataset(snap)
    rng = np.random.default_rng(SEED)
    cols = ds.candidates["candidate_id"].tolist()

    lifts = lift_table(ds, cols, rng)
    lifts_title = lift_table(ds, cols, rng, title_only=True)
    arts = ds.articles
    data: dict[str, Any] = {
        "meta": {
            "snapshot_at": ds.snapshot_at,
            "snapshot_dir": str(snap.relative_to(ROOT)),
            "period": [
                arts["published_at"].min().strftime("%Y-%m-%d"),
                arts["published_at"].max().strftime("%Y-%m-%d"),
            ],
            "n_articles": len(arts),
            "n_with_candidate": int(ds.pairs["article_id"].nunique()),
            "n_pairs": len(ds.pairs),
            "n_dup_dropped": ds.n_dup_dropped,
            "n_boot": N_BOOT,
            "ci": CI,
            "lean_position": LEAN_POSITION,
        },
        "outlets": ds.outlets,
        "outlet_lean": ds.outlet_lean,
        "candidates": [
            {
                "id": int(r.candidate_id),
                "name": r.display_name,
                "lean": r.lean,
                "eligible": bool(r.eligible),
            }
            for r in ds.candidates.itertuples()
        ],
        "overview": overview(ds),
        "lift": lifts,
        "lift_title": lifts_title,
        "blocs": bloc_lifts(ds, rng),
        "position": coverage_position(ds, rng),
        "prominence": prominence(ds),
        "concentration": concentration(ds, lifts, cols),
        "comentions": co_mentions(ds),
        "similarity": similarity(ds, lifts),
        "weekly": weekly(ds, cols),
        "robustness": robustness(lifts, lifts_title, ds.outlets),
    }

    findings_path = FINDINGS_DIR / "layer1.md"
    findings = findings_path.read_text() if findings_path.exists() else ""

    REPORTS_DIR.mkdir(exist_ok=True)
    (REPORTS_DIR / "layer1-coverage.md").write_text(render_md(data, findings))
    template = (ROOT / "templates" / "layer1.html").read_text()
    page = template.replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False)).replace(
        "<!--__FINDINGS__-->", md_inline_to_html(findings) if findings else ""
    )
    (REPORTS_DIR / "layer1-coverage.html").write_text(page)
    (snap / "layer1.json").write_text(json.dumps(data, ensure_ascii=False, indent=1))
    print(
        f"snapshot {snap.name}: {data['meta']['n_articles']} articles, {data['meta']['n_pairs']} pairs"
    )
    print(f"wrote {REPORTS_DIR / 'layer1-coverage.md'} and .html")


if __name__ == "__main__":
    main()
