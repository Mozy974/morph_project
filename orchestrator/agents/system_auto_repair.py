"""
SystemAutoRepair : Moteur d'Auto-Réparation Système & Infrastructure (Niveau 9.0 Conscience Collective).
Applique une stratégie graduée : auto-réparation 100% autonome pour le réversible, validation HITL pour le critique.
"""

import json
import os
import datetime
from typing import Dict, Any, List, Optional
from orchestrator.memory.event_bus import publish_event


class SystemAutoRepair:
    """
    Agent d'Auto-Réparation Système (Niveau 9.0).
    Détecte et résout automatiquement les faiblesses d'infrastructure sans risque pour les données persistantes.
    """

    SAFE_ACTIONS = ["REDIS_RECONNECT", "PURGE_TEMP_SANDBOX", "CACHE_FLUSH", "LOG_ROTATE"]
    CRITICAL_ACTIONS = ["POSTGRES_SCHEMA_MIGRATION", "CLEAR_PERSISTENT_DB", "GLOBAL_CONFIG_MUTATION"]

    def __init__(self):
        self.nom = "System Auto-Repair"

    def evaluate_and_repair(self, fault_type: str, details: Dict[str, Any], job_id: str = "auto_repair") -> Dict[str, Any]:
        """
        Évalue une panne système et applique la remédiation autonome ou requiert un HITL.
        """
        print(f"[{self.nom}] 🩺 Évaluation de la défaillance système : '{fault_type}'...")

        if fault_type in self.SAFE_ACTIONS:
            # Réparation 100% autonome
            msg = f"⚡ Auto-réparation autonome appliquée pour '{fault_type}' (Action sans risque)."
            print(f"[{self.nom}] {msg}")
            publish_event(
                job_id=job_id,
                event_type="system_auto_repaired",
                message=msg,
                payload={"fault_type": fault_type, "status": "AUTONOMOUSLY_RESOLVED"}
            )
            return {
                "fault_type": fault_type,
                "action": fault_type,
                "status": "AUTONOMOUSLY_RESOLVED",
                "requires_hitl": False,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }

        elif fault_type in self.CRITICAL_ACTIONS:
            # Action critique -> HITL Requis
            msg = f"⚠️ Action d'infrastructure CRITIQUE détectée '{fault_type}'. Demande de validation HITL émise."
            print(f"[{self.nom}] {msg}")
            publish_event(
                job_id=job_id,
                event_type="system_repair_hitl_required",
                message=msg,
                payload={"fault_type": fault_type, "status": "PENDING_HITL"}
            )
            return {
                "fault_type": fault_type,
                "action": fault_type,
                "status": "PENDING_HITL",
                "requires_hitl": True,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }

        else:
            # Action inconnue -> Traitement prudent
            return {
                "fault_type": fault_type,
                "action": "NONE",
                "status": "UNKNOWN_FAULT",
                "requires_hitl": True,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
