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

## Layer 2: tone toward each politician (LLM classifier) ✅ done 2026-11-14

Script: `analysis/layer2_tone.py` (`pilot` subcommand for now). One request per
article (headline + summary, HTML stripped) listing the politicians the
keyword extractor found; one label per politician. **The outlet name is not
sent**, so the model cannot lean on priors about an outlet's politics.

Codebook (verbatim in the script and in `reports/layer2-pilot.md`):
- `tone`: `positive` / `neutral` / `negative` / `mixed`: how the text
  presents *this* politician. Attacking someone is not negative for the
  attacker; being targeted is negative only if the text presents the
  accusation as credible (a debunked or "fallacieux" attack reads as
  sympathetic).
- `voice`: who carries the evaluation: `editorial` (the outlet's own wording),
  `event` (a fact good or bad for them: poll, ruling, defection, being booed;
  poll verbs like "progresse" or "s'impose" count here), `quoted` (a third
  party), `self` (their own words or acts), `none` (iff tone is neutral,
  enforced in code). Splitting the old `outlet` value into
  `editorial`/`event` lets layer 3 separate slant in wording from slant in
  which facts get reported.
- `frame`: `horse_race`, `programme`, `scandal_justice`,
  `strategy_alliances`, `campaign_event`, `governing`, `personal`, `other`.
- `salience`: `main` / `secondary` / `incidental`, so passing mentions can
  be down-weighted or filtered.
- `evidence`: shortest verbatim French span supporting the tone.

Model `claude-haiku-5-5`, effort `low` (adaptive thinking on), strict JSON
schema via `output_config.format` (politician field restricted to the
names sent), codebook prompt-cached. Version id = SHA-256 prefix of the
codebook.

### Pilot (2026-11-14, 42 articles / 50 pairs, round-robin over outlets)

- Run health: 0 errors, 0 refusals, 0 label-set mismatches, ~2.4 s median
  latency per article.
- Measured cost: $0.008 for 50 pairs → **≈ $2.1 for all 12.4k pairs live,
  ≈ $1.0 with the Batch API** (list prices).
- Codebook v1 (`8db2221e`) → v2 (`f0ecf375`) after reading all 50 labels:
  v1 read victim framing as negative (LFI "victime" of disinformation, a
  "bouc-émissaire" story, a "fallacieux" audio, a fact-check clearing
  Bardella), read poll verbs as editorial, and could not tell passing
  mentions from subjects. v2 fixes all of these.
- Self-consistency, v2 vs a v2 re-run on the same items: tone 47/50
  (κ = 0.90), voice 48/50, frame 48/50, salience 46/50. The three tone flips are
  genuinely ambiguous headlines.
- Known open issue: v2 is more cautious (26 neutral vs 21) and now reads
  Mediapart's "école libérale et parfois réactionnaire" as neutral for
  Attal and Retailleau. Candidate v3 rule: evaluative descriptors in the
  outlet's own voice ("réactionnaire", "démagogue") count as editorial;
  standard classifications ("extrême droite", "gauche radicale") stay
  descriptive. Without that distinction, outlets that use the standard label
  would look biased.

### Evaluation against a reference model (2026-11-14, dev sample)

Fresh 200-pair sample (159 articles), disjoint from the pilot; reference =
`claude-opus-5-5` (effort medium) with the same codebook. Agreement is a
proxy for accuracy, not ground truth (`reports/layer2-eval-dev.md` lists
every disagreement).

| Haiku arm | Tone | κ | Opposite sign | Full run (batch) |
|---|---|---|---|---|
| v2 low | 84% | 0.75 | 1 | $0.78 |
| v3 low | 84% | 0.73 | 1 | $0.86 |
| v3 medium | 88% | 0.80 | 0 | $1.11 |
| v4 low | 84% | 0.74 | 1 | $0.90 |
| v4 medium | 90% | 0.83 | 0 | $1.14 |

- Effort matters more than codebook wording: medium beats low by 4–6
  points under every codebook, for ~+$0.25 on the full run.
- Haiku-low's disagreements were mostly one-sided: understated editorial
  negatives read as neutral ("un rendez-vous sans résultat", "toujours
  « challenger »"), plainly reported good news read as neutral ("en
  position de se qualifier", "réélu"), and question headlines attributed to
  the wrong person. Codebook v4 (`d18c3c3b`) addresses these; its dev
  numbers are in-sample (v4 was written from these disagreements), so they
  need confirming on a held-out `test` sample.

### Held-out test (2026-11-14, 100 pairs / 71 articles, `reports/layer2-eval-test.md`)

Reference `opus-v4-medium`, sample disjoint from the pilot and dev sets.

| Haiku arm | Tone | κ | Opposite sign | Voice (both non-neutral) |
|---|---|---|---|---|
| v4 low | 83% | 0.73 | 2 | 78% |
| **v4 medium (chosen)** | **90%** | **0.84** | 2 | 76% |

The dev result holds out of sample (90% / κ 0.84). Known limitations of the
chosen arm, kept as-is rather than edited after validation:
- Misleading headlines whose summary reverses them: Le Point's "les
  chouchous de Moscou" (the summary says Russian disinformation *targets*
  Glucksmann and Attal) was read as negative; this produced both
  opposite-sign errors.
- "en embuscade", which v4 lists as an implicit signal, tends to be read as
  negative; the reference treats it as neutral or positive (a contender in
  waiting). Drop it from the list in any v5.
- Voice agreement is the weakest field (76–85%); slant estimates split by
  voice will be noisier than those on tone alone.

Decision (2026-11-14): full run with codebook v4 + **medium** effort (the user
had first asked for low; medium measured 4–6 points better for ~+$0.25).

### Spend ledger (list prices, from logged usage)

- 2026-11-14: pilots + dev evaluation = $1.21 (Opus reference $1.01,
  921 Haiku requests $0.17, smoke tests ~$0.02).
- 2026-11-14: held-out test = $0.66 (Opus reference $0.63).
- 2026-11-14: full run, batch `msgbatch_01UCbaMfYJV5J7uoBnbBroT2`: 9,590
  requests, 12,449 labels, 0 errors, **$1.12** (estimate $1.16), ~70 min.
- **Layer 2 total ≈ $3.00** (experiments $1.88, full run $1.12).

### Next steps

1. ~~Codebook v3, re-pilot on a fresh sample~~ done (dev evaluation above);
   v4 confirmed on the held-out `test` sample (above).
2. Audit: ~300 stratified pairs re-labelled by a larger Claude model;
   report agreement per field and inspect the disagreements.
3. Full run via the Batch API: `python -m analysis.layer2_tone full submit`
   then `full collect --wait`; labels land in
   `analysis/data/<snapshot>/layer2_full/<arm version>/labels.csv`. Moving them
   into Postgres (a `mention_tone` table keyed by article, candidate and
   version) is still to decide.
4. Review queue export (disagreements + random sample) for future hand
   labels.

### Tone report (`analysis/layer2_report.py` → `reports/layer2-tone.{md,html}`)

Scaffold built 2026-11-14 while the batch ran, checked on the dev+test labels
(`--sample`; `--min-cell 3` only to exercise every chart). Measures:
- net tone = (positive − negative) / labels; incidental mentions excluded;
- relative tone per outlet × bloc and outlet × politician = outlet net tone
  minus the equal-weight press average (cells need ≥ 10 labels), 90%
  bootstrap over articles; every view in two scopes: *all voices* and
  *outlet's own wording only* (voice = editorial);
- tone slant per outlet = relative tone toward right-bloc minus left-bloc
  candidates (eligible, centre excluded), plotted against layer-1 coverage
  position (the "outlet map");
- who carries the tone (voice mix of negative/positive labels), story mix
  (frames), monthly tone per politician, clickable example headlines per
  cell, validation figures read from the saved eval runs.

`make analysis-tone` collects the batch (if done) and renders the report.

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
- 2026-11-14: layer 2 voice split into editorial/event (+ quoted/self/none),
  salience field added, outlet name withheld from the model.
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
