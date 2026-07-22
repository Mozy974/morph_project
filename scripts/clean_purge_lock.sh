#!/usr/bin/env bash
# Script d'automatisation SRE : Déblocage du verrou de purge RGPD
set -e

LOCK_FILE="/tmp/intent_classifier_purge.lock"

echo "🔍 Vérification du verrou de purge RGPD..."

if [ -f "$LOCK_FILE" ]; then
    echo "⚠️ Verrou trouvé sur $LOCK_FILE. Suppression en cours..."
    rm -f "$LOCK_FILE"
    echo "✅ Verrou de purge réinitialisé avec succès !"
else
    echo "ℹ️ Aucun verrou actif trouvé. Le système est prêt."
fi
