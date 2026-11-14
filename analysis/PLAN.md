# Media orientation analysis: plan

Goal: describe, per outlet, **who gets covered** (visibility) and **how
they are presented** (tone), and estimate each outlet's slant, i.e.
coverage or tone that differs from what the rest of the press did over
the same period. Applied sequentially; each layer has its own script,
report (`reports/*.md`) and static interactive page (`reports/*.html`,
plain JS + ECharts from a CDN, no build, no backend).

Started 2026-11-14 on the merged local dataset (28.9k articles,
2026-05-15 → 2026-11-14, 15 feeds / 14 outlets, 14 tracked politicians).

## Data constraints (shape every choice below)

- Text = headline + summary (~170–430 chars). Le Parisien ships no
  summary (headline only); L'Express ships full bodies, which we **do
  not use**, to keep every outlet on the same footing (title + summary).
- Feeds are not like-for-like samples: section feeds (`politique`) vs
  front-page feeds (Marianne `une`, Mediapart). Candidate-mention rates
  range 9% → 56%. Everything is normalised **within outlet**.
- BFM TV = 48% of the corpus. Baselines are **equal-weighted across
  outlets** so one outlet does not define "normal".
- Mentions come from the keyword extractor (`keyword v1`): exact or whole-word
  aliases only. Indirect references ("le leader insoumis", "le chef de
  l'État") are missed, so recall is uneven across candidates.
- Macron (sitting president, cannot run) is tracked but reported apart
  from the candidate blocs. Marine Le Pen was flagged ineligible when the
  pipeline was set up; she is treated as a candidate from 2026-11-14.
- Unit of analysis: a distinct **(article, politician) pair**; several
  matches of the same name in one article count once.
- France Info's two feeds (politique, élections) are merged into one
  outlet; they share no URLs.
- Scope: `published_at` from 2026-05-15 (429 older back-catalogue items in
  the first fetches are excluded).

## Layer 1: coverage (deterministic) ✅ done 2026-11-14

Script: `analysis/layer1_coverage.py` → `reports/layer1-coverage.{md,html}`.

| Measure | Definition |
|---|---|
| Share of voice | outlet's pairs for politician *c* / outlet's pairs |
| Coverage lift | share / equal-weight mean share across outlets (1.0 = average) |
| Bloc lift | same, candidates grouped by political lean (eligible candidates only) |
| Coverage position | mean lean position (hard-left −3 … hard-right +3) of an outlet's candidate pairs, minus the cross-outlet mean. *Where its attention sits*, **not** a measure of sympathy |
| Prominence | % of pairs where the name is in the headline (vs summary only) |
| Concentration | effective number of candidates = 1 / Σ share² |
| Co-mentions | candidate pairs in the same article, observed/expected lift |
| Outlet similarity | Jensen–Shannon distance between candidate-share vectors |
| Weekly share | per politician, per outlet vs equal-weight all-outlet mean |

Uncertainty: bootstrap over articles within each outlet (400 resamples,
90% interval). A cell counts as notable when its interval excludes 1.0
(or 0 for the position). Robustness: lifts recomputed on headline-only
mentions (removes the summary-length difference between outlets).

## Layer 2: tone toward each politician (LLM classifier)

One label per (article, politician) pair on title + summary, about 15k pairs.

Codebook (French news, written into the prompt):
- `tone`: how the text presents *this* politician: `positive` /
  `neutral` / `negative` (+ `mixed`).
- `voice`: who carries the evaluation: `outlet` (editorial framing,
  word choice, what the headline foregrounds), `quoted` (a third party
  quoted or reported), `self` (the politician speaking or acting, e.g.
  attacking someone, which isn't negative *about* them).
- `frame`: `horse_race` (polls, rankings), `programme` (policy),
  `scandal_justice`, `strategy_alliances`, `campaign_event`, `personal`,
  `other`.
- `evidence`: the short span that motivates the label.

Model: `claude-haiku-5-5` (decided 2026-11-14), low effort, structured
JSON output, Batch API, prompt caching on the codebook. Stored as
versioned annotations (`extractor = "llm-tone"`, `extractor_version`
= model + prompt hash), so they can be re-run and compared.
Exact cost to be computed from current pricing on a dry-run sample
before the full run.

Validation **without hand labels** (decided 2026-11-14: no hand-labelling for
now):
1. *Self-consistency*: a 10% sample re-labelled with a reworded prompt;
   report agreement (Cohen's κ). Low-κ categories are reported as fragile.
2. *Audit by a stronger model*: ~300 stratified pairs re-labelled by a
   larger Claude model; agreement with Haiku reported as a proxy accuracy.
3. *Face validity*: per-outlet results must reproduce well-known
   positions (e.g. L'Humanité vs Le Figaro); if not, the method is
   wrong, not the press.
4. A review queue (disagreements + random sample) exported for future
   hand labelling, so the gold set can be added later without rework.

## Layer 3: slant estimation

- **Presentation slant**: model `negative/positive` with
  politician × week fixed effects (what everyone said that week) plus
  outlet × politician (or outlet × bloc) effects; the latter are the
  slant estimates, with intervals. Restricted to `voice = outlet` for the
  "editorial" variant, all voices for the "what readers see" variant.
- **Selection slant**: layer-1 lifts, plus *story selection*: share of an
  outlet's coverage of X that is `scandal_justice` vs the press average.
- **Same-story comparison**: cluster articles about the same event (same
  day ± 1, similar text) and contrast how each outlet framed it.
- Outlet map: x = presentation slant (left ↔ right blocs), y = coverage
  position, size = volume, colour = declared lean.

## Layer 4: dashboard integration (later)

Port the stable views (heatmaps, outlet map, tone timeline, same-story
view with click-through to headlines) into the React dashboard behind
new API endpoints.

## Decisions log

- 2026-11-14: `analysis/` subdir; Markdown report + static HTML per
  layer; layer 1 first; Haiku for layer 2 with low effort; no hand
  labels for now (validation via self-consistency + stronger-model
  audit); API key in `.env` (`ANTHROPIC_API_KEY`, gitignored).
- 2026-11-14: Marine Le Pen treated as an eligible candidate (seed
  `eligible: true`); she now counts in the hard-right bloc, the coverage
  position and the concentration measures.
- 2026-11-14: diverging colour pair is blue ↔ orange, not blue ↔ red:
  in French politics red/blue read as left/right, which would make the
  over/under-coverage map look like a political verdict.

## How to run

Analysis code runs in the shared data-science venv `/opt/venvs/pyDS`
(numpy, pandas, scipy, anthropic). It has no Postgres driver, so inputs
are read through `psql` in the docker container and frozen as a dated
CSV snapshot in `analysis/data/<date>/` (gitignored).

```bash
make analysis-coverage                           # fresh snapshot + layer 1 report
/opt/venvs/pyDS/bin/python -m analysis.layer1_coverage   # re-render from the latest snapshot
xdg-open analysis/reports/layer1-coverage.html   # needs internet for the ECharts CDN
```

Hand-written findings live in `analysis/findings/layer<N>.md` and are
inlined into both report formats on each render.
