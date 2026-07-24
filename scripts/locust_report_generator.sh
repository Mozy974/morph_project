#!/bin/bash
# Script pour exécuter Locust et générer des rapports automatiquement (scripts/locust_report_generator.sh)

echo "🚀 Lancement du générateur de rapports Locust..."

mkdir -p reports screenshots

if ! command -v locust &> /dev/null; then
    echo "❌ Locust non installé. Installation en cours..."
    pip install locust
fi

LOCUST_FILE="locustfile.py"
if [ ! -f "$LOCUST_FILE" ]; then
    LOCUST_FILE="locust/locustfile.py"
fi

TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
echo "📊 Lancement du benchmark Locust (100 utilisateurs, 15 sec)..."
locust -f "$LOCUST_FILE" \
    --headless \
    -u 100 \
    -r 20 \
    --host=http://localhost:8000 \
    --run-time=15s \
    --html=reports/locust_report_${TIMESTAMP}.html \
    --csv=reports/locust_metrics_${TIMESTAMP}.csv || true

echo "✅ Rapport Locust généré avec succès dans reports/"
