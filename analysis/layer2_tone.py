"""Layer 2: tone toward each politician, labelled by Claude. See analysis/PLAN.md.

    /opt/venvs/pyDS/bin/python -m analysis.layer2_tone pilot --n-pairs 50
    /opt/venvs/pyDS/bin/python -m analysis.layer2_tone eval --n-pairs 200

One request per article: headline + summary (HTML stripped) and the list of
tracked politicians the keyword extractor found in it. The model returns one
label per politician (tone, voice, frame, salience, evidence) under a strict
JSON schema. The outlet name is deliberately NOT sent, so the model cannot
lean on its own priors about an outlet's politics.

Codebooks live in analysis/codebooks/tone-<name>.txt; a codebook's version id
is the first 8 hex chars of its SHA-256, so any edit is a new version.

- `pilot`: one arm on a small round-robin sample, every label printed for
  reading (reports/layer2-pilot.md).
- `eval`: a fresh sample (disjoint from pilot articles) labelled by several
  arms (model × codebook × effort) and by a reference arm (a larger model,
  same codebook); agreement of each arm with the reference, cost per arm, and
  the disagreements for review (reports/layer2-eval.md).
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import time
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import anthropic
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sklearn.metrics import cohen_kappa_score

from analysis.common import REPORTS_DIR, ROOT, Dataset, latest_snapshot

load_dotenv(ROOT.parent / ".env")
HAIKU = os.environ.get("ANALYSIS_MODEL", "claude-haiku-5-5")
REFERENCE_MODEL = "claude-opus-5-5"
MODEL_ALIASES = {"haiku": HAIKU, "opus": REFERENCE_MODEL}
CODEBOOK_DIR = ROOT / "codebooks"
CURRENT_CODEBOOK = "v4"
MAX_TOKENS = 8000  # thinking + a few labels; reference model thinks more
PILOT_SEED = 20261114
SAMPLE_SEEDS = {"dev": 20261115, "test": 20261116}

# List prices, USD per million tokens: (input, output). Cache writes 1.25x
# input, cache reads 0.1x input, Batch API 50% off. Verify on the pricing
# page before a large run.
PRICES = {"claude-haiku-5-5": (0.10, 0.50), "claude-opus-5-5": (4.00, 20.00)}
CACHE_WRITE, CACHE_READ, BATCH_FACTOR = 1.25, 0.1, 0.5

TONES = ["positive", "neutral", "negative", "mixed"]
VOICES = ["editorial", "event", "quoted", "self", "none"]
SALIENCE = ["main", "secondary", "incidental"]
FRAMES = [
    "horse_race",
    "programme",
    "scandal_justice",
    "strategy_alliances",
    "campaign_event",
    "governing",
    "personal",
    "other",
]


# ---------------------------------------------------------------- codebooks & arms


def load_codebook(name: str) -> tuple[str, str]:
    text = (CODEBOOK_DIR / f"tone-{name}.txt").read_text()
    return text, hashlib.sha256(text.encode()).hexdigest()[:8]


@dataclass(frozen=True)
class Arm:
    name: str
    model: str
    codebook: str
    effort: str

    @property
    def codebook_text(self) -> str:
        return load_codebook(self.codebook)[0]

    @property
    def version(self) -> str:
        return f"{self.model}+{load_codebook(self.codebook)[1]}+{self.effort}"

    @classmethod
    def from_name(cls, name: str) -> Arm:
        """'haiku-v4-medium' -> Arm(model=Haiku, codebook='v4', effort='medium')."""
        alias, codebook, effort = name.split("-")
        return cls(name, MODEL_ALIASES[alias], codebook, effort)


DEFAULT_ARM = Arm.from_name(f"haiku-{CURRENT_CODEBOOK}-low")


# ---------------------------------------------------------------- requests


def clean(text: str | float | None) -> str:
    if not isinstance(text, str):
        return ""
    text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    return re.sub(r"\s+", " ", text).strip()


def schema_for(names: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "labels": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "politician": {"type": "string", "enum": names},
                        "tone": {"type": "string", "enum": TONES},
                        "voice": {"type": "string", "enum": VOICES},
                        "frame": {"type": "string", "enum": FRAMES},
                        "salience": {"type": "string", "enum": SALIENCE},
                        "evidence": {"type": "string"},
                    },
                    "required": ["politician", "tone", "voice", "frame", "salience", "evidence"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["labels"],
        "additionalProperties": False,
    }


def build_request(item: dict[str, Any], arm: Arm) -> dict[str, Any]:
    pols = item["politicians"]
    listed = "\n".join(f"- {p['name']} ({p['party']})" for p in pols)
    user = (
        f"Headline: {item['title']}\n"
        f"Summary: {item['summary'] or '(no summary)'}\n\n"
        f"Politicians to label (one label each):\n{listed}"
    )
    return {
        "model": arm.model,
        "max_tokens": MAX_TOKENS,
        "system": [
            {"type": "text", "text": arm.codebook_text, "cache_control": {"type": "ephemeral"}}
        ],
        "messages": [{"role": "user", "content": user}],
        "output_config": {
            "effort": arm.effort,
            "format": {"type": "json_schema", "schema": schema_for([p["name"] for p in pols])},
        },
    }


def call(client: anthropic.Anthropic, req: dict[str, Any]) -> Any:
    if req["model"] == REFERENCE_MODEL:
        # Server-side refusal fallback (opt-in, recommended for this model).
        # The installed SDK predates the typed `fallbacks` parameter, hence extra_body.
        return client.beta.messages.create(
            **req,
            betas=["server-side-fallback-2026-07-01"],
            extra_body={"fallbacks": "default"},
        )
    return client.messages.create(**req)


def parse_message(msg: Any, item: dict[str, Any], out: dict[str, Any]) -> dict[str, Any]:
    """Shared post-processing for live and batch responses."""
    out["served_by"] = msg.model
    u = msg.usage
    out["usage"] = {
        "input": u.input_tokens,
        "output": u.output_tokens,
        "cache_read": u.cache_read_input_tokens or 0,
        "cache_write": u.cache_creation_input_tokens or 0,
    }
    out["stop_reason"] = msg.stop_reason
    if msg.stop_reason != "end_turn":
        details = getattr(msg, "stop_details", None)
        return {**out, "error": f"stop_reason={msg.stop_reason} {details or ''}".strip()}
    text = next(b.text for b in msg.content if b.type == "text")
    labels = json.loads(text)["labels"]
    expected = sorted(p["name"] for p in item["politicians"])
    if sorted(lab["politician"] for lab in labels) != expected:
        out["warning"] = f"label set mismatch: expected {expected}"
    # The schema cannot express "voice is none iff tone is neutral"; enforce it here.
    for lab in labels:
        if lab["tone"] == "neutral" and lab["voice"] != "none":
            lab["voice_raw"], lab["voice"] = lab["voice"], "none"
        elif lab["tone"] != "neutral" and lab["voice"] == "none":
            out["warning"] = "non-neutral tone with voice=none"
    out["labels"] = labels
    return out


def label_article(client: anthropic.Anthropic, item: dict[str, Any], arm: Arm) -> dict[str, Any]:
    out: dict[str, Any] = {"article_id": item["article_id"], "outlet": item["outlet"]}
    t0 = time.monotonic()
    try:
        resp = call(client, build_request(item, arm))
    except anthropic.APIStatusError as e:
        return {**out, "error": f"{e.status_code}: {e.message}"}
    except anthropic.APIConnectionError as e:
        return {**out, "error": f"connection: {e}"}
    out["latency_s"] = round(time.monotonic() - t0, 2)
    out["request_id"] = resp._request_id
    return parse_message(resp, item, out)


def run_arm(
    items: list[dict[str, Any]], arm: Arm, workers: int, client: anthropic.Anthropic
) -> list[dict[str, Any]]:
    first = label_article(client, items[0], arm)  # warm the prompt cache
    with ThreadPoolExecutor(max_workers=workers) as ex:
        rest = list(ex.map(lambda it: label_article(client, it, arm), items[1:]))
    return [first, *rest]


def cost(usage: dict[str, int], model: str, batch: bool = False) -> float:
    p_in, p_out = PRICES[model]
    c = (
        usage["input"] * p_in
        + usage["cache_write"] * p_in * CACHE_WRITE
        + usage["cache_read"] * p_in * CACHE_READ
        + usage["output"] * p_out
    ) / 1e6
    return c * (BATCH_FACTOR if batch else 1.0)


def total_usage(results: Iterable[dict[str, Any]]) -> dict[str, int]:
    res = list(results)
    return {
        k: sum(r.get("usage", {}).get(k, 0) for r in res)
        for k in ("input", "output", "cache_read", "cache_write")
    }


# ---------------------------------------------------------------- sampling & io


def sample_items(
    ds: Dataset, n_pairs: int, seed: int, exclude: set[int] | None = None
) -> list[dict[str, Any]]:
    """Round-robin over outlets (random article order within each) until n_pairs."""
    rng = np.random.default_rng(seed)
    exclude = exclude or set()
    cands = ds.candidates.set_index("candidate_id")
    pairs = ds.pairs.merge(
        ds.articles[["article_id", "title", "summary"]], on="article_id", how="left"
    )
    pairs = pairs[~pairs["article_id"].isin(exclude)]
    queues = {
        o: list(rng.permutation(pairs.loc[pairs["outlet"] == o, "article_id"].unique()))
        for o in ds.outlets
    }
    items: list[dict[str, Any]] = []
    total = 0
    while total < n_pairs and any(queues.values()):
        for o in ds.outlets:
            if not queues[o] or total >= n_pairs:
                continue
            aid = int(queues[o].pop())
            rows = pairs[pairs["article_id"] == aid]
            pols = [
                {"name": str(cands.loc[c, "display_name"]), "party": str(cands.loc[c, "party"])}
                for c in sorted(rows["candidate_id"].unique())
            ]
            first = rows.iloc[0]
            items.append(
                {
                    "article_id": aid,
                    "outlet": o,
                    "title": clean(first["title"]),
                    "summary": clean(first["summary"]),
                    "politicians": pols,
                }
            )
            total += len(pols)
    return items


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def label_map(results: list[dict[str, Any]]) -> dict[tuple[int, str], dict[str, Any]]:
    return {
        (r["article_id"], lab["politician"]): lab for r in results for lab in r.get("labels", [])
    }


def md_cell(text: str) -> str:
    return text.replace("|", "/").replace("\n", " ")


# ---------------------------------------------------------------- pilot


def pilot(n_pairs: int, workers: int) -> None:
    snap = latest_snapshot()
    ds = Dataset(snap)
    arm = DEFAULT_ARM
    items = sample_items(ds, n_pairs, PILOT_SEED)
    results = run_arm(items, arm, workers, anthropic.Anthropic(max_retries=4))
    _, cb_id = load_codebook(arm.codebook)
    out = snap / f"layer2_pilot_{cb_id}.jsonl"
    write_jsonl(out, ({**r, "title": it["title"]} for it, r in zip(items, results, strict=True)))
    by_id = {it["article_id"]: it for it in items}
    labels = [
        {**lab, "article_id": r["article_id"], "outlet": r["outlet"]}
        for r in results
        for lab in r.get("labels", [])
    ]
    tot = total_usage(results)
    spent = cost(tot, arm.model)
    lines = [
        "# Layer 2 pilot: tone labels on a sample",
        "",
        f"Arm `{arm.version}`, snapshot {ds.snapshot_at}. {len(items)} articles → "
        f"{len(labels)} labels. Pilot cost ≈ ${spent:.4f}; errors "
        f"{sum('error' in r for r in results)}.",
        "",
        "| # | Outlet | Headline | Politician | Tone | Voice | Frame | Salience | Evidence |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for i, lab in enumerate(labels, 1):
        lines.append(
            f"| {i} | {lab['outlet']} | {md_cell(by_id[lab['article_id']]['title'])} | "
            f"{lab['politician']} | {lab['tone']} | {lab['voice']} | {lab['frame']} | "
            f"{lab['salience']} | {md_cell(lab['evidence'])} |"
        )
    (REPORTS_DIR / "layer2-pilot.md").write_text("\n".join(lines) + "\n")
    print(f"pilot: {len(items)} articles, ${spent:.4f}, raw in {out}")


# ---------------------------------------------------------------- eval


def agreement(
    arm_labels: dict[tuple[int, str], dict[str, Any]],
    ref: dict[tuple[int, str], dict[str, Any]],
) -> dict[str, Any]:
    keys = [k for k in ref if k in arm_labels]
    a = [arm_labels[k] for k in keys]
    r = [ref[k] for k in keys]
    out: dict[str, Any] = {"n": len(keys)}
    for f in ("tone", "frame", "salience"):
        out[f] = float(np.mean([x[f] == y[f] for x, y in zip(a, r, strict=True)]))
    out["tone_kappa"] = float(cohen_kappa_score([x["tone"] for x in a], [y["tone"] for y in r]))
    # Voice only matters where both see an evaluation.
    both = [(x, y) for x, y in zip(a, r, strict=True) if x["tone"] != "neutral" != y["tone"]]
    out["voice_n"] = len(both)
    out["voice"] = (
        float(np.mean([x["voice"] == y["voice"] for x, y in both])) if both else float("nan")
    )
    # Polarity sign (neg / neutral-or-mixed / pos) is what layer 3 aggregates.
    sign = {"negative": -1, "neutral": 0, "mixed": 0, "positive": 1}
    out["opposite_sign"] = int(
        sum(sign[x["tone"]] * sign[y["tone"]] == -1 for x, y in zip(a, r, strict=True))
    )
    out["neutral_rate"] = float(np.mean([x["tone"] == "neutral" for x in a]))
    return out


def confusion(
    arm_labels: dict[tuple[int, str], dict[str, Any]],
    ref: dict[tuple[int, str], dict[str, Any]],
) -> str:
    keys = [k for k in ref if k in arm_labels]
    tab = pd.crosstab(
        pd.Categorical([ref[k]["tone"] for k in keys], TONES),
        pd.Categorical([arm_labels[k]["tone"] for k in keys], TONES),
        rownames=["reference"],
        colnames=["arm"],
        dropna=False,
    )
    head = "| reference ↓ / arm → | " + " | ".join(TONES) + " |"
    rows = [head, "|---|" + "---|" * len(TONES)]
    rows += ["| " + t + " | " + " | ".join(str(int(v)) for v in tab.loc[t]) + " |" for t in TONES]
    return "\n".join(rows)


def evaluate(
    sample: str, n_pairs: int, arm_names: list[str], ref_name: str, workers: int, force: bool
) -> None:
    snap = latest_snapshot()
    ds = Dataset(snap)
    eval_dir = snap / "layer2_eval" / sample
    if (eval_dir / "items.jsonl").exists():
        items = read_jsonl(eval_dir / "items.jsonl")  # a sample stays fixed once drawn
    else:
        # Disjoint from the pilot and from every other evaluation sample.
        used = {r["article_id"] for f in snap.glob("layer2_pilot_*.jsonl") for r in read_jsonl(f)}
        used |= {
            r["article_id"] for f in snap.glob("layer2_eval/*/items.jsonl") for r in read_jsonl(f)
        }
        items = sample_items(ds, n_pairs, SAMPLE_SEEDS[sample], exclude=used)
        write_jsonl(eval_dir / "items.jsonl", items)
    client = anthropic.Anthropic(max_retries=4)
    item_ids = {it["article_id"] for it in items}
    arms = [Arm.from_name(n) for n in arm_names]
    reference = Arm.from_name(ref_name)

    results: dict[str, list[dict[str, Any]]] = {}
    for arm in [*arms, reference]:
        path = eval_dir / f"{arm.name}__{arm.version.replace('+', '_')}.jsonl"
        cached = read_jsonl(path) if path.exists() and not force else None
        if cached and {r["article_id"] for r in cached} == item_ids:
            results[arm.name] = cached
            print(f"{arm.name}: reused {path.name}")
            continue
        t0 = time.monotonic()
        results[arm.name] = run_arm(items, arm, workers, client)
        write_jsonl(path, results[arm.name])
        print(
            f"{arm.name}: {len(items)} articles in {time.monotonic() - t0:.0f}s, "
            f"${cost(total_usage(results[arm.name]), arm.model):.3f}"
        )

    ref = label_map(results[reference.name])
    n_total_pairs = len(ds.pairs)
    by_id = {it["article_id"]: it for it in items}
    n_labels = len(ref)
    lines = [
        f"# Layer 2 evaluation ({sample} sample): Haiku arms vs a reference model",
        "",
        f"Snapshot {ds.snapshot_at}. Sample `{sample}`: {len(items)} articles / {n_labels} "
        "(article, politician) pairs, round-robin across outlets, **disjoint from the pilot "
        "and from every other evaluation sample**. Reference = "
        f"`{reference.model}` (effort {reference.effort}) with codebook "
        f"`{reference.codebook}`. Agreement with a stronger model is a proxy for accuracy, "
        "not ground truth: where they disagree, the disagreements table below is what to read.",
        "",
        "## Agreement with the reference",
        "",
        "| Arm | Tone | κ tone | Opposite sign | Voice (both non-neutral) | Frame | Salience "
        "| Neutral rate | Errors | Cost (sample) | Full run, batch |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for arm in [*arms, reference]:
        res = results[arm.name]
        usage = total_usage(res)
        spent = cost(usage, arm.model)
        per_pair = spent / max(n_labels, 1)
        ag = agreement(label_map(res), ref)
        is_ref = arm is reference
        lines.append(
            f"| `{arm.name}` ({load_codebook(arm.codebook)[1]}) | "
            + (
                "reference | | | | | | "
                if is_ref
                else f"{ag['tone']:.0%} | {ag['tone_kappa']:.2f} | {ag['opposite_sign']} | "
                f"{ag['voice']:.0%} (n={ag['voice_n']}) | {ag['frame']:.0%} | "
                f"{ag['salience']:.0%} | "
            )
            + f"{ag['neutral_rate']:.0%} | {sum('error' in r for r in res)} | ${spent:.3f} | "
            f"${per_pair * n_total_pairs * BATCH_FACTOR:.2f} |"
        )
    lines += [
        "",
        "*Opposite sign* = pairs where one says positive and the other negative: the errors "
        "that would flip a slant estimate. Full-run costs extrapolate the measured per-pair "
        f"cost to all {n_total_pairs:,} pairs at Batch API prices.",
        "",
    ]
    main = arms[-1].name  # the arm under study goes last on the command line
    main_labels = label_map(results[main])
    lines += [f"## Tone confusion: `{main}` vs reference", "", confusion(main_labels, ref), ""]
    dis = [k for k in ref if k in main_labels and main_labels[k]["tone"] != ref[k]["tone"]]
    lines += [
        f"## Tone disagreements: `{main}` vs reference ({len(dis)})",
        "",
        "| Outlet | Headline | Politician | Haiku | Reference | Haiku evidence | Reference evidence |",
        "|---|---|---|---|---|---|---|",
    ]
    for k in dis:
        it, h, r = by_id[k[0]], main_labels[k], ref[k]
        lines.append(
            f"| {it['outlet']} | {md_cell(it['title'])} | {k[1]} | {h['tone']} / {h['voice']} | "
            f"{r['tone']} / {r['voice']} | {md_cell(h['evidence'])} | {md_cell(r['evidence'])} |"
        )
    problems = [
        (name, r) for name, res in results.items() for r in res if "error" in r or "warning" in r
    ]
    if problems:
        lines += ["", "## Problems", ""]
        lines += [
            f"- {name} / article {r['article_id']}: {r.get('error') or r.get('warning')}"
            for name, r in problems
        ]
    out = REPORTS_DIR / f"layer2-eval-{sample}.md"
    out.write_text("\n".join(lines) + "\n")
    print(f"report: {out}")


# ---------------------------------------------------------------- full run (Batch API)

FULL_ARM = Arm.from_name(f"haiku-{CURRENT_CODEBOOK}-medium")


def full_dir(snap: Path) -> Path:
    return snap / "layer2_full" / FULL_ARM.version.replace("+", "_")


def full_submit(max_cost: float) -> None:
    from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
    from anthropic.types.messages.batch_create_params import Request

    snap = latest_snapshot()
    ds = Dataset(snap)
    run_dir = full_dir(snap)
    if (run_dir / "batch.json").exists():
        raise SystemExit(f"already submitted: {run_dir / 'batch.json'} (use `full collect`)")
    items = sample_items(ds, 10**9, PILOT_SEED)  # every article with a mention
    # Cost guard: per-article cost measured on the held-out test sample, at batch price.
    test_runs = list((snap / "layer2_eval" / "test").glob(f"{FULL_ARM.name}__*.jsonl"))
    if not test_runs:
        raise SystemExit(f"no test-sample run for {FULL_ARM.name}: run `eval --sample test` first")
    measured = read_jsonl(test_runs[0])
    per_article = cost(total_usage(measured), FULL_ARM.model) / len(measured)
    estimate = per_article * len(items) * BATCH_FACTOR
    print(
        f"{len(items)} articles, {sum(len(i['politicians']) for i in items)} pairs, "
        f"arm {FULL_ARM.version}, estimated ${estimate:.2f} (cap ${max_cost:.2f})"
    )
    if estimate > max_cost:
        raise SystemExit("estimate above --max-cost, not submitting")
    requests = [
        Request(
            custom_id=f"a{it['article_id']}",
            params=MessageCreateParamsNonStreaming(**build_request(it, FULL_ARM)),  # type: ignore[typeddict-item]
        )
        for it in items
    ]
    batch = anthropic.Anthropic(max_retries=4).messages.batches.create(requests=requests)
    write_jsonl(run_dir / "items.jsonl", items)
    (run_dir / "batch.json").write_text(
        json.dumps(
            {
                "batch_id": batch.id,
                "created_at": str(batch.created_at),
                "arm": FULL_ARM.version,
                "n_requests": len(requests),
                "estimate_usd": round(estimate, 4),
            },
            indent=1,
        )
    )
    print(f"submitted batch {batch.id}: {batch.processing_status}")


def full_collect(wait: bool) -> None:
    snap = latest_snapshot()
    ds = Dataset(snap)
    run_dir = full_dir(snap)
    meta = json.loads((run_dir / "batch.json").read_text())
    client = anthropic.Anthropic(max_retries=4)
    while True:
        b = client.messages.batches.retrieve(meta["batch_id"])
        c = b.request_counts
        print(
            f"{time.strftime('%H:%M:%S')} {b.processing_status}: processing {c.processing}, "
            f"succeeded {c.succeeded}, errored {c.errored}, expired {c.expired}",
            flush=True,
        )
        if b.processing_status == "ended":
            break
        if not wait:
            return
        time.sleep(60)
    items = {f"a{it['article_id']}": it for it in read_jsonl(run_dir / "items.jsonl")}
    results = []
    for res in client.messages.batches.results(meta["batch_id"]):
        it = items[res.custom_id]
        out: dict[str, Any] = {"article_id": it["article_id"], "outlet": it["outlet"]}
        if res.result.type == "succeeded":
            results.append(parse_message(res.result.message, it, out))
        else:
            results.append({**out, "error": f"batch result {res.result.type}"})
    write_jsonl(run_dir / "results.jsonl", results)
    name_to_id = dict(
        zip(ds.candidates["display_name"], ds.candidates["candidate_id"], strict=True)
    )
    rows = [
        {
            "article_id": r["article_id"],
            "outlet": r["outlet"],
            "candidate_id": int(name_to_id[lab["politician"]]),
            "politician": lab["politician"],
            **{k: lab[k] for k in ("tone", "voice", "frame", "salience", "evidence")},
            "version": FULL_ARM.version,
        }
        for r in results
        for lab in r.get("labels", [])
    ]
    pd.DataFrame(rows).to_csv(run_dir / "labels.csv", index=False)
    spent = cost(total_usage(results), FULL_ARM.model, batch=True)
    n_err = sum("error" in r for r in results)
    n_warn = sum("warning" in r for r in results)
    meta.update({"collected_usd": round(spent, 4), "n_labels": len(rows), "n_errors": n_err})
    (run_dir / "batch.json").write_text(json.dumps(meta, indent=1))
    print(
        f"{len(rows)} labels from {len(results)} articles; errors {n_err}, warnings {n_warn}; "
        f"cost ${spent:.3f} (estimate ${meta['estimate_usd']:.2f}) -> {run_dir / 'labels.csv'}"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pilot", help="label a small stratified sample, print every label")
    p.add_argument("--n-pairs", type=int, default=50)
    p.add_argument("--workers", type=int, default=4)
    e = sub.add_parser("eval", help="compare Haiku arms against a reference model")
    e.add_argument("--sample", choices=sorted(SAMPLE_SEEDS), default="dev")
    e.add_argument("--n-pairs", type=int, default=200)
    e.add_argument("--arms", default="haiku-v4-low,haiku-v4-medium", help="comma-separated")
    e.add_argument("--reference", default="opus-v4-medium")
    e.add_argument("--workers", type=int, default=6)
    e.add_argument("--force", action="store_true", help="re-run arms even if cached")
    f = sub.add_parser("full", help="label every article via the Batch API")
    f.add_argument("action", choices=["submit", "collect"])
    f.add_argument("--max-cost", type=float, default=2.0, help="USD cap on the estimate")
    f.add_argument("--wait", action="store_true", help="collect: poll until the batch ends")
    args = ap.parse_args()
    if args.cmd == "pilot":
        pilot(args.n_pairs, args.workers)
    elif args.cmd == "full":
        full_submit(args.max_cost) if args.action == "submit" else full_collect(args.wait)
    else:
        evaluate(
            args.sample,
            args.n_pairs,
            args.arms.split(","),
            args.reference,
            args.workers,
            args.force,
        )


if __name__ == "__main__":
    main()
