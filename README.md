# Plateforme d’analyse de collecte de fonds (Fintech)

Pipeline data batch, dashboards KPI et contrôles d’audit pour l’analyse des transactions de don sur plateformes Fintech.

## Compétences démontrées (alignement poste Stagiaire Data Analyst – Fintech)

| **Missions** | **Réalisation dans ce projet** |
|--------------|--------------------------------|
| **Analyse et exploitation des données** | `data_processing.py` : mapping colonnes, épuration, enrichissement (saisonnalité, géographie) à partir d’exports Excel |
| **KPI, dashboards et reportings** | `report_plotly.py` : KPI (total FCFA, transactions, contributeurs), graphiques temporels et par status/provider, design moderne |
| **Audit Logs, AML/CFT** | `audit.py` : détection doublons, montants anormaux (Z-score), dates incohérentes ; génération `audit_log.json` pour traçabilité |
| **Pipelines data (batch)** | `run_pipeline.sh` : orchestration épuration → audit → dashboard ; pipeline reproductible et automatisable |
| **SQL** | `sql_analytics.py` + `queries.sql` : chargement CSV → SQLite, requêtes analytiques (agrégations, KPI, répartitions) |
| **Collaboration (Git, déploiement)** | Structure claire, déploiement Render, usage de Git |

**Technos :** Python, pandas, Plotly, openpyxl, SQLite, SQL, Excel, Git, Render, Bash

---

## Installation

```bash
pip install -r requirements.txt
```

## Utilisation rapide (pipeline complet)

```bash
chmod +x run_pipeline.sh
./run_pipeline.sh ~/Downloads/export.xlsx
open reports/dashboard_plotly.html
```

## Pipeline détaillé

### 1. Épuration et enrichissement

```bash
python data_processing.py --input "~/Downloads/export.xlsx" --output "data/processed.csv"
```

- Mapping colonnes (id, user, ref_commande, amount, date, status, provider, etc.)
- Nettoyage (dates, montants numériques)
- Enrichissement : année, mois, trimestre, saison, jour de semaine

### 2. Audit et contrôles (Audit Logs)

```bash
python audit.py --input "data/processed.csv" --output_dir "audit_reports"
```

- Doublons (ID transaction, triplet contributeur/date/montant)
- Montants anormaux (Z-score)
- Dates hors plage
- Fichier `audit_log.json` pour traçabilité des contrôles

### 3. Dashboard KPI (Plotly)

```bash
python report_plotly.py --input "data/processed.csv" --output_html "reports/dashboard_plotly.html"
open reports/dashboard_plotly.html
```

### 4. Requêtes SQL analytiques

```bash
python sql_analytics.py --input "data/processed.csv"
```

Charge le CSV dans SQLite et exécute des requêtes KPI, agrégations, répartitions (voir `queries.sql`).

## Déploiement Render

- **Build Command :** `pip install -r requirements.txt && python report_plotly.py --input data/processed.csv --output_html build/index.html`
- **Publish Directory :** `build`
- Prérequis : `data/processed.csv` dans le dépôt

## Structure du projet

```
├── data_processing.py   # Épuration, enrichissement
├── audit.py             # Audit Logs, contrôles AML-style
├── report_plotly.py     # Dashboard KPI
├── sql_analytics.py     # Requêtes SQL
├── queries.sql          # Requêtes analytiques
├── run_pipeline.sh      # Pipeline batch
├── data/
│   └── processed.csv
├── audit_reports/
└── reports/
```
