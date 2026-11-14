"""Layer 2 report: tone toward each politician, per outlet. See analysis/PLAN.md.

    /opt/venvs/pyDS/bin/python -m analysis.layer2_report            # full-run labels
    /opt/venvs/pyDS/bin/python -m analysis.layer2_report --sample   # eval labels (scaffold check)

Reads the labels produced by analysis.layer2_tone (full Batch run by default,
or the dev+test evaluation labels of the same arm with --sample, to check the
report on real but sparse data), and writes reports/layer2-tone.md and
reports/layer2-tone.html (static page, data inlined, ECharts from CDN).
Hand-written findings in analysis/findings/layer2.md are inlined when present.

Descriptive only: an outlet's tone is compared with the average outlet on the
same politician over the whole period. Correcting for what happened each week
(a bad week is negative everywhere) is layer 3.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

import numpy as np
import pandas as pd

from analysis.common import FINDINGS_DIR, LEAN_POSITION, REPORTS_DIR, ROOT, Dataset, latest_snapshot
from analysis.layer1_coverage import md_inline_to_html, md_table
from analysis.layer2_tone import (
    FRAMES,
    FULL_ARM,
    agreement,
    cost,
    full_dir,
    label_map,
    read_jsonl,
    total_usage,
)

N_BOOT = 400
CI = (5, 95)
SEED = 20261114
MIN_CELL = 10  # labels needed in an outlet × politician (or bloc) cell to assess it
MIN_MONTH = 5  # labels needed in an outlet-month to plot it
N_EXAMPLES = 4
SIGN = {"positive": 1, "negative": -1, "neutral": 0, "mixed": 0}
LEFT = {"hard-left", "left", "centre-left"}
RIGHT = {"centre-right", "right", "hard-right"}
VOICE_ORDER = ["editorial", "event", "quoted", "self"]
SCOPES = {"all": "all voices", "editorial": "outlet's own wording only"}


# ---------------------------------------------------------------- data


def load_labels(snap_dir: Any, sample: bool) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Labels as a flat frame + provenance. --sample uses the eval runs of the full-run arm."""
    if not sample:
        run = full_dir(snap_dir)
        meta = json.loads((run / "batch.json").read_text())
        return pd.read_csv(run / "labels.csv"), {"source": "full", **meta}
    rows, usd = [], 0.0
    for split in ("dev", "test"):
        for f in (snap_dir / "layer2_eval" / split).glob(f"{FULL_ARM.name}__*.jsonl"):
            res = read_jsonl(f)
            usd += cost(total_usage(res), FULL_ARM.model)
            for r in res:
                for lab in r.get("labels", []):
                    rows.append({"article_id": r["article_id"], "outlet": r["outlet"], **lab})
    df = pd.DataFrame(rows)
    return df, {"source": "sample", "arm": FULL_ARM.version, "collected_usd": round(usd, 4)}


def prepare(ds: Dataset, labels: pd.DataFrame) -> pd.DataFrame:
    cands = ds.candidates.rename(columns={"display_name": "politician"})
    df = labels.drop(columns=["candidate_id"], errors="ignore").merge(
        cands[["politician", "candidate_id", "lean", "eligible"]], on="politician"
    )
    df = df.merge(ds.articles[["article_id", "title", "published_at"]], on="article_id")
    df["sign"] = df["tone"].map(SIGN)
    # "Editorial" scope: only the outlet's own wording carries a sign.
    df["sign_editorial"] = np.where(df["voice"] == "editorial", df["sign"], 0)
    df["month"] = df["published_at"].dt.strftime("%Y-%m")
    df["side"] = np.select(
        [df["lean"].isin(LEFT) & df["eligible"], df["lean"].isin(RIGHT) & df["eligible"]],
        ["left", "right"],
        default="",
    )
    return df


# ---------------------------------------------------------------- statistics


