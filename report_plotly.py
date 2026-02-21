from __future__ import annotations

from pathlib import Path
import os

import numpy as np
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go


def load_data(path: str | Path) -> pd.DataFrame:
    # Gérer correctement le "~" (répertoire utilisateur)
    path = Path(os.path.expanduser(str(path)))
    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable: {path}")

    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)


def build_figures(df: pd.DataFrame) -> dict[str, go.Figure]:
    figs: dict[str, go.Figure] = {}
    template = "plotly_dark"

    # 1) Série temporelle mensuelle
    if {"annee", "mois", "montant"}.issubset(df.columns):
        df_ts = (
            df.groupby(["annee", "mois"], as_index=False)["montant"]
            .sum()
            .sort_values(["annee", "mois"])
        )
        df_ts["date_mois"] = pd.to_datetime(
            df_ts["annee"].astype(str) + "-" + df_ts["mois"].astype(str) + "-01",
            errors="coerce",
        )
        figs["time_series"] = px.line(
            df_ts,
            x="date_mois",
            y="montant",
            markers=True,
            title="Série temporelle des montants collectés",
            template=template,
            color_discrete_sequence=["#00E396"],
        ).update_layout(
            yaxis_title="Montant (FCFA)",
            xaxis_title="Date (mois)",
            hovermode="x unified",
        )

    # 2) Par saison
    if {"saison", "montant"}.issubset(df.columns):
        df_saison = (
            df.groupby("saison", as_index=False)["montant"]
            .sum()
            .sort_values("montant", ascending=False)
        )
        figs["by_season"] = px.bar(
            df_saison,
            x="saison",
            y="montant",
            title="Montants collectés par saison",
            template=template,
            color_discrete_sequence=["#008FFB"],
        ).update_layout(yaxis_title="Montant (FCFA)", xaxis_title="Saison")

    # 3) Catégories propres à ton export : status, type, provider, currency
    for col, title in [
        ("status", "Montants par status"),
        ("type", "Montants par type de transaction"),
        ("provider", "Montants par provider"),
        ("currency", "Montants par devise"),
    ]:
        if col in df.columns and "montant" in df.columns:
            df_cat = (
                df.groupby(col, as_index=False)["montant"]
                .sum()
                .sort_values("montant", ascending=False)
            )
            figs[f"by_{col}"] = px.bar(
                df_cat,
                x=col,
                y="montant",
                title=title,
                template=template,
                color_discrete_sequence=["#FEB019"],
            ).update_layout(yaxis_title="Montant (FCFA)", xaxis_title=col)

    # 4) Heatmap saisonnalité (année x mois)
    if {"annee", "mois", "montant"}.issubset(df.columns):
        df_hm = df.groupby(["annee", "mois"], as_index=False)["montant"].sum()
        pivot = df_hm.pivot(index="mois", columns="annee", values="montant").fillna(0)
        figs["heatmap"] = px.imshow(
            pivot,
            labels=dict(x="Année", y="Mois", color="Montant (FCFA)"),
            title="Heatmap : Montants collectés par mois et année (saisonnalité)",
            template=template,
            aspect="auto",
            color_continuous_scale="Teal",
        ).update_layout(yaxis=dict(tickvals=list(range(1, 13)), ticktext=["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sep", "Oct", "Nov", "Déc"]))

    # 5) Treemap hiérarchique (provider > status)
    if "provider" in df.columns and "status" in df.columns and "montant" in df.columns:
        df_treemap = df.groupby(["provider", "status"], as_index=False)["montant"].sum()
        figs["treemap"] = px.treemap(
            df_treemap,
            path=["provider", "status"],
            values="montant",
            title="Treemap : Répartition par provider et status (interactif)",
            template=template,
            color="montant",
            color_continuous_scale="Blues",
        ).update_traces(textinfo="label+value")

    # 6) Box plot - Distribution des montants par provider
    if "provider" in df.columns and "montant" in df.columns:
        top_prov = df.groupby("provider")["montant"].sum().nlargest(8).index.tolist()
        df_box = df[df["provider"].isin(top_prov)]
        figs["boxplot"] = px.box(
            df_box,
            x="provider",
            y="montant",
            title="Distribution des montants par provider (box plot)",
            template=template,
            points="outliers",
        ).update_layout(
            yaxis_title="Montant (FCFA)",
            xaxis_tickangle=-45,
            showlegend=False,
        )

    # 7) Histogramme - Distribution des montants
    if "montant" in df.columns:
        figs["histogram"] = px.histogram(
            df,
            x="montant",
            nbins=50,
            title="Distribution des montants de transaction (histogramme)",
            template=template,
        ).update_layout(
            xaxis_title="Montant (FCFA)",
            yaxis_title="Nombre de transactions",
            bargap=0.1,
        )

    # 8) Évolution temporelle par provider (stacked area)
    if {"annee", "mois", "montant", "provider"}.issubset(df.columns):
        df_stacked = df.groupby(["annee", "mois", "provider"], as_index=False)["montant"].sum()
        top_prov = df.groupby("provider")["montant"].sum().nlargest(5).index.tolist()
        df_stacked = df_stacked[df_stacked["provider"].isin(top_prov)]
        df_stacked["date_mois"] = pd.to_datetime(
            df_stacked["annee"].astype(str) + "-" + df_stacked["mois"].astype(str) + "-01",
            errors="coerce",
        )
        figs["stacked_area"] = px.area(
            df_stacked,
            x="date_mois",
            y="montant",
            color="provider",
            title="Évolution mensuelle par canal de paiement (top 5)",
            template=template,
        ).update_layout(yaxis_title="Montant (FCFA)", xaxis_title="Date", hovermode="x unified")

    # 9) Répartition jour de semaine
    if "jour_semaine" in df.columns and "montant" in df.columns:
        ordre_jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
        df_jour = df.groupby("jour_semaine", as_index=False)["montant"].sum()
        df_jour["jour_semaine"] = pd.Categorical(df_jour["jour_semaine"], categories=ordre_jours, ordered=True)
        df_jour = df_jour.sort_values("jour_semaine")
        figs["jour_semaine"] = px.bar(
            df_jour,
            x="jour_semaine",
            y="montant",
            title="Montants collectés par jour de semaine",
            template=template,
            color_discrete_sequence=["#8B5CF6"],
        ).update_layout(yaxis_title="Montant (FCFA)", xaxis_title="Jour")

    return figs


