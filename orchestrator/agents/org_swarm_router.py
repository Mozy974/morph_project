"""
OrgSwarmRouter : Routeur d'Organisation Multi-Guildes (Niveau 8.0 Auto-Évolution Collective).
Structure et route les tâches complexes vers les Guildes spécialisées (Product, Eng, Security, DevOps).
"""

import json
from typing import Dict, Any, List, Optional
from orchestrator.llm import call_llm, DEFAULT_MODEL, TEMP_ECLAIREUR


class OrgSwarmRouter:
    """
    Routeur d'Organisation en Swarm (Niveau 8.0).
    Orchestre la répartition des tâches entre Guildes d'Ingénierie.
    """

    GUILDS = ["PRODUCT_GUILD", "ENGINEERING_GUILD", "SECURITY_GUILD", "DEVOPS_GUILD"]

    def __init__(self):
        self.nom = "Org Swarm Router"

    def route_task_to_guilds(self, task: str) -> Dict[str, Any]:
        """
        Analyse une tâche complexe et définit le plan d'exécution inter-guildes.
        """
        print(f"[{self.nom}] 🏛️ Routage Swarm pour la tâche : '{task[:50]}...'")

        system_prompt = """Tu es le Routeur d'Organisation en Swarm Multi-Guildes.
Analyse la tâche et détermine les guildes impliquées et la séquence d'exécution.

Guildes disponibles :
- PRODUCT_GUILD (Spécifications & User Stories)
- ENGINEERING_GUILD (Architecture & TDD Code)
- SECURITY_GUILD (Audit & Sécurité)
- DEVOPS_GUILD (Déploiement & Containers)

Structure JSON attendue :
{
  "primary_guild": "ENGINEERING_GUILD",
  "participating_guilds": ["PRODUCT_GUILD", "ENGINEERING_GUILD", "SECURITY_GUILD"],
  "execution_pipeline": [
    {"step": 1, "guild": "PRODUCT_GUILD", "objective": "Définir les critères d'acceptation"},
    {"step": 2, "guild": "ENGINEERING_GUILD", "objective": "Générer la suite TDD et le code"},
    {"step": 3, "guild": "SECURITY_GUILD", "objective": "Auditer le code"}
  ]
}"""

        user_prompt = f"TÂCHE À ROUTER : {task}"

        try:
            raw_res = call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=DEFAULT_MODEL,
                temperature=TEMP_ECLAIREUR,
                json_mode=True
            )
            plan = json.loads(raw_res)
            print(f"[{self.nom}] ✅ Routage Swarm établi ! (Guilde principale: {plan.get('primary_guild')})")
            return plan

        except Exception as e:
            print(f"[{self.nom}] ⚠️ Fallback routage Swarm : {e}")
            return {
                "primary_guild": "ENGINEERING_GUILD",
                "participating_guilds": ["ENGINEERING_GUILD"],
                "execution_pipeline": [
                    {"step": 1, "guild": "ENGINEERING_GUILD", "objective": "Exécution TDD standard"}
                ]
            }
