# Cahier des charges (implémentation prototype)

## Portée couverte

- Préparation des données : chargement CSV, suppression des doublons, gestion des valeurs manquantes.
- Analyse exploratoire légère : métriques de volumétrie affichées dans le dashboard.
- Prévision : modèle baseline (dernière valeur) + modèle ML (régression linéaire entraînée).
- Évaluation : MAE et RMSE, comparaison baseline vs ML.
- Recommandation de commande : stock de sécurité, point de commande, quantité recommandée.
- Dashboard Streamlit : exécution du pipeline, tableau d’évaluation, tableau de recommandations.

## Limites connues (alignées au périmètre)

- Prototype hors ERP et hors production temps réel.
- Règle de réapprovisionnement volontairement simple.
- Données d’exemple publiques/simulées uniquement.
