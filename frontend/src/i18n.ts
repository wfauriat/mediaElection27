/** Single-locale (fr-FR) string table. Keep keys descriptive; values can stay
 *  inline if a refactor to a real i18n library happens later. */

export const t = {
  app: {
    title: "mediaElection27",
    subtitle: "Couverture média de la présidentielle 2027",
  },
  filters: {
    candidates: "Candidats",
    selectAll: "Tout sélectionner",
    clearAll: "Tout désélectionner",
    period: "Période",
    from: "Du",
    to: "Au",
    eligible: "Éligibles",
    ineligible: "Inéligibles / suivis",
  },
  chart: {
    title: "Mentions par jour",
    yAxisLabel: "Nombre de mentions",
    noData: "Aucune mention dans cette période. Élargissez la fenêtre temporelle ou sélectionnez d'autres candidats.",
    loading: "Chargement…",
  },
  stats: {
    totalMentions: "Mentions totales",
    articles: "Articles",
    activeSources: "Médias actifs",
    period: "Période sélectionnée",
  },
  errors: {
    apiUnreachable: "API indisponible. Vérifiez que `make api` est en cours d'exécution.",
    parseError: "Réponse de l'API invalide.",
    unknown: "Une erreur s'est produite.",
  },
  footer: {
    methodology:
      "Données : flux RSS publics. Mentions extraites par appariement par mots-clés (extracteur keyword v1).",
    sourceCode: "Code source",
  },
} as const;
