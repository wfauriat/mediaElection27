# Layer 2: how each outlet presents each politician (tone)

Snapshot 2026-11-14T13:55:51+00:00 · 10,795 (article, politician) labels from 8,837 articles · arm `claude-haiku-5-5+d18c3c3b+medium` · 1,654 incidental mentions excluded · labelling cost ≈ $1.12.

Interactive version: [`layer2-tone.html`](./layer2-tone.html). Method: [`../PLAN.md`](../PLAN.md). Coverage (who gets attention) is layer 1.

## Key findings

- **Outlets differ less in whom they cover than in how they present them.** Tone slant (how much more favourably an outlet presents right-bloc than left-bloc candidates, relative to the average outlet) follows declared lean closely: Spearman **0.81** across the 11 outlets with a lean on the left–right axis, **0.87** counting only the outlet's own wording. Layer 1's coverage position showed no such link (−0.18), and the two measures are unrelated to each other (−0.20).
- **Most favourable to left-bloc candidates**: Mediapart (−0.62) and L'Humanité (−0.57), well ahead of L'Obs (−0.15) and Libération (−0.06). Mediapart presents Mélenchon far better than the press average (+0.66, net +0.57) even though it gives him less *attention* than average (layer 1: 0.69×). L'Humanité is favourable to Mélenchon (+0.38) and Glucksmann (+0.34) and the harshest on Macron (−0.43), Le Pen (−0.45), Retailleau (−0.40) and Attal (−0.39).
- **Most favourable to right-bloc candidates**: L'Express (+0.28), Le Figaro (+0.24) and Marianne (+0.20). Le Figaro is the outlet most favourable to Bardella (+0.42) and Retailleau (+0.36); L'Express is the harshest on Glucksmann (−0.55) and on the centre-left overall (−0.48), which places it with the centre-right papers rather than with the "centre" label in our seed file; Marianne is hard on the centre (−0.35) and the hard left (−0.27).
- **Outlets differ hugely in overall harshness**: net tone ranges from −0.09 at BFM TV (65% of labels neutral, 4% negative in its own wording) to −0.64 at Mediapart (73% negative, 61% in its own wording); L'Express, L'Humanité and Marianne follow Mediapart. This is why BFM TV looks "more favourable than average" toward every bloc: read the bloc table row by row, or use the slant, which removes each outlet's own level.
- **The lean shows in the outlets' own words, not only in what they report**: restricting tone to editorial wording strengthens the link with declared lean (0.81 → 0.87) and sharpens Libération's slant (−0.06 → −0.11), while events, quotes and politicians' own words dilute it.
- **Press-wide, right-bloc candidates are presented more negatively**: Bardella (−0.60, 40% of his labels framed as scandal or justice), Zemmour (−0.55) and Darmanin (−0.50) are the most negative; Glucksmann (−0.03), Mélenchon (−0.09) and Tondelier (−0.09) the least. This is descriptive: it mixes press-wide leanings with what happened to each candidate (Bardella's antisemitic-messages affair dominates his coverage). Layer 3 is needed before reading it as bias.
- **Reliability**: the labeller agreed with Claude Opus on 90% of tone labels on a held-out sample (κ 0.84); 63 of 196 outlet × politician cells differ from the press average with 90% confidence. Small cells (Mediapart has only 45 left-bloc labels) carry wide intervals, shown in every table.

## How to read

- **Net tone** = (positive − negative) / labels, from −1 (all negative) to +1. Neutral and mixed count 0.
- **Relative tone** = an outlet's net tone on X minus the press average on X (each outlet weighted equally, among outlets with ≥ 10 labels). **Bold** = the 90% bootstrap interval excludes 0; (n) = too few labels to assess.
- **All voices** = what a reader sees. **Editorial** = only the outlet's own wording carries a sign; events, quotes and the politician's own words count as 0.
- Descriptive: a politician's bad month is negative everywhere. Layer 3 compares outlets within the same weeks.

## Tone slant per outlet

Relative net tone toward right-bloc candidates minus toward left-bloc candidates (eligible candidates, centre excluded), centred on the average outlet. Positive = more favourable to the right than the average outlet.

**All voices**

| Outlet | Declared lean | Slant | 90% interval | Labels left / right |
|---|---|---|---|---|
| Mediapart | left | -0.62 | [-0.85, -0.37] | 45 / 133 |
| L'Humanité | hard-left | -0.57 | [-0.71, -0.43] | 87 / 140 |
| Le Nouvel Obs | left | -0.15 | [-0.28, -0.02] | 159 / 147 |
| Libération | left | -0.06 | [-0.15, +0.02] | 320 / 403 |
| Le Monde | centre-left | -0.02 | [-0.10, +0.06] | 271 / 380 |
| France Info | public | +0.09 | [+0.03, +0.14] | 374 / 691 |
| Le Parisien | centre | +0.09 | [+0.00, +0.18] | 333 / 314 |
| RFI | public | +0.09 | [-0.09, +0.30] | 45 / 94 |
| Le Point | centre-right | +0.13 | [-0.02, +0.28] | 103 / 127 |
| BFM TV | centre-right | +0.14 | [+0.11, +0.18] | 1180 / 1845 |
| 20 Minutes | centre | +0.17 | [+0.04, +0.27] | 180 / 200 |
| Marianne | sovereigntist | +0.20 | [+0.04, +0.36] | 113 / 123 |
| Le Figaro | centre-right | +0.24 | [+0.10, +0.41] | 77 / 141 |
| L'Express | centre | +0.28 | [+0.09, +0.46] | 53 / 97 |

**Outlet's own wording only**

| Outlet | Declared lean | Slant | 90% interval | Labels left / right |
|---|---|---|---|---|
| Mediapart | left | -0.55 | [-0.72, -0.37] | 45 / 133 |
| L'Humanité | hard-left | -0.42 | [-0.52, -0.32] | 87 / 140 |
| Libération | left | -0.11 | [-0.18, -0.05] | 320 / 403 |
| Le Nouvel Obs | left | -0.07 | [-0.17, +0.02] | 159 / 147 |
| Le Monde | centre-left | -0.00 | [-0.06, +0.04] | 271 / 380 |
| Le Parisien | centre | +0.07 | [+0.02, +0.12] | 333 / 314 |
| France Info | public | +0.08 | [+0.04, +0.11] | 374 / 691 |
| 20 Minutes | centre | +0.11 | [+0.04, +0.17] | 180 / 200 |
| Le Point | centre-right | +0.13 | [+0.01, +0.24] | 103 / 127 |
| BFM TV | centre-right | +0.14 | [+0.12, +0.15] | 1180 / 1845 |
| Le Figaro | centre-right | +0.14 | [+0.02, +0.27] | 77 / 141 |
| Marianne | sovereigntist | +0.15 | [+0.02, +0.28] | 113 / 123 |
| RFI | public | +0.16 | [+0.04, +0.27] | 45 / 94 |
| L'Express | centre | +0.19 | [+0.04, +0.34] | 53 / 97 |

## Press-average tone per politician

| Politician | Labels | Outlets assessed | Positive | Negative | Net | 90% interval | Scandal frame |
|---|---|---|---|---|---|---|---|
| Jordan Bardella | 1162 | 14 | 8% | 57% | -0.60 | [-0.64, -0.56] | 40% |
| Éric Zemmour | 167 | 6 | 3% | 50% | -0.55 | [-0.63, -0.47] | 16% |
| Gérald Darmanin | 425 | 10 | 3% | 42% | -0.50 | [-0.56, -0.45] | 24% |
| Gabriel Attal | 924 | 14 | 5% | 32% | -0.41 | [-0.45, -0.36] | 6% |
| Emmanuel Macron † | 1696 | 14 | 6% | 31% | -0.39 | [-0.43, -0.36] | 2% |
| Olivier Faure | 373 | 9 | 3% | 30% | -0.36 | [-0.42, -0.31] | 3% |
| Marine Le Pen | 1253 | 14 | 16% | 43% | -0.36 | [-0.41, -0.31] | 34% |
| Laurent Wauquiez | 110 | 3 | 5% | 40% | -0.34 | [-0.45, -0.22] | 7% |
| Bruno Retailleau | 673 | 11 | 6% | 31% | -0.31 | [-0.36, -0.26] | 2% |
| Édouard Philippe | 1045 | 14 | 16% | 31% | -0.29 | [-0.34, -0.24] | 7% |
| François Ruffin | 182 | 5 | 4% | 23% | -0.23 | [-0.30, -0.16] | 8% |
| Jean-Luc Mélenchon | 1341 | 14 | 20% | 31% | -0.09 | [-0.14, -0.04] | 6% |
| Marine Tondelier | 399 | 7 | 9% | 18% | -0.09 | [-0.16, -0.02] | 3% |
| Raphaël Glucksmann | 1045 | 14 | 23% | 21% | -0.03 | [-0.09, +0.01] | 2% |

## Relative tone by bloc (all voices)

| Outlet | hard-left | left | centre-left | centre | centre-right | right | hard-right |
|---|---|---|---|---|---|---|---|
| L'Humanité | **+0.38** | +0.11 | **+0.24** | **-0.39** | **-0.25** | **-0.40** | **-0.33** |
| Le Nouvel Obs | -0.00 | **-0.34** | +0.02 | -0.05 | -0.09 | -0.10 | **-0.16** |
| Libération | -0.01 | -0.12 | **-0.11** | -0.09 | -0.05 | **-0.19** | **-0.16** |
| Mediapart | **+0.66** | (7) | -0.20 | **-0.28** | **-0.43** | (9) | **-0.36** |
| Le Monde | -0.01 | +0.14 | +0.08 | -0.02 | **+0.13** | +0.05 | -0.06 |
| 20 Minutes | -0.06 | **+0.16** | -0.00 | +0.10 | **+0.23** | +0.01 | **+0.16** |
| L'Express | **-0.32** | (3) | **-0.48** | -0.14 | -0.14 | (8) | -0.04 |
| Le Parisien | +0.02 | +0.00 | +0.08 | +0.08 | **+0.17** | +0.06 | **+0.11** |
| France Info | -0.06 | **+0.08** | +0.08 | **+0.23** | **+0.12** | **+0.15** | **+0.14** |
| RFI | -0.05 | (3) | +0.13 | **+0.34** | +0.17 | (8) | +0.14 |
| BFM TV | +0.01 | **+0.22** | **+0.20** | **+0.32** | **+0.28** | **+0.18** | **+0.31** |
| Le Figaro | +0.04 | (9) | +0.10 | +0.08 | +0.02 | **+0.25** | **+0.28** |
| Le Point | **-0.32** | (6) | +0.02 | +0.16 | -0.04 | +0.08 | -0.08 |
| Marianne | **-0.27** | -0.24 | -0.15 | **-0.35** | -0.11 | -0.09 | +0.07 |

## Relative tone by bloc (outlet's own wording only)

| Outlet | hard-left | left | centre-left | centre | centre-right | right | hard-right |
|---|---|---|---|---|---|---|---|
| L'Humanité | **+0.14** | -0.05 | **+0.13** | **-0.46** | **-0.25** | **-0.40** | **-0.35** |
| Le Nouvel Obs | -0.03 | **-0.35** | +0.01 | -0.12 | -0.07 | -0.09 | -0.10 |
| Libération | -0.03 | -0.08 | -0.06 | **-0.09** | **-0.13** | **-0.18** | **-0.18** |
| Mediapart | **+0.37** | (7) | -0.06 | -0.20 | **-0.33** | (9) | **-0.37** |
| Le Monde | +0.06 | +0.06 | **+0.11** | +0.06 | **+0.16** | +0.03 | +0.03 |
| 20 Minutes | -0.00 | **+0.23** | **+0.09** | **+0.17** | **+0.24** | +0.09 | **+0.14** |
| L'Express | **-0.30** | (3) | **-0.46** | **-0.29** | **-0.25** | (8) | **-0.11** |
| Le Parisien | +0.03 | +0.07 | **+0.12** | **+0.20** | **+0.17** | +0.04 | **+0.15** |
| France Info | -0.01 | **+0.14** | **+0.13** | **+0.22** | **+0.14** | **+0.16** | **+0.18** |
| RFI | **+0.15** | (3) | -0.08 | **+0.28** | **+0.22** | (8) | **+0.20** |
| BFM TV | **+0.10** | **+0.17** | **+0.18** | **+0.32** | **+0.26** | **+0.21** | **+0.32** |
| Le Figaro | -0.02 | (9) | +0.10 | **+0.13** | +0.03 | **+0.17** | **+0.10** |
| Le Point | **-0.21** | (6) | -0.10 | +0.13 | -0.08 | **+0.13** | -0.09 |
| Marianne | **-0.24** | -0.20 | -0.12 | **-0.35** | -0.12 | -0.15 | +0.06 |

## Relative tone by politician (all voices)

| Outlet | Jean-Luc Mélenchon | François Ruffin | Marine Tondelier | Olivier Faure | Raphaël Glucksmann | Gabriel Attal | Gérald Darmanin | Édouard Philippe | Bruno Retailleau | Laurent Wauquiez | Jordan Bardella | Marine Le Pen | Éric Zemmour | Emmanuel Macron |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L'Humanité | **+0.38** | (9) | -0.08 | +0.03 | **+0.34** | **-0.39** | **-0.34** | -0.03 | **-0.40** | (1) | **-0.23** | **-0.45** | (3) | **-0.43** |
| Le Nouvel Obs | -0.00 | (7) | (6) | -0.10 | +0.00 | -0.05 | -0.14 | -0.07 | -0.12 | – | -0.08 | **-0.24** | (4) | +0.07 |
| Libération | -0.01 | **-0.25** | -0.13 | +0.00 | **-0.17** | -0.09 | -0.11 | -0.08 | **-0.14** | **-0.46** | **-0.18** | **-0.13** | -0.12 | -0.07 |
| Mediapart | **+0.66** | (2) | (5) | (4) | -0.24 | **-0.28** | **-0.28** | **-0.53** | (7) | (2) | **-0.36** | **-0.36** | (4) | **-0.35** |
| Le Monde | -0.01 | (6) | +0.05 | +0.11 | +0.08 | -0.02 | +0.15 | +0.10 | -0.02 | (9) | -0.05 | **-0.11** | -0.03 | **+0.15** |
| 20 Minutes | -0.06 | (8) | **+0.22** | +0.03 | -0.04 | +0.10 | +0.24 | **+0.19** | +0.03 | (5) | +0.14 | **+0.31** | (8) | +0.02 |
| L'Express | **-0.32** | (1) | (2) | (1) | **-0.55** | -0.14 | (4) | -0.10 | (8) | – | -0.09 | -0.08 | – | -0.18 |
| Le Parisien | +0.02 | +0.14 | **-0.14** | +0.06 | +0.05 | +0.08 | **+0.24** | **+0.14** | +0.06 | (5) | **+0.20** | +0.21 | +0.08 | **+0.14** |
| France Info | -0.06 | **+0.18** | -0.06 | +0.05 | +0.08 | **+0.23** | +0.16 | **+0.09** | **+0.12** | +0.24 | +0.09 | **+0.12** | +0.11 | **+0.25** |
| RFI | -0.05 | – | (3) | (5) | +0.28 | **+0.34** | (8) | +0.13 | (8) | – | +0.03 | +0.14 | (2) | **+0.29** |
| BFM TV | +0.01 | **+0.20** | **+0.13** | **+0.25** | **+0.18** | **+0.32** | **+0.27** | **+0.27** | **+0.16** | **+0.22** | **+0.34** | **+0.23** | **+0.32** | **+0.28** |
| Le Figaro | +0.04 | (1) | (8) | (6) | +0.08 | +0.08 | (9) | +0.02 | **+0.36** | (9) | **+0.42** | +0.19 | (5) | -0.00 |
| Le Point | **-0.32** | (2) | (4) | **-0.44** | +0.12 | +0.16 | (5) | -0.04 | +0.02 | (4) | -0.11 | +0.03 | **-0.35** | -0.13 |
| Marianne | **-0.27** | -0.27 | (8) | (2) | **-0.21** | **-0.35** | -0.20 | -0.10 | -0.06 | (3) | -0.11 | +0.15 | (6) | -0.05 |

## Who carries the negativity

| Outlet | Negative labels | editorial | event | quoted | self | Editorial-negative rate |
|---|---|---|---|---|---|---|
| L'Humanité | 180 | 87% | 10% | 3% | 0% | 53% |
| Le Nouvel Obs | 182 | 72% | 13% | 14% | 1% | 34% |
| Libération | 475 | 79% | 8% | 13% | 0% | 41% |
| Mediapart | 165 | 83% | 8% | 8% | 0% | 61% |
| Le Monde | 351 | 55% | 18% | 27% | 0% | 20% |
| 20 Minutes | 176 | 43% | 20% | 36% | 1% | 16% |
| L'Express | 103 | 91% | 3% | 6% | 0% | 54% |
| Le Parisien | 294 | 45% | 25% | 29% | 1% | 14% |
| France Info | 463 | 43% | 17% | 39% | 0% | 14% |
| RFI | 63 | 44% | 27% | 29% | 0% | 15% |
| BFM TV | 846 | 17% | 24% | 57% | 2% | 4% |
| Le Figaro | 104 | 73% | 12% | 14% | 1% | 26% |
| Le Point | 139 | 75% | 11% | 14% | 0% | 37% |
| Marianne | 175 | 77% | 8% | 15% | 0% | 43% |

Editorial-negative rate = share of all an outlet's labels that are negative *in its own wording*.

## Validation

- `dev` sample (200 pairs, reference `opus-v3-medium`): tone agreement 90% (κ 0.83), 0 opposite-sign, voice 85%, frame 82%.
- `test` sample (100 pairs, reference `opus-v4-medium`): tone agreement 90% (κ 0.84), 2 opposite-sign, voice 76%, frame 81%.

Known limitations (see PLAN.md): headlines contradicted by their summary can be misread; voice is the least reliable field; keyword-based mention detection misses indirect references.
