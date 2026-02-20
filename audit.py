from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd


def detect_duplicate_transactions(
    df: pd.DataFrame,
    id_transaction_col: str = "id_transaction",
    contributor_col: str = "id_contributeur",
    amount_col: str = "montant",
    date_col: str = "date",
) -> pd.DataFrame:
    """
    Détecte les transactions potentiellement en double.

    - Doublons stricts sur l'ID de transaction.
    - Doublons "fortement suspects" sur (id_contributeur, date, montant).
    """
    flags = []

    # Doublons stricts sur l'ID transaction
    if id_transaction_col in df.columns:
        dup_trans_id = df[df.duplicated(id_transaction_col, keep=False)].copy()
        dup_trans_id["raison_suspicion"] = "ID_TRANSACTION_DUPLIQUE"
        flags.append(dup_trans_id)

    # Doublons sur (contributeur, date, montant)
    for col in [contributor_col, date_col, amount_col]:
        if col not in df.columns:
            break
    else:
        subset_cols = [contributor_col, date_col, amount_col]
        dup_triplet = df[df.duplicated(subset_cols, keep=False)].copy()
        dup_triplet["raison_suspicion"] = dup_triplet.get(
            "raison_suspicion", ""
        ) + ";TRIPLET_CONTRIB_DATE_MONTANT"
        flags.append(dup_triplet)

    if not flags:
        return pd.DataFrame(columns=df.columns.tolist() + ["raison_suspicion"])

    suspicious = pd.concat(flags, ignore_index=True).drop_duplicates()
    return suspicious


def detect_anomalies_amounts(
    df: pd.DataFrame,
    amount_col: str = "montant",
    zscore_threshold: float = 4.0,
) -> pd.DataFrame:
    """
    Détecte les montants extrêmes à l’aide d’un Z-score simple.
    Peut mettre en avant des erreurs de saisie ou des fraudes potentielles.
    """
    if amount_col not in df.columns:
        return pd.DataFrame(columns=df.columns.tolist() + ["zscore_montant"])

    series = df[amount_col].astype(float)
    mean = series.mean()
    std = series.std(ddof=0)

    if std == 0 or pd.isna(std):
        return pd.DataFrame(columns=df.columns.tolist() + ["zscore_montant"])

    zscores = (series - mean) / std
    mask = zscores.abs() >= zscore_threshold

    anomalies = df.loc[mask].copy()
    anomalies["zscore_montant"] = zscores[mask]
    return anomalies


def detect_inconsistent_dates(
    df: pd.DataFrame,
    date_col: str = "date",
    min_year: int = 2000,
    max_year: Optional[int] = None,
) -> pd.DataFrame:
    """
    Détecte les dates incohérentes (trop anciennes, dans le futur, etc.).
    """
    if date_col not in df.columns:
        return pd.DataFrame(columns=df.columns.tolist() + ["motif_incoherence"])

    if max_year is None:
        max_year = pd.Timestamp.today().year + 1

    dates = pd.to_datetime(df[date_col], errors="coerce")
    mask_invalid = dates.dt.year.lt(min_year) | dates.dt.year.gt(max_year)

    invalid = df.loc[mask_invalid].copy()
    invalid["motif_incoherence"] = "ANNEE_HORS_PLAGE"
    return invalid


def run_audit_checks(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Exécute l’ensemble des contrôles d’audit et retourne les résultats par type."""
    return {
        "doublons_transactions": detect_duplicate_transactions(df),
        "montants_anormaux": detect_anomalies_amounts(df),
        "dates_incoherentes": detect_inconsistent_dates(df),
    }


def save_audit_reports(reports: dict[str, pd.DataFrame], output_dir: str | Path) -> None:
    """Sauvegarde les rapports d’audit au format CSV dans un répertoire donné."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for name, report_df in reports.items():
        report_path = output_dir / f"{name}.csv"
        if not report_df.empty:
            report_df.to_csv(report_path, index=False)
        else:
            # Créer un fichier vide avec un message explicite
            empty_df = pd.DataFrame({"info": [f"Aucune anomalie détectée pour: {name}"]})
            empty_df.to_csv(report_path, index=False)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Contrôles d’audit sur les données de dons.")
    parser.add_argument(
        "--input",
        required=True,
        help="Chemin vers le fichier de données enrichies (.parquet ou .csv).",
    )
    parser.add_argument(
        "--output_dir",
        required=True,
        help="Répertoire de sortie pour les rapports d’audit (CSV).",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Fichier introuvable: {input_path}")

    if input_path.suffix.lower() == ".parquet":
        df = pd.read_parquet(input_path)
    else:
        df = pd.read_csv(input_path)

    reports = run_audit_checks(df)
    save_audit_reports(reports, args.output_dir)

    print(f"Rapports d’audit générés dans: {args.output_dir}")


if __name__ == "__main__":
    main()

