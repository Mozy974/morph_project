"""
SymbioticHumanInterface : Interface Symbiotique Humain-Agent (Niveau 9.0 Conscience Collective).
Assure le dialogue naturel, la désambiguïsation d'intentions et le pair-programming interactif.
"""

import json
from typing import Dict, Any, List, Optional
from orchestrator.llm import call_llm, DEFAULT_MODEL, TEMP_REDACTEUR
from orchestrator.memory.event_bus import publish_event


class SymbioticHumanInterface:
    """
    Interface Symbiotique (Niveau 9.0).
    Facilite la collaboration fluide et naturelle entre l'ingénieur humain et la conscience collective Morph.
    """

    def __init__(self):
        self.nom = "Symbiotic Human Interface"

    def clarify_human_intent(self, user_prompt: str, job_id: str = "symbiotic_chat") -> Dict[str, Any]:
        """
        Analyse une requête utilisateur ambiguë et génère une réponse explicative claire ou des questions de précision.
        """
        print(f"[{self.nom}] 💬 Dialogue symbiotique pour la requête : '{user_prompt[:50]}...'")

        publish_event(
            job_id=job_id,
            event_type="symbiotic_dialogue_start",
            message=f"💬 Analyse symbiotique d'intention...",
            payload={"prompt_snippet": user_prompt[:80]}
        )

        system_prompt = """Tu es l'Interface Symbiotique de SuperAgent Morph.
Ton rôle est de dialoguer avec l'ingénieur humain de manière naturelle, empathique, précise et partenaire.
Analyse la requête et détermine si l'intention est claire ou nécessite une clarification.

Structure JSON attendue :
{
  "intent_clear": true,
  "understood_goal": "Résumé de l'objectif compris",
  "symbiotic_response": "Explication claire du plan engagé par le Swarm",
  "clarification_questions": []
}"""

        try:
            raw_res = call_llm(
                system_prompt=system_prompt,
                user_prompt=f"REQUÊTE HUMAINE : {user_prompt}",
                model=DEFAULT_MODEL,
                temperature=TEMP_REDACTEUR,
                json_mode=True
            )
            res = json.loads(raw_res)

            publish_event(
                job_id=job_id,
                event_type="symbiotic_dialogue_done",
                message=f"💬 Réponse symbiotique générée pour l'humain.",
                payload=res
            )
            return res

        except Exception as e:
            print(f"[{self.nom}] ⚠️ Fallback dialogue symbiotique : {e}")
            fallback = {
                "intent_clear": True,
                "understood_goal": user_prompt,
                "symbiotic_response": f"J'ai pris en compte votre demande : '{user_prompt}'. Le Swarm Morph démarre l'analyse.",
                "clarification_questions": []
            }
            return fallback
