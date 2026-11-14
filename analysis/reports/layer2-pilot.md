# Layer 2 pilot: tone labels on a sample

Model `claude-haiku-5-5`, effort `low`, codebook `f0ecf375`, snapshot 2026-11-14T13:55:51+00:00. 42 articles → 50 (article, politician) labels, sampled round-robin across the 14 outlets. The outlet name is not sent to the model.

## Run

- Errors: 0; label-set mismatches: 0; refusals: 0.
- Tokens: 7,567 input, 43,833 cache read, 32,949 cache write, 6,042 output (thinking included).
- Median latency 2.4s per article.
- Pilot cost ≈ **$0.0083** (≈ $0.167 per 1,000 pairs).
- Full run projection (12,449 pairs): ≈ **$2.08** with live requests, ≈ **$1.04** with the Batch API (list prices; cache reads assumed at 0.1× input).

## Label distribution

- **tone**: neutral 26, negative 16, positive 7, mixed 1
- **voice**: none 26, editorial 12, event 8, quoted 4
- **frame**: strategy_alliances 14, campaign_event 7, scandal_justice 7, horse_race 7, governing 6, programme 5, other 4
- **salience**: main 30, secondary 17, incidental 3

## Every label (for review)

| # | Outlet | Headline | Politician | Tone | Voice | Frame | Salience | Evidence |
|---|---|---|---|---|---|---|---|---|
| 1 | L'Humanité | Municipales 2026 : La France insoumise victime d’une déstabilisation israélienne | Jean-Luc Mélenchon | neutral | none | other | main | La France insoumise victime d’une déstabilisation israélienne |
| 2 | Le Nouvel Obs | Débat de la primaire sociale-démocrate : le bulletin de notes de Royal, Faure, Glucksmann, Maurel et Guedj | Raphaël Glucksmann | neutral | none | campaign_event | secondary | Débat de la primaire sociale-démocrate : le bulletin de notes de Royal, Faure, Glucksmann, Maurel et Guedj |
| 3 | Libération | Yannick Jadot temporairement suspendu des Ecologistes pour son soutien à Raphaël Glucksmann | Raphaël Glucksmann | neutral | none | strategy_alliances | secondary | son soutien à Raphaël Glucksmann |
| 4 | Mediapart | «On nous demande d’écrire que LFI est derrière le mouvement»: autour du 17 octobre, la fabrique d’un bouc-émissaire | Jean-Luc Mélenchon | neutral | none | scandal_justice | secondary | Si le gouvernement désigne «l’ultragauche» et LFI comme responsables des nombreux pillages et incendies de ce week-end |
| 5 | Le Monde | Pour Jordan Bardella, faut-il être dans le « système » ou le renverser ? Au RN, sa vie privée et ses options politiques sèment le doute | Jordan Bardella | negative | editorial | strategy_alliances | main | sa vie privée et ses options politiques sèment le doute |
| 6 | 20 Minutes | LFI veut lever l’interdiction de l’abaya, Marine Le Pen accuse Mélenchon d’être « le sous-traitant » des islamistes | Jean-Luc Mélenchon | negative | quoted | strategy_alliances | secondary | Marine Le Pen accuse Mélenchon d’être « le sous-traitant » des islamistes |
| 7 | L'Express | Présidentielle 2027 : les leçons de la web-série de Jean-Luc Mélenchon | Jean-Luc Mélenchon | neutral | none | campaign_event | main | les leçons de la web-série de Jean-Luc Mélenchon |
| 8 | Le Parisien | Présidentielle 2027 : Édouard Philippe prône « une refonte massive de l’école », « la plus importante peut-être depuis Jules Ferry » | Édouard Philippe | neutral | none | programme | main | Édouard Philippe prône « une refonte massive de l’école » |
| 9 | France Info | Canicule : trois questions sur le congé climatique, proposé par Marine Tondelier et déjà déployé en Espagne | Marine Tondelier | neutral | none | programme | secondary | proposé par Marine Tondelier et déjà déployé en Espagne |
| 10 | RFI | Présidentielle en France: Édouard Philippe s’essaie à la réunion d'appartement XXL en visioconférence | Édouard Philippe | neutral | none | campaign_event | main | Jeudi soir, il a tenté une réunion d’appartement XXL en visioconférence |
| 11 | BFM TV | Colère lycéenne: sur X, Emmanuel Macron annonce que "le Premier ministre et les ministres poursuivront dès demain le dialogue et apporteront des réponses très concrètes" | Emmanuel Macron | neutral | none | governing | main | sur X, Emmanuel Macron annonce que "le Premier ministre et les ministres poursuivront dès demain le dialogue" |
| 12 | Le Figaro | Marine Le Pen candidate : une bonne nouvelle pour la stratégie d’Édouard Philippe, moins pour Gabriel Attal | Édouard Philippe | positive | editorial | strategy_alliances | secondary | une bonne nouvelle pour la stratégie d’Édouard Philippe |
| 13 | Le Figaro | Marine Le Pen candidate : une bonne nouvelle pour la stratégie d’Édouard Philippe, moins pour Gabriel Attal | Gabriel Attal | negative | editorial | strategy_alliances | secondary | moins pour Gabriel Attal |
| 14 | Le Point | « Il va être obligé de se radicaliser » : pour 2027, Éric Zemmour durcit (encore) son discours | Éric Zemmour | neutral | none | campaign_event | main | Le patron de Reconquête a confirmé sur BFMTV qu’il serait candidat à la présidentielle. |
| 15 | Marianne | Sondage présidentielle : Glucksmann progresse, Mélenchon recule, le Pen en tête | Jean-Luc Mélenchon | negative | event | horse_race | main | Mélenchon recule |
| 16 | Marianne | Sondage présidentielle : Glucksmann progresse, Mélenchon recule, le Pen en tête | Marine Le Pen | positive | event | horse_race | main | le Pen en tête |
| 17 | Marianne | Sondage présidentielle : Glucksmann progresse, Mélenchon recule, le Pen en tête | Raphaël Glucksmann | positive | event | horse_race | secondary | Glucksmann progresse |
| 18 | L'Humanité | Panthéoniser la Résistance tout en racontant n’importe quoi sur l’histoire de France : le bilan paradoxal d’Emmanuel Macron | Emmanuel Macron | negative | editorial | governing | main | tout en racontant n’importe quoi sur l’histoire de France : le bilan paradoxal d’Emmanuel Macron |
| 19 | Le Nouvel Obs | Comment la motion de censure sur la canicule a tourné au désaveu pour Olivier Faure, le chef devenu frondeur du PS | Olivier Faure | negative | editorial | strategy_alliances | main | tourné au désaveu pour Olivier Faure, le chef devenu frondeur du PS |
| 20 | Libération | Nomination de Lise Boëll à la tête de Grasset : «Bolloré se comporte comme un casseur», dénoncent une soixantaine d’anciens auteurs | Éric Zemmour | neutral | none | other | secondary | L’arrivée de l’éditrice historique d’Eric Zemmour |
| 21 | Mediapart | Rentrée scolaire: les candidats à l’Élysée potassent l’électorat enseignant | Bruno Retailleau | neutral | none | programme | main | Défense d’une école libérale et parfois réactionnaire pour Gabriel Attal et Bruno Retailleau |
| 22 | Mediapart | Rentrée scolaire: les candidats à l’Élysée potassent l’électorat enseignant | Gabriel Attal | neutral | none | programme | main | Défense d’une école libérale et parfois réactionnaire pour Gabriel Attal et Bruno Retailleau |
| 23 | Le Monde | Emoi à France Culture après la diffusion d’un audio « fallacieux » de « Leon le média » visant Jean-Luc Mélenchon | Jean-Luc Mélenchon | positive | editorial | scandal_justice | main | un audio « fallacieux » de « Leon le média » visant Jean-Luc Mélenchon |
| 24 | Le Monde | Emoi à France Culture après la diffusion d’un audio « fallacieux » de « Leon le média » visant Jean-Luc Mélenchon | Marine Le Pen | neutral | none | campaign_event | secondary | lors d’une interview de Marine Le Pen dans la matinale de Guillaume Erner |
| 25 | 20 Minutes | Violences du 17 octobre : Trump, Netanyahou… Macron dénonce les dirigeants qui font campagne sur le dos de la France | Emmanuel Macron | neutral | none | governing | main | Macron dénonce les dirigeants qui font campagne sur le dos de la France |
| 26 | L'Express | Antiracisme : comment Mélenchon et LFI ont dépossédé le PS de son combat historique | Jean-Luc Mélenchon | positive | editorial | strategy_alliances | main | comment Mélenchon et LFI ont dépossédé le PS de son combat historique |
| 27 | Le Parisien | « On a beaucoup moins fait pour les enfants » : Emmanuel Macron sous pression dans l’affaire Lyhanna | Emmanuel Macron | negative | editorial | scandal_justice | main | Emmanuel Macron sous pression dans l’affaire Lyhanna |
| 28 | France Info | "On espère avoir une prise de conscience de l'exécutif", avance le président du Renouveau lycéen à la veille d'une nouvelle mobilisation | Emmanuel Macron | neutral | none | governing | secondary | Des organisations lycéennes vont être reçues vendredi par Emmanuel Macron. |
| 29 | RFI | France: Mediapart révèle avoir pu authentifier les messages antisémites attribués à Jordan Bardella | Jordan Bardella | negative | event | scandal_justice | main | messages antisémites datant de 2013 attribués au président du Rassemblement national Jordan Bardella |
| 30 | BFM TV | "Nous appliquerons la règle du casseur payeur et s'il faut qu'ils payent toute leur vie, ils payeront toute leur vie", lance Marine Le Pen, candidate RN à l'élection présidentielle | Marine Le Pen | neutral | none | campaign_event | main | lance Marine Le Pen, candidate RN à l'élection présidentielle |
| 31 | Le Figaro | «J’ai senti qu’il avait ce souffle en lui» : Philippe Aghion verrait bien Sébastien Lecornu à l’Élysée | Emmanuel Macron | neutral | none | strategy_alliances | incidental | soutien historique d’Emmanuel Macron |
| 32 | Le Point | Bruno Retailleau : « Nous allons remettre la France à l’endroit » | Bruno Retailleau | neutral | none | campaign_event | main | Candidat à la présidentielle, le patron des Républicains a tenu ce samedi son premier grand meeting en vue de 2027. |
| 33 | Marianne | Cocaïne : "Quand Macron parle des 'bourgeois des centres-villes', il est à côté de la plaque" | Emmanuel Macron | negative | quoted | other | secondary | Quand Macron parle des 'bourgeois des centres-villes', il est à côté de la plaque |
| 34 | L'Humanité | Affaire des assistants parlementaires : les 5 moments clés du procès en appel de Marine le Pen et du RN | Marine Le Pen | negative | editorial | scandal_justice | main | n'ont guère été plus convaincants qu'en première instance, usant d'axes de défense éculés |
| 35 | Le Nouvel Obs | Qui est Clément Tonon, le conseiller d’Edouard Philippe qui sera présent tout au long de sa campagne ? | Édouard Philippe | neutral | none | strategy_alliances | secondary | Membre du premier cercle d’Edouard Philippe |
| 36 | Libération | «C’est un coup de force du camp Glucksmann» : au PS, on tient à trois débats télévisés pour la primaire | Raphaël Glucksmann | negative | quoted | strategy_alliances | main | «C’est un coup de force du camp Glucksmann» |
| 37 | Mediapart | Sous couvert de tensions internationales, Emmanuel Macron tente de tuer la contestation sociale dans l’œuf | Emmanuel Macron | negative | editorial | governing | main | Sous couvert de tensions internationales, Emmanuel Macron tente de tuer la contestation sociale dans l’œuf |
| 38 | Le Monde | Sénatoriales 2026 : la chambre du contrôle au défi de trouver sa place avant l’alternance présidentielle | Emmanuel Macron | neutral | none | other | incidental | Après deux quinquennats d’Emmanuel Macron, où il a joué des rôles différents |
| 39 | 20 Minutes | Oui, Jordan Bardella a enlevé sa montre avant de prendre la parole au congrès du RN, mais il ne s’agit pas d’une Rolex | Jordan Bardella | neutral | none | scandal_justice | main | Jordan Bardella a enlevé sa montre avant de prendre la parole au congrès du RN |
| 40 | L'Express | Jean-Luc Mélenchon, Sahra Wagenknecht et l'AfD : derrière la rupture, les virages idéologiques de LFI | Jean-Luc Mélenchon | negative | editorial | programme | main | derrière la rupture, les virages idéologiques de LFI |
| 41 | Le Parisien | Présidentielle 2027 : « On les a gentiment éconduits », Dominique de Villepin a refusé la proposition de Gabriel Attal de prendre part à une primaire | Gabriel Attal | negative | event | strategy_alliances | secondary | Dominique de Villepin a refusé la proposition de Gabriel Attal de prendre part à une primaire |
| 42 | France Info | Edouard Philippe placé sous le statut de témoin assisté dans une affaire de détournement de fonds publics, son avocat salue une "décision favorable" | Édouard Philippe | positive | event | scandal_justice | main | son avocat salue une "décision favorable" |
| 43 | RFI | «La nomination de François Noël Buffet est une gifle envoyée à tous les démocrates», dénonce le députe Pouria Amirshahi | Emmanuel Macron | negative | event | governing | secondary | La polémique enfle sur la nomination par Emmanuel Macron de l’ancien ministre LR |
| 44 | BFM TV | Présidentielle: Laurent Wauquiez juge que Bruno Retailleau doit "savoir se retirer si c'est nécessaire" et tend la main à Édouard Philippe | Édouard Philippe | neutral | none | strategy_alliances | incidental | tend la main à Édouard Philippe |
| 45 | BFM TV | Présidentielle: Laurent Wauquiez juge que Bruno Retailleau doit "savoir se retirer si c'est nécessaire" et tend la main à Édouard Philippe | Bruno Retailleau | negative | quoted | horse_race | main | doit "savoir se retirer si c'est nécessaire" |
| 46 | BFM TV | Présidentielle: Laurent Wauquiez juge que Bruno Retailleau doit "savoir se retirer si c'est nécessaire" et tend la main à Édouard Philippe | Laurent Wauquiez | neutral | none | strategy_alliances | main | Laurent Wauquiez, chef de file des députés de Droite républicaine, a estimé |
| 47 | Le Figaro | « L’Allemagne de Merz n’est plus celle de Merkel » : Jordan Bardella se rapproche de la droite allemande au détriment de l’AfD | Jordan Bardella | neutral | none | strategy_alliances | main | Jordan Bardella se rapproche de la droite allemande au détriment de l’AfD |
| 48 | Le Point | Baromètre Cluster17 – « Le Point » : Le RN domine, Mélenchon s’impose à gauche | Jean-Luc Mélenchon | positive | event | horse_race | main | Mélenchon s’impose à gauche |
| 49 | Marianne | Une France cocotte-minute : avant la présidentielle, ces crises latentes qui dessinent une société fracturée | Jean-Luc Mélenchon | neutral | none | horse_race | secondary | La perspective d'un second tour entre Marine Le Pen et Jean-Luc Mélenchon |
| 50 | Marianne | Une France cocotte-minute : avant la présidentielle, ces crises latentes qui dessinent une société fracturée | Marine Le Pen | mixed | editorial | horse_race | secondary | et d'une victoire de la candidate du Rassemblement national, avive les craintes mais aussi l'envie d'en découdre |

