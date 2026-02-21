## Plateforme d’analyse de collecte de fonds

Ce projet fournit :

- un **script d’épuration et d’enrichissement** des données de dons (`data_processing.py`) ;
- un **module d’audit et de sécurité** (`audit.py`) ;
- un **dashboard Plotly (HTML)** pour le suivi des KPI de collecte (`report_plotly.py`).

### 1. Installation

Dans votre environnement (idéalement un virtualenv) :

```bash
cd "Plateforme d'Analyse de Collecte de Fonds TCK"
pip install -r requirements.txt
```

### 2. Préparation des données

Placez votre export (par ex. `export.xlsx`) dans un dossier de votre choix (par ex. `~/Downloads/export.xlsx`).

Lancez le script de traitement :

```bash
python data_processing.py \
  --input "~/Downloads/export.xlsx" \
  --output "data/processed.parquet" \
  --sheet "NomDeLaFeuille"  # optionnel
```

Ce script :

- détecte automatiquement les colonnes importantes (date, montant, géographie, etc.) pour la plupart des exports ;
- nettoie les données (dates invalides, montants non numériques, montants nuls ou négatifs) ;
- enrichit les données avec :
  - année, mois, trimestre ;
  - saison (Hiver, Printemps, Été, Automne) ;
  - pays / région / ville si disponibles ;
  - identifiants normalisés des contributeurs et transactions si présents.

### 3. Audit & sécurité

Après traitement des données (`data/processed.parquet`), exécutez :

```bash
python audit.py \
  --input "data/processed.parquet" \
  --output_dir "audit_reports"
```

Cela génère des rapports CSV :

- `doublons_transactions.csv` : transactions en double (par ID transaction ou par triplet contributeur/date/montant) ;
- `montants_anormaux.csv` : montants considérés comme extrêmes (basés sur un Z-score) ;
- `dates_incoherentes.csv` : dates hors plage.

### 4. Tableau de bord (Reporting & KPI) – version Plotly (HTML)

Une fois les données enrichies prêtes (`data/processed.parquet` par exemple) :

```bash
python report_plotly.py \
  --input "data/processed.parquet" \
  --output_html "reports/dashboard_plotly.html"
```

Ensuite, ouvrez le fichier HTML généré avec votre navigateur :

```bash
open reports/dashboard_plotly.html  # macOS
```

Le dashboard Plotly propose notamment :

- les KPI principaux : **total collecté (FCFA)**, nombre de transactions, nombre de contributeurs uniques ;
- l’évolution temporelle mensuelle des montants collectés ;
- la répartition par **région** et par **saison** ;
- des filtres interactifs (année, saison, région, ville).

### 5. Déploiement sur Render (site statique)

Le dashboard peut être déployé sur [Render](https://render.com) en tant que **site statique**. Prérequis : `data/processed.csv` doit être dans le dépôt.

**Configuration** : Static Site → Build Command : `pip install -r requirements.txt && python report_plotly.py --input data/processed.csv --output_html build/index.html` → Publish Directory : `build`. Un `render.yaml` et `.python-version` (Python 3.12) sont fournis.

### 6. Adaptation aux spécificités de votre export

Si les noms de colonnes de votre fichier ne sont pas reconnus automatiquement, nous pourrons ajuster le mapping dans `data_processing.py` (classe `ColumnMapping`). Partagez un exemple d’en-têtes de colonnes et nous pourrons l’adapter précisément à votre cas.