def compute_analytics(df: pd.DataFrame) -> dict:
    """Indicateurs d'analyse poussée : stats, tendances, concentration."""
    if "montant" not in df.columns:
        return {}
    m = df["montant"]
    out = {
        "médiane": m.median(),
        "moyenne": m.mean(),
        "écart_type": m.std(),
        "p90": m.quantile(0.9),
        "nb_transactions": len(df),
    }
    if "id_contributeur" in df.columns:
        contrib_totals = df.groupby("id_contributeur")["montant"].sum().sort_values(ascending=False)
        total = contrib_totals.sum()
        cumsum = contrib_totals.cumsum()
        # Top 10% contributeurs = X% du total
        top10_pct = int(len(contrib_totals) * 0.1) or 1
        pct_from_top10 = (cumsum.iloc[top10_pct - 1] / total * 100) if total > 0 else 0
        out["concentration_top10_pct"] = round(pct_from_top10, 1)
    if {"annee", "mois", "montant"}.issubset(df.columns):
        ts = df.groupby(["annee", "mois"])["montant"].sum()
        if len(ts) >= 2:
            last = ts.iloc[-1]
            prev = ts.iloc[-2]
            mom = ((last - prev) / prev * 100) if prev else 0
            out["croissance_mom_pct"] = round(mom, 1)
    if "status" in df.columns:
        completed = df[df["status"].str.upper().str.contains("COMPLET", na=False)]
        total_m = df["montant"].sum()
        completed_m = completed["montant"].sum()
        out["taux_completion_montant"] = round(completed_m / total_m * 100, 1) if total_m else 0
    return out