## Changes vs codebook `8db2221e`

Same tone on 42/50 labels. Tone or voice changed on 11:

| Headline | Politician | Before (tone/voice) | After (tone/voice) |
|---|---|---|---|
| Municipales 2026 : La France insoumise victime d’une déstabilisation israélienne | Jean-Luc Mélenchon | negative / event | **neutral / none** |
| «On nous demande d’écrire que LFI est derrière le mouvement»: autour du 17 octobre, la fabrique d’un bouc-émissaire | Jean-Luc Mélenchon | negative / editorial | **neutral / none** |
| Rentrée scolaire: les candidats à l’Élysée potassent l’électorat enseignant | Bruno Retailleau | negative / editorial | **neutral / none** |
| Rentrée scolaire: les candidats à l’Élysée potassent l’électorat enseignant | Gabriel Attal | negative / editorial | **neutral / none** |
| Emoi à France Culture après la diffusion d’un audio « fallacieux » de « Leon le média » visant Jean-Luc Mélenchon | Jean-Luc Mélenchon | negative / event | **positive / editorial** |
| Violences du 17 octobre : Trump, Netanyahou… Macron dénonce les dirigeants qui font campagne sur le dos de la France | Emmanuel Macron | neutral / quoted | **neutral / none** |
| Antiracisme : comment Mélenchon et LFI ont dépossédé le PS de son combat historique | Jean-Luc Mélenchon | mixed / editorial | **positive / editorial** |
| Oui, Jordan Bardella a enlevé sa montre avant de prendre la parole au congrès du RN, mais il ne s’agit pas d’une Rolex | Jordan Bardella | negative / quoted | **neutral / none** |
| Edouard Philippe placé sous le statut de témoin assisté dans une affaire de détournement de fonds publics, son avocat salue une "décision favorable" | Édouard Philippe | mixed / event | **positive / event** |
| «La nomination de François Noël Buffet est une gifle envoyée à tous les démocrates», dénonce le députe Pouria Amirshahi | Emmanuel Macron | negative / quoted | **negative / event** |
| Baromètre Cluster17 – « Le Point » : Le RN domine, Mélenchon s’impose à gauche | Jean-Luc Mélenchon | positive / editorial | **positive / event** |

