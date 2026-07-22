"""
Moteur de Checkpointing et de Sauvegarde d'État Persistant (Redis + Fallback Local).
Permet la persistance et la reprise transparente du SuperAgent après crash/interruption.
"""

import os
import json
from typing import Optional, Dict, Any
from orchestrator.state import SuperAgentState

CHECKPOINTS_DIR = os.path.join(os.path.dirname(__file__), "checkpoints")

# Essai de connexion à Redis si disponible
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
redis_client = None

try:
    import redis
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
    print("[RedisCheckpointSaver] 🔌 Connexion Redis active pour les checkpoints !")
except Exception:
    redis_client = None
    print("[RedisCheckpointSaver] ℹ️ Redis non accessible directement. Mode fallback fichier local activé.")


class RedisCheckpointSaver:
    """
    Sauvegarde l'état du SuperAgent (`SuperAgentState`) après chaque transition de nœud.
    """
    def __init__(self, ttl_seconds: int = 604800):  # 7 jours
        self.ttl = ttl_seconds
        os.makedirs(CHECKPOINTS_DIR, exist_ok=True)

    def save_checkpoint(self, job_id: str, state: SuperAgentState) -> None:
        """
        Sauvegarde l'état du graphe sous la clé `checkpoint:{job_id}`.
        """
        if not job_id:
            return

        state_dict = state.to_dict()
        serialized = json.dumps(state_dict, ensure_ascii=False)

        # 1. Sauvegarde dans Redis si disponible
        if redis_client:
            try:
                redis_client.setex(f"checkpoint:{job_id}", self.ttl, serialized)
                print(f"[RedisCheckpointSaver] 💾 Checkpoint Redis sauvegardé pour '{job_id}' (Nœud: {state.last_completed_node})")
            except Exception as e:
                print(f"[RedisCheckpointSaver] ⚠️ Erreur sauvegarde Redis : {e}")

        # 2. Sauvegarde miroir dans un fichier local pour sécurité accrue
        filepath = os.path.join(CHECKPOINTS_DIR, f"{job_id}.json")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(serialized)
            print(f"[RedisCheckpointSaver] 📁 Checkpoint fichier sauvegardé : '{job_id}.json'")
        except Exception as e:
            print(f"[RedisCheckpointSaver] ⚠️ Erreur sauvegarde fichier local : {e}")

    def get_checkpoint(self, job_id: str) -> Optional[SuperAgentState]:
        """
        Récupère le dernier état connu pour le `job_id`.
        """
        if not job_id:
            return None

        # 1. Tentative via Redis
        if redis_client:
            try:
                data = redis_client.get(f"checkpoint:{job_id}")
                if data:
                    print(f"[RedisCheckpointSaver] 🔄 Checkpoint chargé depuis Redis pour '{job_id}' !")
                    return SuperAgentState.from_dict(json.loads(data))
            except Exception as e:
                print(f"[RedisCheckpointSaver] ⚠️ Erreur lecture Redis : {e}")

        # 2. Fallback via fichier local
        filepath = os.path.join(CHECKPOINTS_DIR, f"{job_id}.json")
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    print(f"[RedisCheckpointSaver] 🔄 Checkpoint chargé depuis fichier local pour '{job_id}' !")
                    return SuperAgentState.from_dict(data)
            except Exception as e:
                print(f"[RedisCheckpointSaver] ⚠️ Erreur lecture fichier local : {e}")

        return None

    def has_checkpoint(self, job_id: str) -> bool:
        """
        Vérifie si un checkpoint existe pour ce `job_id`.
        """
        return self.get_checkpoint(job_id) is not None
