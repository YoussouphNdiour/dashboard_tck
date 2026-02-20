from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


def load_data(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        st.error(f"Fichier introuvable: {path}")
        return pd.DataFrame()

    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)


def kpi_cards(df: pd.DataFrame):
    total = df["montant"].sum()
    nb_transactions = len(df)
    nb_contributeurs = df["id_contributeur"].nunique() if "id_contributeur" in df.columns else np.nan

    col1, col2, col3 = st.columns(3)
    col1.metric("Total collecté", f"{total:,.0f} FCFA".replace(",", " "))
    col2.metric("Nombre de transactions", f"{nb_transactions:,}".replace(",", " "))
    if not np.isnan(nb_contributeurs):
        col3.metric("Nombre de contributeurs uniques", f"{nb_contributeurs:,}".replace(",", " "))


def filters_sidebar(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filtres")

    if "annee" in df.columns:
        years = sorted(df["annee"].dropna().unique().tolist())
        selected_years = st.sidebar.multiselect("Années", years, default=years)
        if selected_years:
            df = df[df["annee"].isin(selected_years)]

    if "saison" in df.columns:
        seasons = sorted(df["saison"].dropna().unique().tolist())
        selected_seasons = st.sidebar.multiselect("Saisons", seasons, default=seasons)
        if selected_seasons:
            df = df[df["saison"].isin(selected_seasons)]

    if "region" in df.columns:
        regions = sorted(df["region"].dropna().unique().tolist())
        selected_regions = st.sidebar.multiselect("Régions", regions, default=regions)
        if selected_regions:
            df = df[df["region"].isin(selected_regions)]

    if "ville" in df.columns:
        villes = sorted(df["ville"].dropna().unique().tolist())
        selected_villes = st.sidebar.multiselect("Villes", villes, default=villes)
        if selected_villes:
            df = df[df["ville"].isin(selected_villes)]

    return df


def plot_time_series(df: pd.DataFrame):
    if not {"annee", "mois", "montant"}.issubset(df.columns):
        return

    df_ts = (
        df.groupby(["annee", "mois"], as_index=False)["montant"].sum().sort_values(["annee", "mois"])
    )
    df_ts["date_mois"] = pd.to_datetime(
        df_ts["annee"].astype(str) + "-" + df_ts["mois"].astype(str) + "-01", errors="coerce"
    )

    fig = px.line(
        df_ts,
        x="date_mois",
        y="montant",
        markers=True,
        title="Série temporelle des montants collectés",
    )
    fig.update_layout(yaxis_title="Montant (FCFA)", xaxis_title="Date (mois)")
    st.plotly_chart(fig, use_container_width=True)


def plot_by_region(df: pd.DataFrame):
    if "region" not in df.columns:
        return

    df_reg = df.groupby("region", as_index=False)["montant"].sum().sort_values("montant", ascending=False)
    fig = px.bar(
        df_reg,
        x="region",
        y="montant",
        title="Montants collectés par région",
    )
    fig.update_layout(yaxis_title="Montant (FCFA)", xaxis_title="Région")
    st.plotly_chart(fig, use_container_width=True)


def plot_by_season(df: pd.DataFrame):
    if "saison" not in df.columns:
        return

    df_sai = df.groupby("saison", as_index=False)["montant"].sum().sort_values("montant", ascending=False)
    fig = px.bar(
        df_sai,
        x="saison",
        y="montant",
        title="Montants collectés par saison",
    )
    fig.update_layout(yaxis_title="Montant (FCFA)", xaxis_title="Saison")
    st.plotly_chart(fig, use_container_width=True)


def plot_by_category(df: pd.DataFrame, column: str, title: str):
    """Générique Plotly pour les colonnes catégorielles de ton export (status, type, provider, currency)."""
    if column not in df.columns:
        return

    df_cat = (
        df.groupby(column, as_index=False)["montant"].sum().sort_values("montant", ascending=False)
    )
    fig = px.bar(
        df_cat,
        x=column,
        y="montant",
        title=title,
    )
    fig.update_layout(yaxis_title="Montant (FCFA)", xaxis_title=column)
    st.plotly_chart(fig, use_container_width=True)


def main():
    st.set_page_config(page_title="Tableau de bord Collecte de Fonds", layout="wide")

    st.title("Plateforme d’analyse de collecte de fonds")
    st.write(
        "Suivi interactif des montants collectés (FCFA), par période et par zone géographique."
    )

    st.sidebar.subheader("Source de données")
    default_path = "data/processed.parquet"
    data_path = st.sidebar.text_input(
        "Chemin du fichier de données enrichies (.parquet ou .csv)",
        value=default_path,
    )

    df = load_data(data_path)
    if df.empty:
        st.stop()

    df = filters_sidebar(df)

    kpi_cards(df)

    st.markdown("---")
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("Evolution temporelle")
        plot_time_series(df)

    with col_right:
        st.subheader("Répartition et segmentation")
        # Si un jour tu ajoutes pays/région/ville dans ton export
        plot_by_region(df)
        plot_by_season(df)
        # Colonnes de ton export actuel
        plot_by_category(df, "status", "Montants par status")
        plot_by_category(df, "type", "Montants par type de transaction")
        plot_by_category(df, "provider", "Montants par provider")
        plot_by_category(df, "currency", "Montants par devise")

    st.markdown("---")
    with st.expander("Voir les données brutes filtrées"):
        st.dataframe(df.head(500))


if __name__ == "__main__":
    main()

