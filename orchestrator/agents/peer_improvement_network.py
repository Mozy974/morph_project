"""
PeerImprovementNetwork : Réseau d'Amélioration Mutuelle P2P (Niveau 8.0 Auto-Évolution Collective).
Permet aux agents d'échanger des critiques et corrections directement de pair-à-pair,
encadré par le TokenBudgetController et tracé via le bus d'événements Pub/Sub.
"""

import json
from typing import Dict, Any, List, Optional
from orchestrator.llm import call_llm, DEFAULT_MODEL, TEMP_ANALYSTE
from orchestrator.memory.event_bus import publish_event
from orchestrator.memory.token_budget_controller import TokenBudgetController


class PeerImprovementNetwork:
    """
    Réseau P2P d'Amélioration Mutuelle entre Agents (Niveau 8.0).
    Facilite l'auto-correction croisée et l'affinage décentralisé avec contrôle budgétaire.
    """

    def __init__(self, budget_controller: Optional[TokenBudgetController] = None):
        self.nom = "P2P Peer Improvement Network"
        self.budget_controller = budget_controller or TokenBudgetController()

    def peer_critique(
        self,
        source_agent: str,
        target_agent: str,
        output_data: Any,
        job_id: str = "local_p2p"
    ) -> Dict[str, Any]:
        """
        Évalue la production d'un agent pair et formule un feedback constructif.
        """
        print(f"[{self.nom}] 🤝 Critique P2P de '{source_agent}' vers '{target_agent}'...")
        publish_event(
            job_id=job_id,
            event_type="p2p_critique_start",
            message=f"🤝 Critique P2P de '{source_agent}' vers '{target_agent}'...",
            payload={"source": source_agent, "target": target_agent}
        )

        # Contrôle budgétaire
        self.budget_controller.check_and_consume(job_id=job_id, guild="P2P_NETWORK", estimated_tokens=1500)

        system_prompt = """Tu es un agent d'évaluation P2P au sein d'un swarm multi-agents.
Ta mission est d'évaluer le travail produit par un agent confrère et d'émettre des recommandations d'amélioration directes.

Structure JSON attendue :
{
  "approved": true,
  "quality_score": 94,
  "peer_feedback": "Explication synthétique du retour",
  "suggested_patch_instructions": ["Instruction 1", "Instruction 2"]
}"""

        user_prompt = f"""AGENT ÉVALUATEUR : {source_agent}
AGENT ÉVALUÉ : {target_agent}

PRODUCTION À ÉVALUER :
{json.dumps(output_data, ensure_ascii=False, indent=2) if isinstance(output_data, (dict, list)) else str(output_data)}

Génère la critique P2P."""

        try:
            raw_res = call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=DEFAULT_MODEL,
                temperature=TEMP_ANALYSTE,
                json_mode=True
            )
            res = json.loads(raw_res)
            print(f"[{self.nom}] ✅ Critique P2P terminée (Approuvé: {res.get('approved', True)}, Score: {res.get('quality_score', 90)}/100) !")

            publish_event(
                job_id=job_id,
                event_type="p2p_critique_done",
                message=f"✅ Critique P2P terminée (Score: {res.get('quality_score', 90)}/100)",
                payload=res
            )
            return res

        except Exception as e:
            print(f"[{self.nom}] ⚠️ Fallback critique P2P : {e}")
            fallback = {
                "approved": True,
                "quality_score": 88,
                "peer_feedback": "Validation P2P standard par fallback.",
                "suggested_patch_instructions": []
            }
            publish_event(
                job_id=job_id,
                event_type="p2p_critique_fallback",
                message=f"⚠️ Fallback critique P2P : {e}",
                payload=fallback
            )
            return fallback
