#!/bin/bash
# Script d'initialisation Ollama — télécharge le modèle au premier démarrage
# Exécuté automatiquement par le conteneur Ollama

set -e

echo "[Ollama Init] 🚀 Démarrage du serveur Ollama..."
ollama serve &

# Attendre que le serveur soit prêt
echo "[Ollama Init] ⏳ Attente du serveur..."
for i in $(seq 1 30); do
    if ollama list > /dev/null 2>&1; then
        echo "[Ollama Init] ✅ Serveur prêt !"
        break
    fi
    sleep 2
done

# Modèles à pré-télécharger (modèle par défaut pour Morph)
MODELS="mistral:7b"

for MODEL in $MODELS; do
    if ! ollama list 2>/dev/null | grep -q "$MODEL"; then
        echo "[Ollama Init] 📥 Téléchargement du modèle $MODEL..."
        ollama pull "$MODEL"
        echo "[Ollama Init] ✅ Modèle $MODEL prêt !"
    else
        echo "[Ollama Init] ✅ Modèle $MODEL déjà présent."
    fi
done

# Garder le processus en vie
wait
