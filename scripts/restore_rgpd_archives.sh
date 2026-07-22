#!/usr/bin/env bash
# Script d'automatisation PRA : Vérification et restauration des archives d'audit RGPD
set -e

BACKUP_DIR="${1:-/var/lib/rgpd_backups}"

echo "📦 Inspection du répertoire d'archivage RGPD : $BACKUP_DIR"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "⚠️ Le répertoire $BACKUP_DIR n'existe pas. Tentative sur l'emplacement local..."
    BACKUP_DIR="./orchestrator/memory/rgpd_backups"
fi

if [ -d "$BACKUP_DIR" ]; then
    echo "✅ Répertoire d'archives trouvé. Fichiers de sauvegarde :"
    ls -lh "$BACKUP_DIR"/*.json 2>/dev/null || echo "Aucune archive JSON trouvée."
else
    echo "❌ Aucun répertoire de sauvegarde valide trouvé."
    exit 1
fi
