# Layer 2 evaluation (dev sample): Haiku arms vs a reference model

Snapshot 2026-11-14T13:55:51+00:00. Sample `dev`: 159 articles / 200 (article, politician) pairs, round-robin across outlets, **disjoint from the pilot and from every other evaluation sample**. Reference = `claude-opus-5-5` (effort medium) with codebook `v3`. Agreement with a stronger model is a proxy for accuracy, not ground truth: where they disagree, the disagreements table below is what to read.

## Agreement with the reference

| Arm | Tone | κ tone | Opposite sign | Voice (both non-neutral) | Frame | Salience | Neutral rate | Errors | Cost (sample) | Full run, batch |
|---|---|---|---|---|---|---|---|---|---|---|
| `haiku-v2-low` (f0ecf375) | 84% | 0.75 | 1 | 80% (n=85) | 77% | 86% | 52% | 0 | $0.025 | $0.78 |
| `haiku-v3-medium` (60a22583) | 88% | 0.80 | 0 | 90% (n=88) | 80% | 84% | 53% | 0 | $0.036 | $1.11 |
| `haiku-v4-low` (d18c3c3b) | 84% | 0.74 | 1 | 84% (n=94) | 77% | 83% | 44% | 0 | $0.029 | $0.90 |
| `haiku-v4-medium` (d18c3c3b) | 90% | 0.83 | 0 | 85% (n=95) | 82% | 86% | 46% | 0 | $0.037 | $1.14 |
| `haiku-v3-low` (60a22583) | 84% | 0.73 | 1 | 85% (n=84) | 77% | 84% | 53% | 0 | $0.028 | $0.86 |
| `opus-v3-medium` (60a22583) | reference | | | | | | 50% | 0 | $1.014 | $31.57 |

*Opposite sign* = pairs where one says positive and the other negative: the errors that would flip a slant estimate. Full-run costs extrapolate the measured per-pair cost to all 12,449 pairs at Batch API prices.

## Tone confusion: `haiku-v3-low` vs reference

| reference ↓ / arm → | positive | neutral | negative | mixed |
|---|---|---|---|---|
| positive | 11 | 6 | 1 | 1 |
| neutral | 3 | 91 | 4 | 3 |
| negative | 0 | 9 | 54 | 4 |
| mixed | 0 | 0 | 2 | 11 |

## Tone disagreements: `haiku-v3-low` vs reference (33)

