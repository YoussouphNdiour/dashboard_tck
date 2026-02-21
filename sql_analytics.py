"""
Requêtes analytiques SQL sur les données de collecte de fonds.

Charge data/processed.csv dans SQLite et exécute des requêtes KPI,
agrégations par période et contrôles de cohérence.
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pandas as pd


def load_to_sqlite(csv_path: str | Path, db_path: str | Path = "data/transactions.db") -> sqlite3.Connection:
    """Charge le CSV dans une base SQLite pour requêtes analytiques."""
    csv_path = Path(os.path.expanduser(str(csv_path)))
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(csv_path)
    conn = sqlite3.connect(db_path)
    df.to_sql("transactions", conn, if_exists="replace", index=False)
    return conn


def run_queries(conn: sqlite3.Connection) -> None:
    """Exécute des requêtes analytiques et affiche les résultats."""
    queries = [
        ("KPI - Total collecte (FCFA)", "SELECT SUM(montant) AS total_fcfa, COUNT(*) AS nb_transactions, COUNT(DISTINCT id_contributeur) AS nb_contributeurs FROM transactions"),
        ("Agregation mensuelle", "SELECT annee, mois, SUM(montant) AS total FROM transactions GROUP BY annee, mois ORDER BY annee, mois"),
        ("Top 5 providers par montant", "SELECT provider, SUM(montant) AS total FROM transactions WHERE provider IS NOT NULL GROUP BY provider ORDER BY total DESC LIMIT 5"),
        ("Repartition par status", "SELECT status, COUNT(*) AS nb, SUM(montant) AS total FROM transactions GROUP BY status ORDER BY total DESC"),
    ]

    for title, sql in queries:
        print(f"\n--- {title} ---")
        print(sql)
        df = pd.read_sql_query(sql, conn)
        print(df.to_string(index=False))


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Requêtes SQL analytiques sur les données de collecte.")
    parser.add_argument("--input", default="data/processed.csv", help="CSV source")
    parser.add_argument("--db", default="data/transactions.db", help="Base SQLite de sortie")
    args = parser.parse_args()

    conn = load_to_sqlite(args.input, args.db)
    run_queries(conn)
    conn.close()
    print(f"\nBase SQLite : {args.db}")


if __name__ == "__main__":
    main()
