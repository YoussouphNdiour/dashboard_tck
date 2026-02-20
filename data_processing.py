from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import os

import numpy as np
import pandas as pd


@dataclass
class ColumnMapping:
    """Configuration souple pour adapter les noms de colonnes à votre fichier."""

    contributor_id: str = "contributor_id"
    transaction_id: str = "transaction_id"
    date: str = "date"
    amount: str = "amount"
    country: Optional[str] = "country"
    region: Optional[str] = "region"
    city: Optional[str] = "city"


SEASONS_FR = {
    12: "Hiver",
    1: "Hiver",
    2: "Hiver",
    3: "Printemps",
    4: "Printemps",
    5: "Printemps",
    6: "Été",
    7: "Été",
    8: "Été",
    9: "Automne",
    10: "Automne",
    11: "Automne",
}


def load_raw_data(path: str | Path, sheet_name: Optional[str] = None) -> pd.DataFrame:
    """Charge un fichier Excel ou CSV en DataFrame."""
    # Gérer correctement le "~" (répertoire utilisateur)
    path = Path(os.path.expanduser(str(path)))
    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable: {path}")

    if path.suffix.lower() in {".xls", ".xlsx"}:
        # Si aucun nom de feuille n'est donné, on lit uniquement la première feuille,
        # pour éviter que pandas ne renvoie un dict de DataFrame.
        if sheet_name is None:
            return pd.read_excel(path, sheet_name=0, engine="openpyxl")
        return pd.read_excel(path, sheet_name=sheet_name, engine="openpyxl")
    if path.suffix.lower() in {".csv"}:
        return pd.read_csv(path)

    raise ValueError("Format de fichier non supporté (utiliser .xlsx ou .csv).")


def _standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Nettoie les noms de colonnes pour faciliter le mapping (minuscules, sans espaces)."""
    df = df.copy()
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
    )
    return df


def _infer_column(name_candidates: List[str], df: pd.DataFrame) -> Optional[str]:
    for cand in name_candidates:
        if cand in df.columns:
            return cand
    return None


def infer_mapping(df: pd.DataFrame) -> ColumnMapping:
    """Essaie de déduire automatiquement le mapping à partir des noms de colonnes."""
    candidates = {
        # ID du contributeur (dans ton export: `user` ou éventuellement `id`)
        "contributor_id": [
            "contributor_id",
            "id_contributeur",
            "donor_id",
            "id_donateur",
            "user",
            "id",
        ],
        # ID de transaction (dans ton export: `provider_transaction_id` ou `ref_commande`)
        "transaction_id": [
            "transaction_id",
            "id_transaction",
            "ref_transaction",
            "reference",
            "provider_transaction_id",
            "ref_commande",
        ],
        # Date du don (dans ton export: `date`)
        "date": ["date", "date_don", "transaction_date"],
        # Montant du don (dans ton export: `amount`)
        "amount": ["amount", "montant", "montant_fcfa", "value"],
        "country": ["country", "pays"],
        "region": ["region", "région"],
        "city": ["city", "ville", "localite"],
    }

    df_norm = _standardize_columns(df)

    mapping_kwargs = {}
    for field, names in candidates.items():
        col = _infer_column(names, df_norm)
        if col is not None:
            mapping_kwargs[field] = col

    return ColumnMapping(**mapping_kwargs)


def clean_and_enrich(
    df: pd.DataFrame,
    mapping: Optional[ColumnMapping] = None,
    currency: str = "FCFA",
) -> pd.DataFrame:
    """Epuration des données et enrichissement (saisonnalité, géographie agrégée, etc.)."""
    df = _standardize_columns(df)

    if mapping is None:
        mapping = infer_mapping(df)

    # Garder une copie brute des noms choisis pour les colonnes clés
    col_id = mapping.contributor_id
    col_trans = mapping.transaction_id
    col_date = mapping.date
    col_amount = mapping.amount

    # Conversion de la date
    if col_date not in df.columns:
        raise KeyError(f"Colonne date introuvable ({col_date}). Vérifier le mapping.")
    df["date"] = pd.to_datetime(df[col_date], errors="coerce")

    # Conversion du montant
    if col_amount not in df.columns:
        raise KeyError(f"Colonne montant introuvable ({col_amount}). Vérifier le mapping.")
    df["montant"] = pd.to_numeric(df[col_amount], errors="coerce")

    # Nettoyage basique
    df = df.dropna(subset=["date", "montant"])
    df = df[df["montant"] > 0]

    # Enrichissement temporel
    df["annee"] = df["date"].dt.year
    df["mois"] = df["date"].dt.month
    df["trimestre"] = df["date"].dt.quarter
    df["jour_semaine"] = df["date"].dt.day_name(locale="fr_FR").fillna(df["date"].dt.day_name())
    df["saison"] = df["mois"].map(SEASONS_FR)

    # Géographie
    if mapping.country and mapping.country in df.columns:
        df["pays"] = df[mapping.country].astype(str).str.strip()
    if mapping.region and mapping.region in df.columns:
        df["region"] = df[mapping.region].astype(str).str.strip()
    if mapping.city and mapping.city in df.columns:
        df["ville"] = df[mapping.city].astype(str).str.strip()

    # Normaliser la devise
    df["devise"] = currency

    # Colonnes ID/transaction normalisées si disponibles
    if col_id in df.columns:
        df["id_contributeur"] = df[col_id].astype(str).str.strip()
    if col_trans in df.columns:
        df["id_transaction"] = df[col_trans].astype(str).str.strip()

    return df


def save_processed(df: pd.DataFrame, output_path: str | Path) -> None:
    """Sauvegarde les données enrichies en Parquet (recommandé) ou CSV selon l’extension."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.suffix.lower() in {".parquet"}:
        df.to_parquet(output_path, index=False)
    elif output_path.suffix.lower() in {".csv"}:
        df.to_csv(output_path, index=False)
    else:
        raise ValueError("Extension non supportée pour la sauvegarde (utiliser .parquet ou .csv).")