| Outlet | Headline | Politician | Haiku | Reference | Haiku evidence | Reference evidence |
|---|---|---|---|---|---|---|
| Le Nouvel Obs | Présidentielle 2027 : la gauche est-elle coincée entre un duel perdant Mélenchon-Bardella et un « vote utile » Edouard Philippe ? | Jordan Bardella | negative / editorial | neutral / none | un duel perdant Mélenchon-Bardella | un duel perdant Mélenchon-Bardella |
| 20 Minutes | Présidentielle 2027 : « C’est flou »… Pourquoi Raphaël Glucksmann prend-il autant son temps pour être candidat ? | Raphaël Glucksmann | neutral / none | negative / quoted | Le patron de Place publique s’est donné trois mois pour dire s’il sera ou non candidat | « C’est flou »… Pourquoi Raphaël Glucksmann prend-il autant son temps |
| L'Express | Interdiction du voile : "La destitution de Marine Le Pen ne serait pas impensable si..." | Marine Le Pen | neutral / none | negative / quoted | La destitution de Marine Le Pen ne serait pas impensable si... | "La destitution de Marine Le Pen ne serait pas impensable si..." |
| Le Nouvel Obs | Ces sondages précoces de la présidentielle 2027 qui nourrissent un débat « purement spéculatif » | Jean-Luc Mélenchon | neutral / none | positive / event | Jean-Luc Mélenchon en position de se qualifier | Jean-Luc Mélenchon en position de se qualifier |
| Libération | Comment une vidéo relayée par Marine Le Pen, coupée et remontée neuf fois, manipule le discours de Mélenchon sur la «nouvelle France» | Jean-Luc Mélenchon | negative / editorial | positive / editorial | une vidéo relayée par Marine Le Pen, coupée et remontée neuf fois, manipule le discours de Mélenchon | coupée et remontée neuf fois, manipule le discours de Mélenchon |
| L'Humanité | Jordan Bardella : le boulet de Marine Le Pen ? | Marine Le Pen | negative / editorial | neutral / none | Jordan Bardella : le boulet de Marine Le Pen ? | le boulet de Marine Le Pen ? |
| L'Express | "N’allez pas croire un instant que j’aime la pagaille" : face au blocus des lycées, Jean-Luc Mélenchon entre deux eaux | Jean-Luc Mélenchon | mixed / editorial | negative / editorial | Jean-Luc Mélenchon entre deux eaux | Jean-Luc Mélenchon entre deux eaux |
| RFI | France: Édouard Philippe à l'offensive pour le rassemblement | Gérald Darmanin | positive / event | neutral / none | après l'annonce du ralliement du ministre de la Justice à sa candidature | aux côtés de Gérald Darmanin qui organisait comme à son habitude sa rentrée politique |
| Le Figaro | Accusations d’antisémitisme : la pression monte sur Jordan Bardella, le RN fait toujours bloc | Jordan Bardella | negative / editorial | mixed / editorial | la pression monte sur Jordan Bardella | la pression monte sur Jordan Bardella, le RN fait toujours bloc |
| Libération | Ralliement de Darmanin à Philippe : au secours, l’UMP revient ! | Gérald Darmanin | neutral / none | negative / editorial | Le soutien du ministre de la Justice au candidat Horizons à la présidentielle | Ralliement de Darmanin à Philippe : au secours, l’UMP revient ! |
| Mediapart | Primaire du PS: derrière le favori Raphaël Glucksmann, Olivier Faure en embuscade | Olivier Faure | neutral / none | positive / editorial | De quoi relancer les espoirs des proches du premier secrétaire du PS. | Olivier Faure en embuscade |
| BFM TV | "Nous n'allons pas nous laisser faire": Marine Le Pen renouvelle "sa confiance absolue" en Jordan Bardella après les accusations d'écrits antisémites | Marine Le Pen | mixed / self | neutral / none | Marine Le Pen renouvelle "sa confiance absolue" en Jordan Bardella | Marine Le Pen renouvelle "sa confiance absolue" en Jordan Bardella |
| Le Nouvel Obs | Russie, Géorgie, Sarkozy… un livre retrace l’histoire secrète des Glucksmann | Raphaël Glucksmann | neutral / none | positive / event | un livre retrace l'histoire secrète des Glucksmann | les ressorts familiaux du favori de la primaire |
| France Info | Congrès du RN à Orléans : le service de sécurité vérifie que "les femmes portent un soutien-gorge" pour éviter l'intrusion de militantes Femen | Jordan Bardella | neutral / none | positive / event | Jordan Bardella a été réélu à la tête du parti d'extrême droite | Jordan Bardella a été réélu à la tête du parti d'extrême droite |
| RFI | Attentat de Trappes: «Il y a une banalisation de la parole raciste et antisémite dans l'espace politique et médiatique» | Édouard Philippe | mixed / editorial | negative / editorial | Quelles réponses apportent Édouard Philippe à ces revendications ? | les propos polémiques de son candidat concernant l'origine supposée des auteurs de pillages |
| RFI | Procès en appel de Marine Le Pen: les militants Rassemblement national entre appréhension et résignation | Marine Le Pen | neutral / none | negative / event | Marine Le Pen va être fixée sur son sort judiciaire dans l'affaire des assistants d'eurodéputés | dans laquelle elle encourt de l'inéligibilité |
| BFM TV | Marche des fiertés: à six mois de la présidentielle, l'autorisation de la GPA en France toujours dans le débat | Gabriel Attal | mixed / editorial | negative / event | la proposition de Gabriel Attal d'en "débattre" en mai dernier | la proposition fait l'unanimité contre elle dans le bloc central |
| Marianne | "Elle, on sait qu’elle va pas nous mettre de côté" : ils rêvent d'élire Marine le Pen, condamnée ou non | Marine Le Pen | mixed / editorial | positive / quoted | ils rêvent d'élire Marine le Pen, condamnée ou non | "Elle, on sait qu’elle va pas nous mettre de côté" |
| Libération | Sous le feu des attaques après le 17 octobre, LFI fait «monter la pression» sur le gouvernement | Jean-Luc Mélenchon | mixed / editorial | neutral / none | Sous le feu des attaques après le 17 octobre, LFI fait «monter la pression» | le mouvement de Jean-Luc Mélenchon a continué mardi de riposter |
| Le Point | Populism or not populism, le dilemme présidentiel du RN | Jordan Bardella | mixed / editorial | neutral / none | Derrière l’image du tandem uni Le Pen- Bardella, les cadres du Rassemblement national s’opposent de plus en plus frontalement | Derrière l’image du tandem uni Le Pen- Bardella |
| Le Nouvel Obs | Gauche, le choc des générations | Jean-Luc Mélenchon | neutral / none | positive / event | Près d’un jeune sur deux pourrait voter Mélenchon | Près d’un jeune sur deux pourrait voter Mélenchon |
| Libération | Accusations de détournement de fonds publics : Edouard Philippe placé sous le statut de témoin assisté | Édouard Philippe | neutral / none | negative / event | Edouard Philippe placé sous le statut de témoin assisté | Accusations de détournement de fonds publics : Edouard Philippe placé sous le statut de témoin assisté |
| Le Monde | Attentat de Trappes : la gauche en ordre dispersé dans les rassemblements contre le racisme | Raphaël Glucksmann | positive / editorial | neutral / none | Autour de leur candidat à la présidentielle, Raphaël Glucksmann, les partis de l'espace social-démocrate ont répondu à l'appel | Autour de leur candidat à la présidentielle, Raphaël Glucksmann, les partis de l’espace social-démocrate |
| L'Express | Marine Le Pen, la présidentielle et le budget 2027 : le réel, c’est quand on se cogne | Marine Le Pen | neutral / none | negative / editorial | Marine Le Pen, la présidentielle et le budget 2027 : le réel, c’est quand on se cogne | le réel, c’est quand on se cogne |
| Le Parisien | « Des divergences stratégiques » : entre Laurent Wauquiez et Bruno Retailleau, un rendez-vous sans résultat | Bruno Retailleau | neutral / none | negative / editorial | entre Laurent Wauquiez et Bruno Retailleau, un rendez-vous sans résultat | un rendez-vous sans résultat |
| Le Parisien | « Des divergences stratégiques » : entre Laurent Wauquiez et Bruno Retailleau, un rendez-vous sans résultat | Laurent Wauquiez | neutral / none | negative / editorial | entre Laurent Wauquiez et Bruno Retailleau, un rendez-vous sans résultat | un rendez-vous sans résultat |
| Le Point | Othman Nasrou (LR) : « Nous sommes prêts à un débat avec Édouard Philippe, projet contre projet » | Bruno Retailleau | positive / self | neutral / none | Déterminé à démontrer qu'il est le candidat de la « vraie rupture » | Bruno Retailleau est favorable à une confrontation devant les Français avec ses compétiteurs |
| Le Figaro | L’été décisif de Gabriel Attal, toujours «challenger» | Gabriel Attal | neutral / none | negative / editorial | L'été décisif de Gabriel Attal, toujours «challenger» | toujours «challenger» |
| Le Figaro | L’été décisif de Gabriel Attal, toujours «challenger» | Édouard Philippe | neutral / none | positive / editorial | face à Édouard Philippe | marquer des points face à Édouard Philippe |
| Le Point | Gaza et LFI : la primaire de la gauche à l’épreuve de ses divisions | Jean-Luc Mélenchon | negative / editorial | neutral / none | les échanges se sont rapidement crispés autour de l’international et du rapport à Jean-Luc Mélenchon | les échanges se sont rapidement crispés autour de l’international et du rapport à Jean-Luc Mélenchon |
| L'Humanité | Présidentielle 2027 : en meeting, Édouard Philippe promet de la « sueur » pour les travailleurs et la « liberté » pour les entreprises | Édouard Philippe | mixed / editorial | negative / editorial | on sait déjà qu’il est massivement libéral | promet de la « sueur » pour les travailleurs et la « liberté » pour les entreprises |
| Marianne | "Double primaire" de la gauche non-insoumise : tango tragi-comique entre Faure et Glucksmann | Raphaël Glucksmann | negative / editorial | mixed / editorial | tango tragi-comique entre Faure et Glucksmann | tango tragi-comique entre Faure et Glucksmann |
| Mediapart | La chronique de Waly Dia. «Appelez-nous “issus de la colonisation”» | Édouard Philippe | negative / quoted | neutral / none | les propos d’Édouard Philippe associant les pillages et l’immigration | les propos d’Édouard Philippe associant les pillages et l’immigration |
