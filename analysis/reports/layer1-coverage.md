# Layer 1: who gets covered, by whom

Snapshot 2026-11-14T13:55:51+00:00 · articles published 2026-05-15 → 2026-11-14 · 27,713 articles · 9,590 mention a tracked politician · 12,449 (article, politician) pairs · 14 outlets.

Interactive version: [`layer1-coverage.html`](./layer1-coverage.html). Method: [`../PLAN.md`](../PLAN.md).

## Key findings

- **Where an outlet's attention sits says nothing about its declared lean** (Spearman −0.18 across the 11 outlets with a lean on the left–right axis, i.e. no relationship). The outlets most tilted toward left-bloc candidates are Le Parisien (−0.54, largely because it barely covers Marine Le Pen) and Marianne (−0.40); the most tilted to the right are Mediapart (+0.82), RFI (+0.40) and France Info (+0.32). Coverage measures attention, not sympathy, which is exactly why layer 2 (tone) is needed.
- **Over-coverage follows two patterns.** *Own family*: Le Figaro → LR (Wauquiez 3.15×, Retailleau 2.13×), L'Obs → Glucksmann 1.61×, L'Humanité and Marianne → Ruffin 2.64× and 2.38×. *Watching the other side*: Mediapart → Darmanin 2.42×, Bardella 1.80×, Le Pen 1.65×; Libération → Wauquiez 2.26×, Zemmour 1.63×; Le Point → Zemmour 2.22×. Which of these is criticism and which is promotion is a layer-2 question; these are hypotheses for now.
- **Mélenchon gets less attention than average from L'Humanité (0.66×) and Mediapart (0.69×)**, average attention from Libération (0.97×), and more from L'Obs (1.26×), Marianne (1.28×), Le Point (1.33×) and L'Express (1.38×).
- **Marine Le Pen splits outlets** more than any other figure: 1.5–2.0× at France Info, RFI, Mediapart and L'Express, but 0.35× at 20 Minutes and 0.13× at Le Parisien (14 headlines in six months). As one of the two largest names in the hard-right bloc, she alone moves several outlets' coverage position.
- **BFM TV spreads its attention most evenly** (effective 9.8 of 13 candidates) and is the outlet that most over-covers the smaller left leaders (Tondelier 1.78×, Faure 1.60×). L'Express (6.1) and Mediapart (6.7) concentrate on a few names.
- **Co-mentions trace the coalition questions**: Philippe + Wauquiez 3.8× what independence predicts, Glucksmann + Faure 3.2×, Philippe + Attal 2.5× (the race for the centre); Bardella + Le Pen is the most frequent pair (365 articles).
- **The patterns are robust to text length**: lifts recomputed on headlines only correlate at 0.92 with the main lifts, so the outlets without summaries (Le Parisien, L'Express) are not distorting the picture.

## How to read

- **Lift** = an outlet's share of its political coverage going to X, divided by the average share across outlets (each outlet weighted equally). 1.00 = typical; 2.00 = twice the typical attention. **Bold** = the 90% bootstrap interval excludes 1.00. (Parentheses) = fewer than 5 pairs expected at baseline: too thin to assess.
- Coverage measures **attention, not sympathy**: an outlet can cover someone a lot because it investigates them. Tone comes in layer 2.
- † = tracked but not a candidate (Macron: cannot run); excluded from blocs, position and concentration.

## Corpus by outlet

| Outlet | Declared lean | Articles | Mention a politician | Rate | Pairs |
|---|---|---|---|---|---|
| L'Humanité | hard-left | 1,282 | 271 | 21% | 335 |
| Le Nouvel Obs | left | 883 | 346 | 39% | 443 |
| Libération | left | 2,062 | 832 | 40% | 1,053 |
| Mediapart | left | 2,352 | 213 | 9% | 255 |
| Le Monde | centre-left | 3,055 | 800 | 26% | 1,077 |
| 20 Minutes | centre | 1,089 | 414 | 38% | 551 |
| L'Express ‡ | centre | 313 | 144 | 46% | 179 |
| Le Parisien ‡ | centre | 2,605 | 830 | 32% | 946 |
| France Info | public | 3,180 | 1,245 | 39% | 1,580 |
| RFI | public | 435 | 155 | 36% | 219 |
| BFM TV | centre-right | 7,432 | 3,510 | 47% | 4,734 |
| Le Figaro | centre-right | 542 | 263 | 49% | 344 |
| Le Point | centre-right | 561 | 276 | 49% | 361 |
| Marianne | sovereigntist | 1,922 | 291 | 15% | 372 |

‡ no summaries in the feed (headline only), so fewer mentions are detectable.

## Coverage position (where each outlet's attention sits, left ↔ right)

Mean lean of the candidates an outlet covers (hard-left −3 … hard-right +3), minus the average outlet. Negative = attention tilted toward left-bloc candidates.

| Outlet | Declared lean | Position | 90% interval |
|---|---|---|---|
| Le Parisien | centre | -0.54 | [-0.66, -0.42] |
| Marianne | sovereigntist | -0.40 | [-0.62, -0.19] |
| 20 Minutes | centre | -0.35 | [-0.51, -0.21] |
| Le Nouvel Obs | left | -0.33 | [-0.52, -0.13] |
| Le Point | centre-right | -0.23 | [-0.45, -0.03] |
| Libération | left | -0.12 | [-0.24, -0.00] |
| Le Monde | centre-left | -0.11 | [-0.23, -0.00] |
| BFM TV | centre-right | +0.07 | [+0.02, +0.13] |
| Le Figaro | centre-right | +0.10 | [-0.12, +0.35] |
| L'Humanité | hard-left | +0.15 | [-0.09, +0.38] |
| L'Express | centre | +0.23 | [-0.09, +0.53] |
| France Info | public | +0.32 | [+0.21, +0.42] |
| RFI | public | +0.40 | [+0.10, +0.71] |
| Mediapart | left | +0.82 | [+0.58, +1.05] |

## Bloc lift (eligible candidates grouped by lean)

| Outlet | hard-left | left | centre-left | centre | centre-right | right | hard-right |
|---|---|---|---|---|---|---|---|
| L'Humanité | **0.68** | **1.94** | 0.98 | **0.74** | 1.08 | 0.81 | **1.15** |
| Le Nouvel Obs | **1.24** | 0.74 | **1.47** | 0.80 | 0.82 | **0.60** | 0.94 |
| Libération | 0.95 | **1.39** | 1.09 | 1.12 | **0.83** | **1.29** | **0.87** |
| Mediapart | **0.74** | 0.70 | **0.50** | **0.67** | 1.18 | **0.66** | **1.64** |
| Le Monde | 0.97 | 1.01 | 1.01 | 1.09 | **1.21** | 1.02 | **0.85** |
| 20 Minutes | 1.03 | 0.98 | **1.32** | 1.21 | 1.10 | 0.95 | **0.69** |
| L'Express | 1.26 | **0.37** | 0.78 | **0.69** | 0.86 | **0.58** | **1.40** |
| Le Parisien | **1.20** | 1.28 | **1.18** | **1.19** | 1.04 | 1.01 | **0.61** |
| France Info | **0.79** | 1.05 | 0.92 | 1.04 | 1.02 | **0.67** | **1.26** |
| RFI | 0.83 | **0.35** | 0.91 | 1.16 | 1.11 | 0.91 | 1.19 |
| BFM TV | **0.70** | **1.59** | 0.99 | **1.17** | **1.12** | **1.09** | **0.93** |
| Le Figaro | 1.06 | 0.66 | **0.70** | 0.99 | 0.94 | **2.19** | **0.84** |
| Le Point | **1.27** | **0.57** | 1.12 | 1.04 | 0.94 | **1.40** | **0.74** |
| Marianne | **1.28** | 1.36 | 1.05 | 1.11 | **0.74** | 0.81 | 0.88 |

Baseline share per bloc (equal-weight mean of outlets): hard-left 18%, left 5%, centre-left 15%, centre 10%, centre-right 16%, right 9%, hard-right 27%.

## Politician lift

| Outlet | Jean-Luc Mélenchon | François Ruffin | Marine Tondelier | Olivier Faure | Raphaël Glucksmann | Gabriel Attal | Gérald Darmanin | Édouard Philippe | Bruno Retailleau | Laurent Wauquiez | Jordan Bardella | Marine Le Pen | Éric Zemmour | Emmanuel Macron† |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L'Humanité | **0.66** | (2.64) | 1.42 | 1.40 | 0.91 | **0.71** | **1.92** | **0.66** | 0.84 | (0.32) | **1.39** | **0.79** | 1.03 | 1.16 |
| Le Nouvel Obs | **1.26** | 1.08 | **0.58** | 1.28 | **1.61** | 0.82 | 0.93 | **0.78** | **0.63** | (0.24) | 0.97 | 0.97 | 0.78 | 0.87 |
| Libération | 0.97 | **1.74** | 1.32 | 1.24 | 1.10 | **1.16** | **0.49** | 1.00 | **1.27** | **2.26** | 0.95 | **0.70** | **1.63** | **0.83** |
| Mediapart | **0.69** | (0.53) | 0.72 | **0.52** | **0.46** | **0.64** | **2.42** | **0.52** | **0.49** | (1.27) | **1.80** | **1.65** | (1.12) | 1.05 |
| Le Monde | **0.87** | 0.70 | 1.12 | **1.49** | **0.86** | 0.99 | 0.98 | **1.17** | 0.90 | 1.01 | **0.64** | **0.87** | 0.85 | **1.44** |
| 20 Minutes | 1.09 | 0.99 | 1.06 | 1.21 | **1.37** | **1.29** | 0.75 | **1.39** | 1.05 | 0.98 | 0.96 | **0.35** | 0.94 | **0.81** |
| L'Express | **1.38** | (0.38) | (0.41) | **0.19** | 0.93 | 0.77 | 0.57 | 1.12 | 0.70 | (0.00) | 1.28 | **2.01** | (0.00) | **0.53** |
| Le Parisien | **1.21** | 0.79 | **1.54** | 1.06 | 1.09 | **1.20** | 1.03 | 1.02 | 1.05 | 0.57 | **0.88** | **0.13** | 1.21 | **1.24** |
| France Info | **0.76** | 0.86 | 1.13 | 1.06 | **0.82** | 1.00 | 0.94 | 0.98 | **0.65** | 0.69 | 1.08 | **1.53** | **0.69** | **1.09** |
| RFI | **0.78** | (0.00) | 0.50 | 1.07 | 0.89 | 1.08 | 1.06 | 1.06 | 0.93 | (0.00) | 1.01 | **1.64** | (0.52) | 1.01 |
| BFM TV | **0.70** | **1.34** | **1.78** | **1.60** | **0.84** | **1.18** | 0.92 | **1.23** | 1.06 | 1.12 | **0.83** | **1.11** | **0.76** | **0.93** |
| Le Figaro | 1.01 | **0.20** | 0.85 | 0.68 | **0.71** | 0.94 | 0.75 | 1.06 | **2.13** | (3.15) | 0.90 | **0.56** | 1.00 | 1.20 |
| Le Point | **1.33** | **0.38** | 0.71 | 1.02 | 1.22 | 1.11 | **0.50** | 1.20 | **1.51** | (1.50) | **0.71** | **0.73** | **2.22** | **0.65** |
| Marianne | **1.28** | **2.38** | 0.88 | **0.18** | 1.19 | 1.11 | 0.76 | 0.81 | 0.80 | (0.87) | **0.62** | 0.94 | 1.23 | 1.18 |

Baseline share of voice: Jean-Luc Mélenchon 14.1%, François Ruffin 1.5%, Marine Tondelier 2.7%, Olivier Faure 3.0%, Raphaël Glucksmann 10.2%, Gabriel Attal 8.0%, Gérald Darmanin 3.9%, Édouard Philippe 9.0%, Bruno Retailleau 6.4%, Laurent Wauquiez 0.9%, Jordan Bardella 11.3%, Marine Le Pen 11.4%, Éric Zemmour 1.7%, Emmanuel Macron† 15.7%.

Robustness: recomputing lifts on headline-only mentions gives a Spearman correlation of 0.92 with the main lifts across all outlet × politician cells.

## Prominence and concentration

| Outlet | Name in headline | Effective nb of candidates | Top-3 share |
|---|---|---|---|
| L'Humanité | 67% | 9.5 | 42% |
| Le Nouvel Obs | 69% | 7.6 | 53% |
| Libération | 73% | 9.7 | 41% |
| Mediapart | 47% | 6.7 | 59% |
| Le Monde | 64% | 9.4 | 43% |
| 20 Minutes | 78% | 8.4 | 48% |
| L'Express | 99% ‡ | 6.1 | 62% |
| Le Parisien | 100% ‡ | 8.2 | 47% |
| France Info | 71% | 8.2 | 49% |
| RFI | 47% | 7.7 | 49% |
| BFM TV | 75% | 9.8 | 39% |
| Le Figaro | 71% | 8.6 | 47% |
| Le Point | 60% | 8.3 | 47% |
| Marianne | 69% | 8.0 | 50% |

Effective number of candidates = 1 / Σ share² over eligible candidates (13 = perfectly even attention; lower = attention concentrated on a few).

## Most frequent co-mentions (all outlets)

| Pair | Articles | Observed / expected |
|---|---|---|
| Jordan Bardella + Marine Le Pen | 365 | 2.0× |
| Édouard Philippe + Gabriel Attal | 349 | 2.5× |
| Édouard Philippe + Bruno Retailleau | 194 | 1.9× |
| Bruno Retailleau + Gabriel Attal | 190 | 2.1× |
| Raphaël Glucksmann + Olivier Faure | 190 | 3.2× |
| Jean-Luc Mélenchon + Édouard Philippe | 188 | 1.0× |
| Jean-Luc Mélenchon + Raphaël Glucksmann | 176 | 0.9× |
| Jean-Luc Mélenchon + Marine Le Pen | 148 | 0.7× |
| Jean-Luc Mélenchon + Gabriel Attal | 123 | 0.7× |
| Marine Le Pen + Édouard Philippe | 93 | 0.5× |
| Édouard Philippe + Gérald Darmanin | 82 | 1.4× |
| Raphaël Glucksmann + Gabriel Attal | 77 | 0.6× |
| Gabriel Attal + Emmanuel Macron | 74 | 0.3× |
| Marine Le Pen + Gabriel Attal | 71 | 0.4× |
| Édouard Philippe + Raphaël Glucksmann | 69 | 0.4× |
| Édouard Philippe + Laurent Wauquiez | 60 | 3.8× |
| Jean-Luc Mélenchon + Bruno Retailleau | 57 | 0.4× |
| Marine Tondelier + Gabriel Attal | 57 | 1.1× |
| Édouard Philippe + Emmanuel Macron | 56 | 0.2× |
| Jean-Luc Mélenchon + Marine Tondelier | 56 | 0.8× |

## Caveats

- Feeds are samples of each outlet's output, not the full output, and section feeds vs front-page feeds differ (Marianne, Mediapart). All measures are within-outlet shares, which removes volume but not editorial scope.
- Keyword matching misses indirect references ("le leader insoumis", "le chef de l'État"), and the miss rate differs by politician.
- Bootstrap intervals hold the baseline fixed and ignore week-to-week dependence, so they are somewhat optimistic.
