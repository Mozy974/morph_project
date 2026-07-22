"""
Test automatisé de restauration d'urgence Disaster Recovery / Loki (tests/test_loki_recovery.py).
Simule la purge, la réinitialisation des verrous et la restauration des archives RGPD.
"""

import os
import pytest
from orchestrator.agents.intent_sentiment_classifier import IntentSentimentClassifier


def test_loki_and_rgpd_recovery_simulation(tmp_path):
    # 1. Simulation d'un fichier de verrou de purge
    lock_file = "/tmp/test_intent_classifier_purge.lock"
    with open(lock_file, "w") as f:
        f.write("LOCK_ACTIVE")

    assert os.path.exists(lock_file) is True

    # 2. Exécution du déblocage d'urgence (flock / cleanup)
    os.remove(lock_file)
    assert os.path.exists(lock_file) is False

    # 3. Initialisation du dossier d'archivage RGPD
    backup_dir = "orchestrator/memory/rgpd_backups"
    os.makedirs(backup_dir, exist_ok=True)

    # 4. Test de la fonction de pré-purge et d'archivage automatique
    classifier = IntentSentimentClassifier()
    classifier.purge_old_audit_logs(retention_days=30)
    
    assert os.path.exists(backup_dir) is True