def save_dashboard_html(figs: dict[str, go.Figure], output_html: str | Path, df: pd.DataFrame) -> None:
    """Construit un dashboard HTML moderne (dark, responsive) avec KPI + grille de graphiques."""
    output_html = Path(output_html)
    output_html.parent.mkdir(parents=True, exist_ok=True)

    total = df["montant"].sum() if "montant" in df.columns else 0
    nb_transactions = len(df)
    nb_contributeurs = df["id_contributeur"].nunique() if "id_contributeur" in df.columns else None
    analytics = compute_analytics(df)

    # Structure HTML avec design moderne et grille responsive
    html_parts = [
        "<!DOCTYPE html>",
        "<html lang='fr'>",
        "<head>",
        "  <meta charset='utf-8'/>",
        "  <meta name='viewport' content='width=device-width, initial-scale=1'/>",
        "  <title>Dashboard Collecte de Fonds</title>",
        "  <style>",
        "    body { margin: 0; font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #050816; color: #f5f5f5; }",
        "    .page { max-width: 1280px; margin: 0 auto; padding: 24px 16px 48px; }",
        "    .header { display: flex; flex-direction: column; gap: 8px; margin-bottom: 24px; }",
        "    .title { font-size: 28px; font-weight: 700; }",
        "    .subtitle { font-size: 14px; color: #a1a1aa; }",
        "    .kpi-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px; }",
        "    .kpi-card { background: radial-gradient(circle at top left, #1f2937, #020617); border-radius: 16px; padding: 16px 18px; border: 1px solid rgba(148, 163, 184, 0.25); box-shadow: 0 18px 40px rgba(0,0,0,0.4); }",
        "    .kpi-label { font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; color: #9ca3af; margin-bottom: 6px; }",
        "    .kpi-value { font-size: 20px; font-weight: 600; }",
        "    .kpi-chip { display: inline-flex; align-items: center; gap: 4px; margin-top: 6px; padding: 2px 8px; border-radius: 999px; font-size: 11px; background: rgba(34,197,94,0.08); color: #4ade80; }",
        "    .grid { display: grid; grid-template-columns: minmax(0, 2.2fr) minmax(0, 1.5fr); gap: 20px; align-items: flex-start; }",
        "    @media (max-width: 960px) { .grid { grid-template-columns: minmax(0, 1fr); } }",
        "    .card { background: #020617; border-radius: 18px; padding: 12px 12px 4px; border: 1px solid rgba(31, 41, 55, 0.9); box-shadow: 0 18px 40px rgba(15,23,42,0.9); margin-bottom: 18px; }",
        "    .card-title { font-size: 14px; font-weight: 500; margin: 0 4px 4px; color: #e5e7eb; }",
        "    .fig-wrapper { width: 100%; }",
        "  </style>",
        "</head>",
        "<body>",
        "  <div class='page'>",
        "    <header class='header'>",
        "      <div class='title'>Vue d’ensemble collecte de fonds</div>",
        "      <div class='subtitle'>Suivi des performances de dons (FCFA), par période, statut, type et provider.</div>",
        "    </header>",
        "    <section class='kpi-row'>",
        f"      <div class='kpi-card'><div class='kpi-label'>Total collecté</div><div class='kpi-value'>{total:,.0f} FCFA</div><div class='kpi-chip'>KPI principal</div></div>",
        f"      <div class='kpi-card'><div class='kpi-label'>Nombre de transactions</div><div class='kpi-value'>{nb_transactions:,}</div></div>",
    ]

    if nb_contributeurs is not None:
        html_parts.append(
            f"      <div class='kpi-card'><div class='kpi-label'>Contributeurs uniques</div><div class='kpi-value'>{nb_contributeurs:,}</div></div>"
        )
    if analytics:
        if "médiane" in analytics:
            html_parts.append(f"      <div class='kpi-card'><div class='kpi-label'>Médiane transaction</div><div class='kpi-value'>{analytics['médiane']:,.0f} FCFA</div></div>")
        if "croissance_mom_pct" in analytics:
            mom = analytics["croissance_mom_pct"]
            color = "#4ade80" if mom >= 0 else "#f87171"
            html_parts.append(f"      <div class='kpi-card'><div class='kpi-label'>Croissance MoM</div><div class='kpi-value' style='color:{color}'>{mom:+.1f} %</div></div>")
        if "concentration_top10_pct" in analytics:
            html_parts.append(f"      <div class='kpi-card'><div class='kpi-label'>Top 10% contrib. = % total</div><div class='kpi-value'>{analytics['concentration_top10_pct']} %</div></div>")
        if "taux_completion_montant" in analytics:
            html_parts.append(f"      <div class='kpi-card'><div class='kpi-label'>Taux completion (montant)</div><div class='kpi-value'>{analytics['taux_completion_montant']} %</div></div>")

    html_parts.extend(
        [
            "    </section>",
            "    <section class='grid'>",
            "      <div>",
        ]
    )

    # Colonne gauche : série temporelle (si présente)
    if "time_series" in figs:
        html_parts.append("        <div class='card'>")
        html_parts.append("          <h3 class='card-title'>Evolution temporelle des montants</h3>")
        html_parts.append("          <div class='fig-wrapper'>")
        html_parts.append(figs["time_series"].to_html(full_html=False, include_plotlyjs="cdn"))
        html_parts.append("          </div>")
        html_parts.append("        </div>")

    html_parts.append("      </div>")  # fin colonne gauche

    # Colonne droite : saison + catégories
    html_parts.append("      <div>")

    if "by_season" in figs:
        html_parts.append("        <div class='card'>")
        html_parts.append("          <h3 class='card-title'>Répartition saisonnière</h3>")
        html_parts.append("          <div class='fig-wrapper'>")
        html_parts.append(figs["by_season"].to_html(full_html=False, include_plotlyjs=False))
        html_parts.append("          </div>")
        html_parts.append("        </div>")

    for key in ["by_status", "by_type", "by_provider", "by_currency"]:
        if key in figs:
            title = figs[key].layout.title.text or ""
            html_parts.append("        <div class='card'>")
            html_parts.append(f"          <h3 class='card-title'>{title}</h3>")
            html_parts.append("          <div class='fig-wrapper'>")
            html_parts.append(figs[key].to_html(full_html=False, include_plotlyjs=False))
            html_parts.append("          </div>")
            html_parts.append("        </div>")

    html_parts.append("      </div>")
    html_parts.append("    </section>")

    # Section Analyse poussée
    html_parts.append("    <section class='header'><div class='title'>Analyse poussée</div><div class='subtitle'>Visualisations interactives et indicateurs statistiques.</div></section>")
    html_parts.append("    <section class='grid'>")
    html_parts.append("      <div>")

    for key in ["heatmap", "stacked_area", "boxplot", "histogram"]:
        if key in figs:
            title = figs[key].layout.title.text or ""
            html_parts.append("        <div class='card'>")
            html_parts.append(f"          <h3 class='card-title'>{title}</h3>")
            html_parts.append("          <div class='fig-wrapper'>")
            html_parts.append(figs[key].to_html(full_html=False, include_plotlyjs=False))
            html_parts.append("          </div>")
            html_parts.append("        </div>")

    html_parts.append("      </div>")
    html_parts.append("      <div>")

    for key in ["treemap", "jour_semaine"]:
        if key in figs:
            title = figs[key].layout.title.text or ""
            html_parts.append("        <div class='card'>")
            html_parts.append(f"          <h3 class='card-title'>{title}</h3>")
            html_parts.append("          <div class='fig-wrapper'>")
            html_parts.append(figs[key].to_html(full_html=False, include_plotlyjs=False))
            html_parts.append("          </div>")
            html_parts.append("        </div>")

    if analytics:
        stats_html = "        <div class='card'><h3 class='card-title'>Indicateurs statistiques</h3><div class='kpi-row' style='margin:0'>"
        if "moyenne" in analytics:
            stats_html += f"<div class='kpi-card' style='flex:1'><div class='kpi-label'>Moyenne</div><div class='kpi-value'>{analytics['moyenne']:,.0f} FCFA</div></div>"
        if "écart_type" in analytics:
            stats_html += f"<div class='kpi-card' style='flex:1'><div class='kpi-label'>Écart-type</div><div class='kpi-value'>{analytics['écart_type']:,.0f}</div></div>"
        if "p90" in analytics:
            stats_html += f"<div class='kpi-card' style='flex:1'><div class='kpi-label'>Percentile 90</div><div class='kpi-value'>{analytics['p90']:,.0f} FCFA</div></div>"
        stats_html += "</div></div>"
        html_parts.append(stats_html)

    html_parts.extend(
        [
            "      </div>",
            "    </section>",
            "  </div>",
            "</body>",
            "</html>",
        ]
    )

    output_html.write_text("\n".join(html_parts), encoding="utf-8")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Génère un rapport interactif Plotly (HTML) à partir des données traitées."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Chemin vers le fichier de données enrichies (.parquet ou .csv), ex: data/processed.parquet",
    )
    parser.add_argument(
        "--output_html",
        default="reports/dashboard_plotly.html",
        help="Chemin du fichier HTML de sortie (par défaut: reports/dashboard_plotly.html).",
    )

    args = parser.parse_args()

    df = load_data(args.input)
    figs = build_figures(df)
    if not figs:
        raise RuntimeError("Aucune figure générée (colonnes attendues manquantes dans les données).")

    save_dashboard_html(figs, args.output_html, df)
    print(f"Dashboard Plotly généré dans: {args.output_html}")


if __name__ == "__main__":
    main()

