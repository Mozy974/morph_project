#!/bin/bash
# ==============================================================================
# Script de déploiement — SuperAgent Morph sur serveur distant
# Usage :
#   ./scripts/deploy_remote.sh 100.73.157.127 [user] [ssh_key_path]
#
# Prérequis sur le serveur distant :
#   - Docker & Docker Compose installés
#   - Git (optionnel)
#   - Ports 8000, 9091, 3001, 5432, 6379 libres
# ==============================================================================
set -euo pipefail

REMOTE_HOST="${1:?Usage: $0 <host> [user] [ssh_key]}"
REMOTE_USER="${2:-root}"
SSH_KEY="${3:-}"
REMOTE_DIR="/opt/morph"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Clé SSH optionnelle
SSH_CMD="ssh"
if [ -n "$SSH_KEY" ]; then
    SSH_CMD="ssh -i $SSH_KEY"
    SCP_CMD="scp -i $SSH_KEY"
else
    SCP_CMD="scp"
fi

echo "=============================================="
echo "  🚀 Déploiement SuperAgent Morph"
echo "  Cible : $REMOTE_USER@$REMOTE_HOST"
echo "  Répertoire : $REMOTE_DIR"
echo "=============================================="

# 1. Vérifier la connexion SSH
echo ""
echo "📡 Étape 1/5 : Vérification de la connexion SSH..."
if ! $SSH_CMD "$REMOTE_USER@$REMOTE_HOST" "echo OK" 2>/dev/null; then
    echo "❌ Connexion SSH échouée vers $REMOTE_USER@$REMOTE_HOST"
    echo "   Vérifie :"
    echo "   - que le serveur est joignable (ping $REMOTE_HOST)"
    echo "   - que SSH est installé (port 22)"
    echo "   - que la clé publique est autorisée"
    exit 1
fi
echo "   ✅ Connexion SSH OK"

# 2. Vérifier les prérequis sur le serveur distant
echo ""
echo "🔧 Étape 2/5 : Vérification des prérequis distants..."
$SSH_CMD "$REMOTE_USER@$REMOTE_HOST" bash -s << 'PREREQS'
    MISSING=""
    command -v docker >/dev/null 2>&1 || MISSING="$MISSING docker"
    command -v docker compose >/dev/null 2>&1 || MISSING="$MISSING docker-compose"
    if [ -n "$MISSING" ]; then
        echo "❌ Manquant sur le serveur :$MISSING"
        echo "   Installe-les avec :"
        echo "   curl -fsSL https://get.docker.com | sh"
        exit 1
    fi
    echo "   ✅ Docker: $(docker --version)"
    echo "   ✅ Compose: $(docker compose version)"
PREREQS

# 3. Créer le répertoire distant et copier les fichiers
echo ""
echo "📦 Étape 3/5 : Copie des fichiers vers le serveur distant..."
$SSH_CMD "$REMOTE_USER@$REMOTE_HOST" "mkdir -p $REMOTE_DIR"

# Copier les fichiers essentiels (exclure les lourds inutiles)
rsync -avz --delete \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='orchestrator/memory/checkpoints/*.json' \
    --exclude='orchestrator/memory/backups/*.json' \
    --exclude='node_modules' \
    --exclude='.venv' \
    -e "$SSH_CMD" \
    "$PROJECT_DIR/" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/"

echo "   ✅ Fichiers copiés"

# 4. Configurer l'environnement
echo ""
echo "🔐 Étape 4/5 : Configuration de l'environnement..."
$SSH_CMD "$REMOTE_USER@$REMOTE_HOST" bash -s << ENV
    cd $REMOTE_DIR
    # Créer le .env si absent
    if [ ! -f .env ]; then
        cat > .env << 'EOF'
MISTRAL_API_KEY=
TAVILY_API_KEY=
EOF
        echo "   ✅ .env créé (clés API vides — à remplir si besoin)"
    else
        echo "   ✅ .env existant"
    fi
ENV

# 5. Lancer les conteneurs
echo ""
echo "🐳 Étape 5/5 : Démarrage des conteneurs Docker..."
$SSH_CMD "$REMOTE_USER@$REMOTE_HOST" bash -s << DEPLOY
    cd $REMOTE_DIR
    echo "   Build des images..."
    docker compose build api celery_worker 2>&1 | tail -3
    echo "   Démarrage des services..."
    docker compose up -d 2>&1
    echo ""
    echo "   Attente de la disponibilité..."
    sleep 10
    docker compose ps --format "table {{.Name}}\t{{.State}}\t{{.Ports}}"
DEPLOY

echo ""
echo "=============================================="
echo "  ✅ Déploiement terminé !"
echo "=============================================="
echo ""
echo "  Accès :"
echo "    API        → http://$REMOTE_HOST:8000"
echo "    Dashboard  → http://$REMOTE_HOST:8000/app"
echo "    Prometheus → http://$REMOTE_HOST:9091"
echo "    Grafana    → http://$REMOTE_HOST:3001 (admin/superagent)"
echo ""
echo "  Commandes utiles :"
echo "    Voir les logs :  ssh $REMOTE_USER@$REMOTE_HOST 'cd $REMOTE_DIR && docker compose logs -f'"
echo "    Redémarrer :     ssh $REMOTE_USER@$REMOTE_HOST 'cd $REMOTE_DIR && docker compose restart'"
echo "    Arrêter :        ssh $REMOTE_USER@$REMOTE_HOST 'cd $REMOTE_DIR && docker compose down'"
echo "    Smoke test :     ssh $REMOTE_USER@$REMOTE_HOST 'cd $REMOTE_DIR && python3 scripts/smoke_test.py --quick'"
echo ""