def boot_net(signs: np.ndarray, groups: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Bootstrap mean sign, resampling articles (clusters), not labels."""
    uniq, inv = np.unique(groups, return_inverse=True)
    sums = np.bincount(inv, weights=signs)
    counts = np.bincount(inv)
    w = rng.multinomial(len(uniq), np.full(len(uniq), 1 / len(uniq)), size=N_BOOT)
    return (w @ sums) / np.maximum(w @ counts, 1)


def cell_table(
    df: pd.DataFrame, key: str, cols: list[Any], outlets: list[str], rng: np.random.Generator
) -> dict[str, Any]:
    """Outlet × `key` net tone, relative to the equal-weight mean of assessable outlets."""
    out: dict[str, Any] = {}
    for scope, sign_col in (("all", "sign"), ("editorial", "sign_editorial")):
        net = pd.DataFrame(np.nan, index=outlets, columns=cols)
        n = (
            df.groupby(["outlet", key])
            .size()
            .unstack(fill_value=0)
            .reindex(index=outlets, columns=cols, fill_value=0)
        )
        boots: dict[tuple[str, Any], np.ndarray] = {}
        for (o, c), g in df.groupby(["outlet", key]):
            if c not in cols or o not in outlets:
                continue
            net.loc[o, c] = g[sign_col].mean()
            if len(g) >= MIN_CELL:
                boots[(o, c)] = boot_net(
                    g[sign_col].to_numpy(float), g["article_id"].to_numpy(), rng
                )
        ok = n >= MIN_CELL
        baseline = net.where(ok).mean(axis=0)
        rows = {}
        for o in outlets:
            rel, lo, hi = [], [], []
            for c in cols:
                if (o, c) in boots:
                    b = boots[(o, c)] - baseline[c]
                    rel.append(float(net.loc[o, c] - baseline[c]))
                    lo.append(float(np.percentile(b, CI[0])))
                    hi.append(float(np.percentile(b, CI[1])))
                else:
                    rel.append(None)
                    lo.append(None)
                    hi.append(None)
            rows[o] = {
                "n": [int(n.loc[o, c]) for c in cols],
                "net": [None if pd.isna(net.loc[o, c]) else float(net.loc[o, c]) for c in cols],
                "rel": rel,
                "lo": lo,
                "hi": hi,
            }
        out[scope] = {
            "baseline": [None if pd.isna(v) else float(v) for v in baseline],
            "rows": rows,
        }
    return out


def politician_summary(
    df: pd.DataFrame, ds: Dataset, rng: np.random.Generator
) -> list[dict[str, Any]]:
    """Press-average net tone per politician (equal-weight over outlets with ≥ MIN_CELL labels)."""
    rows = []
    for c in ds.candidates.itertuples():
        g = df[df["candidate_id"] == c.candidate_id]
        if g.empty:
            continue
        per_outlet = [(o, gg) for o, gg in g.groupby("outlet") if len(gg) >= MIN_CELL]
        if per_outlet:
            net = float(np.mean([gg["sign"].mean() for _, gg in per_outlet]))
            b = np.mean(
                [
                    boot_net(gg["sign"].to_numpy(float), gg["article_id"].to_numpy(), rng)
                    for _, gg in per_outlet
                ],
                axis=0,
            )
            lo, hi = (float(v) for v in np.percentile(b, CI))
        else:
            net, lo, hi = float(g["sign"].mean()), None, None
        rows.append(
            {
                "politician": c.display_name,
                "eligible": bool(c.eligible),
                "lean": c.lean,
                "n": len(g),
                "n_outlets": len(per_outlet),
                "pos": float((g["tone"] == "positive").mean()),
                "neg": float((g["tone"] == "negative").mean()),
                "net": net,
                "lo": lo,
                "hi": hi,
                "scandal": float((g["frame"] == "scandal_justice").mean()),
            }
        )
    return sorted(rows, key=lambda r: r["net"])


def tone_slant(df: pd.DataFrame, outlets: list[str], rng: np.random.Generator) -> dict[str, Any]:
    """(relative net tone toward right-bloc candidates) − (toward left-bloc candidates).

    Positive = the outlet treats right-bloc candidates more favourably than left-bloc ones,
    compared with the average outlet. Eligible candidates only; centre excluded.
    """
    out: dict[str, Any] = {}
    sided = df[df["side"] != ""]
    for scope, col in (("all", "sign"), ("editorial", "sign_editorial")):
        raw, boots = {}, {}
        for o in outlets:
            g = sided[sided["outlet"] == o]
            parts = {s: g[g["side"] == s] for s in ("left", "right")}
            if min(len(p) for p in parts.values()) < MIN_CELL:
                continue
            raw[o] = parts["right"][col].mean() - parts["left"][col].mean()
            boots[o] = boot_net(
                parts["right"][col].to_numpy(float), parts["right"]["article_id"].to_numpy(), rng
            ) - boot_net(
                parts["left"][col].to_numpy(float), parts["left"]["article_id"].to_numpy(), rng
            )
        centre = float(np.mean(list(raw.values()))) if raw else 0.0
        out[scope] = [
            {
                "outlet": o,
                "slant": float(raw[o] - centre),
                "lo": float(np.percentile(boots[o] - centre, CI[0])),
                "hi": float(np.percentile(boots[o] - centre, CI[1])),
                "n_left": int(((sided["outlet"] == o) & (sided["side"] == "left")).sum()),
                "n_right": int(((sided["outlet"] == o) & (sided["side"] == "right")).sum()),
            }
            for o in raw
        ]
    return out


def voice_mix(df: pd.DataFrame, outlets: list[str]) -> dict[str, Any]:
    """Per outlet: share of its negative (and positive) labels carried by each voice."""
    out: dict[str, Any] = {}
    for tone in ("negative", "positive"):
        g = df[df["tone"] == tone]
        tab = g.groupby(["outlet", "voice"]).size().unstack(fill_value=0)
        tab = tab.reindex(index=outlets, columns=VOICE_ORDER, fill_value=0)
        share = tab.div(tab.sum(axis=1).replace(0, np.nan), axis=0)
        out[tone] = {
            "n": tab.sum(axis=1).astype(int).tolist(),
            "share": [[None if pd.isna(v) else float(v) for v in row] for row in share.to_numpy()],
        }
    rate = df.groupby("outlet").apply(
        lambda g: float(((g["voice"] == "editorial") & (g["tone"] == "negative")).mean()),
        include_groups=False,
    )
    out["editorial_negative_rate"] = [float(rate.get(o, np.nan)) for o in outlets]
    return out


def frame_mix(df: pd.DataFrame, outlets: list[str]) -> dict[str, Any]:
    tab = df.groupby(["outlet", "frame"]).size().unstack(fill_value=0)
    tab = tab.reindex(index=outlets, columns=FRAMES, fill_value=0)
    share = tab.div(tab.sum(axis=1).replace(0, np.nan), axis=0).fillna(0)
    return {"frames": FRAMES, "share": share.to_numpy().round(4).tolist()}


def monthly(df: pd.DataFrame, outlets: list[str], politicians: list[str]) -> dict[str, Any]:
    months = sorted(df["month"].unique())
    g = df.groupby(["outlet", "politician", "month"])["sign"].agg(["mean", "size"])
    per: dict[str, dict[str, list[float | None]]] = {o: {} for o in outlets}
    for o in outlets:
        for p in politicians:
            per[o][p] = [
                round(float(g.loc[(o, p, m), "mean"]), 3)
                if (o, p, m) in g.index and g.loc[(o, p, m), "size"] >= MIN_MONTH
                else None
                for m in months
            ]
    avg = {
        p: [
            (lambda vals: round(float(np.mean(vals)), 3) if vals else None)(
                [per[o][p][i] for o in outlets if per[o][p][i] is not None]
            )
            for i in range(len(months))
        ]
        for p in politicians
    }
    return {"months": months, "per_outlet": per, "all": avg}


def examples(df: pd.DataFrame) -> dict[str, list[dict[str, str]]]:
    """A few labelled headlines per outlet × politician: editorial first, then other non-neutral."""
    rank = {"editorial": 0, "event": 1, "quoted": 2, "self": 3, "none": 4}
    out: dict[str, list[dict[str, str]]] = {}
    d = df.assign(_r=df["voice"].map(rank), _s=(df["salience"] != "main").astype(int))
    for (o, p), g in d.sort_values(
        ["_r", "_s", "published_at"], ascending=[True, True, False]
    ).groupby(["outlet", "politician"]):
        out[f"{o}||{p}"] = [
            {
                "title": r.title,
                "date": r.published_at.strftime("%Y-%m-%d"),
                "tone": r.tone,
                "voice": r.voice,
                "frame": r.frame,
                "evidence": r.evidence,
            }
            for r in g.head(N_EXAMPLES).itertuples()
        ]
    return out


def validation(snap: Any) -> dict[str, Any]:
    """Agreement of the full-run arm with the reference model on dev and test samples."""
    out = {}
    for split in ("dev", "test"):
        d = snap / "layer2_eval" / split
        arm = list(d.glob(f"{FULL_ARM.name}__*.jsonl"))
        refs = sorted(d.glob("opus-*__*.jsonl"))
        if not arm or not refs:
            continue
        ag = agreement(label_map(read_jsonl(arm[0])), label_map(read_jsonl(refs[-1])))
        out[split] = {**ag, "reference": refs[-1].name.split("__")[0]}
    return out


# ---------------------------------------------------------------- rendering


def fmt_rel(row: dict[str, Any], i: int) -> str:
    v, lo, hi = row["rel"][i], row["lo"][i], row["hi"][i]
    if v is None:
        return f"({row['n'][i]})" if row["n"][i] else "–"
    mark = "**" if (lo > 0 or hi < 0) else ""
    return f"{mark}{v:+.2f}{mark}"


def render_md(d: dict[str, Any], findings: str) -> str:
    m = d["meta"]
    banner = (
        [
            "> **Scaffold run on evaluation labels only** "
            f"({m['n_labels']} labels): the structure is final, the numbers are not. "
            "Re-run without `--sample` once the full batch is collected.",
            "",
        ]
        if m["source"] == "sample"
        else []
    )
    pol_names = [p for p in d["politicians"]]
    s = [
        "# Layer 2: how each outlet presents each politician (tone)",
        "",
        *banner,
        f"Snapshot {m['snapshot_at']} · {m['n_labels']:,} (article, politician) labels from "
        f"{m['n_articles']:,} articles · arm `{m['arm']}` · {m['excluded_incidental']:,} incidental "
        "mentions excluded · labelling cost ≈ "
        f"${m['cost_usd']:.2f}.",
        "",
        "Interactive version: [`layer2-tone.html`](./layer2-tone.html). Method: "
        "[`../PLAN.md`](../PLAN.md). Coverage (who gets attention) is layer 1.",
        "",
    ]
    if findings:
        s += ["## Key findings", "", findings.strip(), ""]
    s += [
        "## How to read",
        "",
        "- **Net tone** = (positive − negative) / labels, from −1 (all negative) to +1. Neutral "
        "and mixed count 0.",
        "- **Relative tone** = an outlet's net tone on X minus the press average on X (each "
        f"outlet weighted equally, among outlets with ≥ {MIN_CELL} labels). **Bold** = the 90% "
        "bootstrap interval excludes 0; (n) = too few labels to assess.",
        "- **All voices** = what a reader sees. **Editorial** = only the outlet's own wording "
        "carries a sign; events, quotes and the politician's own words count as 0.",
        "- Descriptive: a politician's bad month is negative everywhere. Layer 3 compares "
        "outlets within the same weeks.",
        "",
        "## Tone slant per outlet",
        "",
        "Relative net tone toward right-bloc candidates minus toward left-bloc candidates "
        "(eligible candidates, centre excluded), centred on the average outlet. Positive = "
        "more favourable to the right than the average outlet.",
        "",
    ]
    for scope, label in SCOPES.items():
        rows = sorted(d["slant"][scope], key=lambda r: r["slant"])
        s += [
            f"**{label.capitalize()}**",
            "",
            md_table(
                ["Outlet", "Declared lean", "Slant", "90% interval", "Labels left / right"],
                [
                    [
                        r["outlet"],
                        d["outlet_lean"][r["outlet"]],
                        f"{r['slant']:+.2f}",
                        f"[{r['lo']:+.2f}, {r['hi']:+.2f}]",
                        f"{r['n_left']} / {r['n_right']}",
                    ]
                    for r in rows
                ],
            )
            if rows
            else "_Not enough labels._",
            "",
        ]
    s += [
        "## Press-average tone per politician",
        "",
        md_table(
            [
                "Politician",
                "Labels",
                "Outlets assessed",
                "Positive",
                "Negative",
                "Net",
                "90% interval",
                "Scandal frame",
            ],
            [
                [
                    r["politician"] + ("" if r["eligible"] else " †"),
                    str(r["n"]),
                    str(r["n_outlets"]),
                    f"{r['pos']:.0%}",
                    f"{r['neg']:.0%}",
                    f"{r['net']:+.2f}",
                    "–" if r["lo"] is None else f"[{r['lo']:+.2f}, {r['hi']:+.2f}]",
                    f"{r['scandal']:.0%}",
                ]
                for r in d["politician_summary"]
            ],
        ),
        "",
    ]
    for scope, label in SCOPES.items():
        s += [
            f"## Relative tone by bloc ({label})",
            "",
            md_table(
                ["Outlet", *d["blocs"]],
                [
                    [o, *[fmt_rel(d["bloc"][scope]["rows"][o], i) for i in range(len(d["blocs"]))]]
                    for o in d["outlets"]
                ],
            ),
            "",
        ]
    s += [
        "## Relative tone by politician (all voices)",
        "",
        md_table(
            ["Outlet", *pol_names],
            [
                [o, *[fmt_rel(d["cand"]["all"]["rows"][o], i) for i in range(len(pol_names))]]
                for o in d["outlets"]
            ],
        ),
        "",
        "## Who carries the negativity",
        "",
        md_table(
            ["Outlet", "Negative labels", *VOICE_ORDER, "Editorial-negative rate"],
            [
                [
                    o,
                    str(d["voice"]["negative"]["n"][i]),
                    *["–" if v is None else f"{v:.0%}" for v in d["voice"]["negative"]["share"][i]],
                    f"{d['voice']['editorial_negative_rate'][i]:.0%}",
                ]
                for i, o in enumerate(d["outlets"])
            ],
        ),
        "",
        "Editorial-negative rate = share of all an outlet's labels that are negative *in its own "
        "wording*.",
        "",
        "## Validation",
        "",
    ]
    for split, v in d["validation"].items():
        s.append(
            f"- `{split}` sample ({v['n']} pairs, reference `{v['reference']}`): tone agreement "
            f"{v['tone']:.0%} (κ {v['tone_kappa']:.2f}), {v['opposite_sign']} opposite-sign, "
            f"voice {v['voice']:.0%}, frame {v['frame']:.0%}."
        )
    s += [
        "",
        "Known limitations (see PLAN.md): headlines contradicted by their summary can be "
        "misread; voice is the least reliable field; keyword-based mention detection misses "
        "indirect references.",
        "",
    ]
    return "\n".join(s)


def main() -> None:
    global MIN_CELL
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true", help="use eval labels (scaffold check)")
    ap.add_argument("--keep-incidental", action="store_true")
    ap.add_argument("--min-cell", type=int, default=MIN_CELL, help="lower only for scaffold checks")
    args = ap.parse_args()
    MIN_CELL = args.min_cell

    snap = latest_snapshot()
    ds = Dataset(snap)
    labels, prov = load_labels(snap, args.sample)
    df = prepare(ds, labels)
    n_incidental = int((df["salience"] == "incidental").sum())
    if not args.keep_incidental:
        df = df[df["salience"] != "incidental"]
    rng = np.random.default_rng(SEED)
    outlets = [o for o in ds.outlets if o in set(df["outlet"])]
    politicians = [p for p in ds.candidates["display_name"] if p in set(df["politician"])]
    elig = ds.candidates[ds.candidates["eligible"]]
    blocs = [b for b in LEAN_POSITION if b in set(elig["lean"])]
    layer1 = snap / "layer1.json"
    coverage_pos = (
        {r["outlet"]: r for r in json.loads(layer1.read_text())["position"]}
        if layer1.exists()
        else {}
    )

    data: dict[str, Any] = {
        "meta": {
            "source": prov["source"],
            "arm": prov.get("arm", FULL_ARM.version),
            "cost_usd": prov.get("collected_usd") or 0.0,
            "snapshot_at": ds.snapshot_at,
            "n_labels": len(df),
            "n_articles": int(df["article_id"].nunique()),
            "excluded_incidental": 0 if args.keep_incidental else n_incidental,
            "min_cell": MIN_CELL,
            "ci": CI,
            "n_boot": N_BOOT,
        },
        "outlets": outlets,
        "outlet_lean": ds.outlet_lean,
        "politicians": politicians,
        "eligible": {
            p: bool(e)
            for p, e in zip(ds.candidates["display_name"], ds.candidates["eligible"], strict=True)
        },
        "blocs": blocs,
        "tone_mix": df["tone"].value_counts().to_dict(),
        "politician_summary": politician_summary(df, ds, rng),
        "bloc": cell_table(df[df["eligible"]], "lean", blocs, outlets, rng),
        "cand": cell_table(df, "politician", politicians, outlets, rng),
        "slant": tone_slant(df, outlets, rng),
        "coverage_position": {o: coverage_pos[o]["position"] for o in outlets if o in coverage_pos},
        "voice": voice_mix(df, outlets),
        "frames": frame_mix(df, outlets),
        "monthly": monthly(df, outlets, politicians),
        "examples": examples(df),
        "validation": validation(snap),
    }

    findings_path = FINDINGS_DIR / "layer2.md"
    findings = findings_path.read_text() if findings_path.exists() else ""
    REPORTS_DIR.mkdir(exist_ok=True)
    (REPORTS_DIR / "layer2-tone.md").write_text(render_md(data, findings))
    template = (ROOT / "templates" / "layer2.html").read_text()
    page = template.replace(
        "/*__DATA__*/null", json.dumps(data, ensure_ascii=False, default=str)
    ).replace("<!--__FINDINGS__-->", md_inline_to_html(findings) if findings else "")
    (REPORTS_DIR / "layer2-tone.html").write_text(page)
    print(f"{prov['source']}: {len(df)} labels, {data['meta']['n_articles']} articles")
    print(f"wrote {REPORTS_DIR / 'layer2-tone.md'} and .html")


if __name__ == "__main__":
    main()
