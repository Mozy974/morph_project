"""
AgentFactory : Synthétiseur dynamique d'agents et compétences (Niveau 6.0 Auto-Évolution).
Permet de générer à la volée de nouveaux agents spécialisés sans redémarrer le système.
"""

import json
import os
import datetime
from typing import Dict, Any, List, Optional
from orchestrator.llm import call_llm, DEFAULT_MODEL, TEMP_CODEUR

REGISTRY_FILE = os.path.join(os.path.dirname(__file__), "..", "memory", "dynamic_agents_registry.json")


class DynamicAgent:
    """Agent généré dynamiquement par l'AgentFactory."""

    def __init__(self, name: str, role: str, system_prompt: str, domain: str):
        self.nom = name
        self.role = role
        self.system_prompt = system_prompt
        self.domain = domain

    def execute(self, user_prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Exécute la mission de l'agent dynamique."""
        full_context = f"\nCONTEXTE:\n{json.dumps(context, ensure_ascii=False)}" if context else ""
        return call_llm(
            system_prompt=self.system_prompt,
            user_prompt=f"{user_prompt}{full_context}",
            model=DEFAULT_MODEL,
            temperature=TEMP_CODEUR
        )


class AgentFactory:
    """
    Factory et registre d'agents dynamiques.
    Détecte les besoins non couverts par les agents standard et génère un nouvel agent spécialisé.
    """

    def __init__(self, registry_path: str = REGISTRY_FILE):
        self.nom = "AgentFactory Prime"
        self.registry_path = os.path.abspath(registry_path)
        self.registry: Dict[str, Any] = self._load_registry()

    def _load_registry(self) -> Dict[str, Any]:
        if os.path.exists(self.registry_path):
            try:
                with open(self.registry_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[{self.nom}] ⚠️ Erreur lecture registre agents : {e}")
        return {}

    def _save_registry(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.registry_path), exist_ok=True)
            with open(self.registry_path, "w", encoding="utf-8") as f:
                json.dump(self.registry, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[{self.nom}] ❌ Erreur sauvegarde registre agents : {e}")

    def synthesize_agent(self, domain_need: str, task_description: str) -> DynamicAgent:
        """
        Génère un nouvel agent spécialisé pour un domaine ou une tâche complexe non couverte.
        """
        print(f"[{self.nom}] 🏭 Synthèse d'un nouvel agent spécialisé pour : '{domain_need}'...")

        # Vérifie si un agent existe déjà pour ce domaine
        if domain_need in self.registry:
            spec = self.registry[domain_need]
            print(f"[{self.nom}] ⚡ Agent existant réutilisé : {spec['name']}")
            return DynamicAgent(
                name=spec["name"],
                role=spec["role"],
                system_prompt=spec["system_prompt"],
                domain=spec["domain"]
            )

        prompt_design_sys = """Tu me sers d'architecte multi-agents.
Un utilisateur ou un système a besoin d'un nouvel agent spécialisé sur un domaine précis.
Génère une spécification complète d'agent au format JSON :
{
  "name": "Nom de l'agent (ex: AgentGraphQL, SqlSpannerSpecialist)",
  "role": "Description courte du rôle",
  "system_prompt": "Le prompt système complet, directif, précis pour cet agent spécialisé",
  "domain": "Domaine de compétence (ex: graphql, spanner, kubernetes)"
}"""

        prompt_design_user = f"""DOMAINE DU BESOIN : {domain_need}
DESCRIPTION DE LA TÂCHE : {task_description}"""

        try:
            raw_res = call_llm(
                system_prompt=prompt_design_sys,
                user_prompt=prompt_design_user,
                model=DEFAULT_MODEL,
                temperature=0.2,
                json_mode=True
            )
            spec = json.loads(raw_res)

            agent_obj = DynamicAgent(
                name=spec.get("name", f"Agent_{domain_need.capitalize()}"),
                role=spec.get("role", f"Spécialiste {domain_need}"),
                system_prompt=spec.get("system_prompt", f"Tu es un expert de {domain_need}."),
                domain=domain_need
            )

            # Enregistrement
            self.registry[domain_need] = {
                "name": agent_obj.nom,
                "role": agent_obj.role,
                "system_prompt": agent_obj.system_prompt,
                "domain": agent_obj.domain,
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
            self._save_registry()

            print(f"[{self.nom}] ✨ Agent '{agent_obj.nom}' créé et enregistré avec succès !")
            return agent_obj

        except Exception as e:
            print(f"[{self.nom}] ⚠️ Échec de synthèse dynamique, fallback sur agent générique : {e}")
            fallback = DynamicAgent(
                name=f"AgentSpecialiste_{domain_need}",
                role=f"Expert {domain_need}",
                system_prompt=f"Tu es un expert autonome spécialisé dans {domain_need}. Règle la tâche efficacement.",
                domain=domain_need
            )
            return fallback

    def get_agent(self, domain_need: str) -> Optional[DynamicAgent]:
        """Récupère un agent du registre s'il existe."""
        if domain_need in self.registry:
            spec = self.registry[domain_need]
            return DynamicAgent(
                name=spec["name"],
                role=spec["role"],
                system_prompt=spec["system_prompt"],
                domain=spec["domain"]
            )
        return None
