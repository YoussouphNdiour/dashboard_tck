-- Requêtes analytiques sur les transactions de collecte de fonds
-- Données chargées depuis data/processed.csv dans la table transactions

-- KPI principaux
SELECT
    SUM(montant) AS total_collecte_fcfa,
    COUNT(*) AS nb_transactions,
    COUNT(DISTINCT id_contributeur) AS nb_contributeurs_uniques
FROM transactions;

-- Agrégation mensuelle (saisonnalité)
SELECT
    annee,
    mois,
    SUM(montant) AS total_mensuel,
    COUNT(*) AS nb_transactions
FROM transactions
GROUP BY annee, mois
ORDER BY annee, mois;

-- Répartition par provider (canaux de paiement)
SELECT
    provider,
    SUM(montant) AS total,
    COUNT(*) AS nb_transactions
FROM transactions
WHERE provider IS NOT NULL
GROUP BY provider
ORDER BY total DESC;

-- Répartition par status
SELECT
    status,
    SUM(montant) AS total,
    COUNT(*) AS nb
FROM transactions
GROUP BY status
ORDER BY total DESC;
