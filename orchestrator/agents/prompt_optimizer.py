"""
PromptOptimizerAgent : Agent d'optimisation automatique des prompts système (Niveau 6.0 Auto-Évolution).
Analyse les échecs et métriques d'exécution pour générer et évaluer des variantes de prompts système.
"""

import json
import os
import datetime
from typing import Dict, Any, List, Optional
from orchestrator.llm import call_llm, DEFAULT_MODEL, TEMP_DISTILLATEUR

PROMPTS_STORE_FILE = os.path.join(os.path.dirname(__file__), "..", "memory", "optimized_prompts.json")


class PromptOptimizerAgent:
    """
    Agent Meta-Prompting / DSPy-style MIPRO Optimizer.
    Ajuste dynamiquement les consignes des agents (Codeur, AutoCorrector, etc.)
    en fonction des échecs constatés dans la Sandbox.
    """

    def __init__(self, store_path: str = PROMPTS_STORE_FILE):
        self.nom = "PromptOptimizer Alpha"
        self.store_path = os.path.abspath(store_path)
        self.optimized_prompts: Dict[str, Any] = self._load_prompts()

    def _load_prompts(self) -> Dict[str, Any]:
        """Charge le store de prompts optimisés."""
        if os.path.exists(self.store_path):
            try:
                with open(self.store_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[{self.nom}] ⚠️ Erreur lecture store prompts : {e}")
        return {}

    def _save_prompts(self) -> None:
        """Sauvegarde les prompts optimisés."""
        try:
            os.makedirs(os.path.dirname(self.store_path), exist_ok=True)
            with open(self.store_path, "w", encoding="utf-8") as f:
                json.dump(self.optimized_prompts, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[{self.nom}] ❌ Erreur sauvegarde store prompts : {e}")

    def optimize_prompt(
        self,
        agent_name: str,
        current_prompt: str,
        execution_failures: List[Dict[str, Any]],
        success_rate: float = 0.0
    ) -> Dict[str, Any]:
        """
        Analyse les échecs récents d'un agent et génère un prompt système optimisé.

        Args:
            agent_name: Nom de l'agent cible (ex: 'Codeur', 'AutoCorrector')
            current_prompt: Prompt système actuel
            execution_failures: Liste des erreurs et tracebacks rencontrés
            success_rate: Taux de succès actuel (0.0 à 1.0)

        Returns:
            Dict contenant le prompt optimisé et la justification de la mutation.
        """
        print(f"[{self.nom}] 🧬 Auto-Tuning du prompt pour l'agent '{agent_name}' (Succès: {success_rate*100:.1f}%)...")

        if not execution_failures:
            return {
                "agent_name": agent_name,
                "optimized_prompt": current_prompt,
                "mutation_applied": False,
                "reason": "Aucun échec détecté, conservation du prompt d'origine."
            }

        system_prompt = """Tu es un expert en Meta-Prompting et ingénierie de prompts autonomes (DSPy / MIPRO style).
Ta tâche est d'optimiser le PROMPT SYSTÈME d'un agent IA en fonction des erreurs d'exécution récurrentes.

RÈGLES STRICTES :
1. Conserve la mission principale de l'agent.
2. Ajoute des directives concrètes, explicites et ciblées pour éviter les erreurs observées.
3. Réponds UNIQUEMENT sous forme d'objet JSON valide avec cette structure :
{
  "reasoning": "Explication synthétique des faiblesses identifiées",
  "added_directives": ["Directive 1", "Directive 2"],
  "optimized_prompt": "Le nouveau prompt système complet et prêt à l'emploi"
}"""

        user_prompt = f"""AGENT CIBLE : {agent_name}

PROMPT ACTUEL :
{current_prompt}

ÉCHECS D'EXÉCUTION RÉCENTS ({len(execution_failures)} cas) :
{json.dumps(execution_failures[:5], ensure_ascii=False, indent=2)}

Génère la version optimisée du prompt système."""

        try:
            raw_res = call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=DEFAULT_MODEL,
                temperature=TEMP_DISTILLATEUR,
                json_mode=True
            )

            data = json.loads(raw_res)
            new_prompt = data.get("optimized_prompt", current_prompt)

            # Mutation record
            record = {
                "agent_name": agent_name,
                "optimized_prompt": new_prompt,
                "reasoning": data.get("reasoning", "Optimisation basée sur l'historique d'échecs"),
                "added_directives": data.get("added_directives", []),
                "mutation_applied": True,
                "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "version": self.optimized_prompts.get(agent_name, {}).get("version", 0) + 1
            }

            self.optimized_prompts[agent_name] = record
            self._save_prompts()

            print(f"[{self.nom}] ✅ Prompt pour '{agent_name}' optimisé v{record['version']} ! ({len(record['added_directives'])} directives ajoutées)")
            return record

        except Exception as e:
            print(f"[{self.nom}] ❌ Erreur lors de l'optimisation : {e}")
            return {
                "agent_name": agent_name,
                "optimized_prompt": current_prompt,
                "mutation_applied": False,
                "reason": f"Erreur d'optimisation: {str(e)}"
            }

    def get_active_prompt(self, agent_name: str, fallback_prompt: str) -> str:
        """Retourne le prompt optimisé s'il existe, sinon le fallback."""
        entry = self.optimized_prompts.get(agent_name)
        if entry and entry.get("optimized_prompt"):
            return entry["optimized_prompt"]
        return fallback_prompt