def build_basic_aggregations(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Construit des agrégations utiles pour l’analyse et le dashboard."""
    aggregations: dict[str, pd.DataFrame] = {}

    # Saisonnalité globale par mois
    aggregations["par_mois"] = (
        df.groupby(["annee", "mois"], as_index=False)["montant"].sum().sort_values(["annee", "mois"])
    )

    # Par saison
    if "saison" in df.columns:
        aggregations["par_saison"] = (
            df.groupby(["annee", "saison"], as_index=False)["montant"]
            .sum()
            .sort_values(["annee", "saison"])
        )

    # Par région
    if "region" in df.columns:
        aggregations["par_region"] = (
            df.groupby(["annee", "region"], as_index=False)["montant"]
            .sum()
            .sort_values(["annee", "region", "montant"], ascending=[True, True, False])
        )

    # Par ville
    if "ville" in df.columns:
        aggregations["par_ville"] = (
            df.groupby(["annee", "ville"], as_index=False)["montant"]
            .sum()
            .sort_values(["annee", "montant"], ascending=[True, False])
        )

    return aggregations


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Epuration & enrichissement des données de collecte de fonds."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Chemin vers le fichier brut (.xlsx ou .csv), ex: ~/Downloads/export.xlsx",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Chemin de sortie des données enrichies (.parquet ou .csv).",
    )
    parser.add_argument(
        "--sheet",
        required=False,
        help="Nom de la feuille Excel (si applicable).",
    )
    parser.add_argument(
        "--currency",
        default="FCFA",
        help="Devise des montants (par défaut: FCFA).",
    )

    args = parser.parse_args()

    raw_df = load_raw_data(args.input, sheet_name=args.sheet)
    df_clean = clean_and_enrich(raw_df, currency=args.currency)
    save_processed(df_clean, args.output)

    print(f"Données traitées sauvegardées dans: {args.output}")


if __name__ == "__main__":
    main()

