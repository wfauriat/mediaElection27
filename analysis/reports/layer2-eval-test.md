# Layer 2 evaluation (test sample): Haiku arms vs a reference model

Snapshot 2026-11-14T13:55:51+00:00. Sample `test`: 71 articles / 100 (article, politician) pairs, round-robin across outlets, **disjoint from the pilot and from every other evaluation sample**. Reference = `claude-opus-5-5` (effort medium) with codebook `v4`. Agreement with a stronger model is a proxy for accuracy, not ground truth: where they disagree, the disagreements table below is what to read.

## Agreement with the reference

| Arm | Tone | κ tone | Opposite sign | Voice (both non-neutral) | Frame | Salience | Neutral rate | Errors | Cost (sample) | Full run, batch |
|---|---|---|---|---|---|---|---|---|---|---|
| `haiku-v4-low` (d18c3c3b) | 83% | 0.73 | 2 | 78% (n=49) | 82% | 89% | 47% | 0 | $0.012 | $0.73 |
| `haiku-v4-medium` (d18c3c3b) | 90% | 0.84 | 2 | 76% (n=50) | 81% | 88% | 49% | 0 | $0.017 | $1.07 |
| `opus-v4-medium` (d18c3c3b) | reference | | | | | | 47% | 0 | $0.629 | $39.15 |

*Opposite sign* = pairs where one says positive and the other negative: the errors that would flip a slant estimate. Full-run costs extrapolate the measured per-pair cost to all 12,449 pairs at Batch API prices.

## Tone confusion: `haiku-v4-medium` vs reference

| reference ↓ / arm → | positive | neutral | negative | mixed |
|---|---|---|---|---|
| positive | 11 | 0 | 2 | 1 |
| neutral | 0 | 46 | 1 | 0 |
| negative | 0 | 3 | 31 | 0 |
| mixed | 0 | 0 | 3 | 2 |

## Tone disagreements: `haiku-v4-medium` vs reference (10)

| Outlet | Headline | Politician | Haiku | Reference | Haiku evidence | Reference evidence |
|---|---|---|---|---|---|---|
| 20 Minutes | Présidentielle 2027 : Marine Tondelier ne veut soutenir ni Mélenchon ni Glucksmann (en tout cas pour l’instant) | Marine Tondelier | neutral / none | negative / editorial | Marine Tondelier souhaite une candidature écologiste pour la présidentielle | (en tout cas pour l’instant) |
| 20 Minutes | Présidentielle 2027 : Édouard Philippe sera candidat même en cas de mise en examen | Édouard Philippe | neutral / none | negative / editorial | Édouard Philippe sera candidat même en cas de mise en examen | Édouard Philippe sera candidat même en cas de mise en examen |
| RFI | LFI : une radicalité revendiquée ou fantasmée | Jean-Luc Mélenchon | mixed / editorial | positive / event | Les sondages annoncent un score important du mouvement de Jean-Luc Mélenchon à la prochaine élection présidentielle française. | Les sondages annoncent un score important du mouvement de Jean-Luc Mélenchon |
| Le Figaro | Présidentielle 2027 : pourquoi Bruno Retailleau veut marquer ses différences économiques avec Marine Le Pen | Bruno Retailleau | negative / event | mixed / event | accuse un recul dans les sondages | le candidat des Républicains accuse un recul dans les sondages |
| Marianne | "Ici, on t’applaudit, Raphaël" : à Saint-Ouen, Glucksmann et Bouamrane roucoulent avant la présidentielle | Raphaël Glucksmann | negative / editorial | mixed / editorial | Glucksmann et Bouamrane roucoulent avant la présidentielle | Glucksmann et Bouamrane roucoulent avant la présidentielle |
| Libération | Il reste huit mois pour arrêter l’ascension de Marine Le Pen (et c’est possible), par Bernard Guetta | Marine Le Pen | negative / editorial | mixed / quoted | Il reste huit mois pour arrêter l'ascension de Marine Le Pen | Il reste huit mois pour arrêter l’ascension de Marine Le Pen (et c’est possible) |
| Le Point | Mélenchon en démonstration, Attal en embuscade… À Lille, les prétendants à la présidentielle se bousculent | Gabriel Attal | negative / editorial | neutral / none | Attal en embuscade | Attal en embuscade |
| Le Point | Présidentielle : les chouchous de Moscou | Raphaël Glucksmann | negative / editorial | positive / editorial | les chouchous de Moscou | les services d’intoxication russes ne désignent pas seulement leurs cibles |
| Le Point | Présidentielle : les chouchous de Moscou | Gabriel Attal | negative / editorial | positive / editorial | les chouchous de Moscou | En s’en prenant aux seuls Glucksmann, Attal et Philippe, les services d’intoxication russes |
| Marianne | Les indiscrétions de "Marianne" : un soutien explosif au meeting de Marine Le Pen à Orléans | Marine Le Pen | neutral / none | negative / editorial | un soutien explosif au meeting de Marine Le Pen à Orléans | un soutien explosif au meeting de Marine Le Pen à Orléans |
