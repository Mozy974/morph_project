"""
FleetEthicsConsensus : Moteur d'Éthique par Consensus de Flotte & Droit de Veto (Niveau 12.0 Conscience Collective Ultime).
Calcule le consensus éthique de la flotte tout en imposant un VETO UNILATÉRAL ABSOLU si un invariant de sécurité est menacé.
"""

import json
from typing import Dict, Any, List, Optional
from orchestrator.memory.event_bus import publish_event


class FleetEthicsConsensus:
    """
    Consensus Éthique de Flotte (Niveau 12.0).
    Règle du Veto Unilatéral : Tout agent de sécurité qui détecte une violation bloque immédiatement la transaction.
    """

    INVIOLABLE_INVARIANTS = [
        "NO_CREDENTIAL_LEAKAGE",
        "NO_MALICIOUS_CODE_INJECTION",
        "NO_UNAUTHENTICATED_DATA_DESTRUCTION"
    ]

    def __init__(self):
        self.nom = "Fleet Ethics Consensus Engine"

    def evaluate_fleet_consensus(
        self,
        agent_audit_reports: List[Dict[str, Any]],
        job_id: str = "ethics_consensus"
    ) -> Dict[str, Any]:
        """
        Évalue le consensus éthique de la flotte et applique la règle du veto unilatéral.
        """
        print(f"[{self.nom}] ⚖️ Évaluation du consensus éthique de la flotte ({len(agent_audit_reports)} rapports audités)...")

        # 1. Vérification du droit de veto unilatéral pour Invariant
        for report in agent_audit_reports:
            flagged = report.get("flagged_invariant")
            agent_name = report.get("agent_name", "Auditeur Anonyme")

            if flagged in self.INVIOLABLE_INVARIANTS:
                msg = f"⛔ VETO UNILATÉRAL ÉMIT PAR '{agent_name}' ! Invariant inviolable menacé : {flagged}. Blocage absolu !"
                print(f"[{self.nom}] {msg}")

                publish_event(
                    job_id=job_id,
                    event_type="fleet_ethics_unilateral_veto",
                    message=msg,
                    payload={"veto_by": agent_name, "invariant": flagged, "status": "BLOCKED_BY_VETO"}
                )

                return {
                    "consensus_approved": False,
                    "veto_applied": True,
                    "veto_by": agent_name,
                    "flagged_invariant": flagged,
                    "status": "BLOCKED_BY_UNILATERAL_VETO"
                }

        # 2. Si aucun veto -> Consensus de flotte validé
        msg = f"✅ Consensus éthique de flotte validé (Aucun veto d'invariant levé)."
        print(f"[{self.nom}] {msg}")

        publish_event(
            job_id=job_id,
            event_type="fleet_ethics_consensus_approved",
            message=msg,
            payload={"consensus_approved": True, "veto_applied": False}
        )

        return {
            "consensus_approved": True,
            "veto_applied": False,
            "veto_by": None,
            "flagged_invariant": None,
            "status": "APPROVED_BY_FLEET_CONSENSUS"
        }