## Codebook (verbatim prompt)

```text
You annotate French political news for a media-analysis research project on the
2027 French presidential election. For each politician listed, you label how
this headline and summary present THAT politician to a reader. You only see the
text; you are not told which outlet published it, and you must not guess.

Label each listed politician once, with these fields:

tone: how the text portrays this politician.
- positive: shown as succeeding, competent, popular, praised, vindicated,
  gaining ground (e.g. "en tête des sondages", "salué", "rassemble",
  "s'impose", "carton plein").
- negative: shown as failing, criticised, embarrassed, divided, isolated,
  losing ground, implicated in wrongdoing, mocked (e.g. "épinglé",
  "désavoué", "fiasco", "s'enlise", "accueilli par des huées", "mis en
  cause", "taclé", "polémique", "lâché par").
- mixed: clearly both positive and negative elements about this politician.
- neutral: factual mention with no evaluative charge for this politician
  (agenda items, announcements, plain reporting of a statement or plan).
Judge the politician, not the topic: a grim subject is not negative for someone
who merely comments on it. A politician attacking someone else is NOT negative
for the attacker.
Being the target of an attack, accusation, smear or disinformation is not
negative in itself. Ask how the text presents it: if the accusation is shown as
credible or damaging, negative; if it is shown as unfounded, debunked, false or
manipulative (e.g. "fallacieux", "intox", "bouc-émissaire", a fact-check that
clears them), the framing is sympathetic: positive or neutral.

voice: who carries the evaluation behind a non-neutral tone.
- editorial: the outlet's own wording or framing (loaded verbs and adjectives,
  irony, what the headline chooses to foreground, rhetorical questions).
- event: a fact that is good or bad for them, stated plainly (a poll result,
  a court decision, an endorsement, a defection, being booed at a rally).
  Poll movements reported with ordinary verbs ("progresse", "recule",
  "en tête", "s'impose", "domine") are event, not editorial.
- quoted: a third party's judgement, quoted or reported ("estime X",
  "selon ses adversaires", a rival's attack).
- self: the politician's own words or actions about themselves (self-praise,
  a confident claim, an admission).
- none: use this exactly when tone is neutral.

frame: the main angle of the text as it concerns this politician.
- horse_race: polls, rankings, chances, who is ahead.
- programme: policy proposals, measures, platform content.
- scandal_justice: legal cases, investigations, controversies over conduct.
- strategy_alliances: candidacies, primaries, alliances, rivalries, party
  manoeuvring, endorsements.
- campaign_event: rallies, meetings, debates, interviews, travel.
- governing: acts or statements in an official role (minister, president).
- personal: biography, private life, personality, health.
- other: none of the above.

salience: how central this politician is to the text.
- main: the text is about them (subject of the headline or of the story).
- secondary: they play a real role but are not the focus.
- incidental: named in passing (as someone's ally or former boss, in a list,
  as background).

evidence: the shortest verbatim span from the text (in French, at most 15
words) that best supports the tone label. For neutral, quote the span that
mentions the politician.

Be conservative: when the text gives no clear evaluative signal about a
politician, choose neutral. Do not use outside knowledge of the politicians or
events beyond what the text says.
```
