# Prévision de la demande & optimisation de stock (prototype IA)

Prototype minimal conforme au cahier des charges :
- pipeline de préparation des données,
- analyse exploratoire simple,
- modèle baseline + modèle ML,
- recommandation de quantité à commander,
- dashboard Streamlit.

## Structure

- `data/` : jeux de données (inclut un échantillon CSV)
- `src/` : logique métier (pipeline, features, prévision, stock)
- `app/` : dashboard Streamlit
- `docs/` : documentation projet
- `notebooks/` : emplacement d'analyse exploratoire
- `tests/` : tests unitaires ciblés

## Lancer la démonstration CLI

```bash
python /home/runner/work/Prevision-de-la-Demande-Optimization-de-Stock/Prevision-de-la-Demande-Optimization-de-Stock/src/pipeline.py \
  --input /home/runner/work/Prevision-de-la-Demande-Optimization-de-Stock/Prevision-de-la-Demande-Optimization-de-Stock/data/sample_sales.csv \
  --horizon 7
```

Le pipeline accepte aussi les données transactionnelles Marjane (`ticket,date,magasin,sku,produit,categorie,quantite,prix`) et applique automatiquement le nettoyage (doublons, dates invalides, valeurs négatives/nulles, imputation des quantités manquantes, suppression des aberrants), puis l’agrégation journalière par magasin/SKU.

## Lancer le dashboard

```bash
streamlit run /home/runner/work/Prevision-de-la-Demande-Optimization-de-Stock/Prevision-de-la-Demande-Optimization-de-Stock/app/dashboard.py
```

## Tests

```bash
python -m unittest discover -s /home/runner/work/Prevision-de-la-Demande-Optimization-de-Stock/Prevision-de-la-Demande-Optimization-de-Stock/tests -v
```