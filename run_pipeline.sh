#!/usr/bin/env bash
# Pipeline data batch : épuration → audit → dashboard
# Usage: ./run_pipeline.sh [chemin_export.xlsx]

set -e
INPUT="${1:-}"
OUTPUT_CSV="data/processed.csv"
AUDIT_DIR="audit_reports"
DASHBOARD_HTML="reports/dashboard_plotly.html"

echo "=== Pipeline Data - Plateforme Collecte de Fonds ==="

if [ -n "$INPUT" ]; then
  echo "[1/3] Epuration des donnees..."
  python data_processing.py --input "$INPUT" --output "$OUTPUT_CSV"
else
  if [ ! -f "$OUTPUT_CSV" ]; then
    echo "Erreur: Pas de fichier $OUTPUT_CSV. Lancez avec: ./run_pipeline.sh ~/Downloads/export.xlsx"
    exit 1
  fi
  echo "[1/3] Utilisation des donnees existantes: $OUTPUT_CSV"
fi

echo "[2/3] Controles d'audit (Audit Logs, detection doublons/anomalies)..."
python audit.py --input "$OUTPUT_CSV" --output_dir "$AUDIT_DIR"

echo "[3/3] Generation du dashboard KPI..."
python report_plotly.py --input "$OUTPUT_CSV" --output_html "$DASHBOARD_HTML"

echo ""
echo "=== Pipeline termine ==="
echo "- Donnees: $OUTPUT_CSV"
echo "- Rapports audit: $AUDIT_DIR/"
echo "- Dashboard: $DASHBOARD_HTML"
echo "Ouvrir: open $DASHBOARD_HTML"
