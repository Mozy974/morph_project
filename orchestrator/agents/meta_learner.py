"""
MetaLearnerAgent : Agent de Méta-Apprentissage Global (Niveau 7.0 Meta-Learning).
Supervise la flotte d'agents, évalue leurs performances croisées et optimise la stratégie d'ensemble.
"""

import json
import os
import datetime
from typing import Dict, Any, List, Optional
from orchestrator.llm import call_llm, DEFAULT_MODEL, TEMP_DISTILLATEUR

META_STORE_FILE = os.path.join(os.path.dirname(__file__), "..", "memory", "meta_learning.json")


class MetaLearnerAgent:
    """
    Agent Meta-Learner (Niveau 7.0).
    Analyse globale des métriques, des taux de succès inter-agents,
    et recommandation de politiques d'exécution optimales.
    """

    def __init__(self, store_path: str = META_STORE_FILE):
        self.nom = "Meta-Learner Omega"
        self.store_path = os.path.abspath(store_path)
        self.meta_store: Dict[str, Any] = self._load_store()

    def _load_store(self) -> Dict[str, Any]:
        if os.path.exists(self.store_path):
            try:
                with open(self.store_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[{self.nom}] ⚠️ Erreur lecture store meta-learning : {e}")
        return {"policy_version": 1, "insights": [], "recommendations": []}

    def _save_store(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.store_path), exist_ok=True)
            with open(self.store_path, "w", encoding="utf-8") as f:
                json.dump(self.meta_store, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[{self.nom}] ❌ Erreur sauvegarde store meta-learning : {e}")

    def analyze_fleet_performance(self, execution_logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyse l'historique d'exécution multi-agents et génère des directives d'optimisation globale.

        Args:
            execution_logs: Liste d'événements et de durées d'exécution par agent.

        Returns:
            Dict contenant les insights de méta-apprentissage et la mise à jour des règles d'ensemble.
        """
        print(f"[{self.nom}] 🧠 Analyse de méta-apprentissage globale ({len(execution_logs)} exécutions)...")

        if not execution_logs:
            return {
                "status": "NO_DATA",
                "insights": ["Données d'exécutions insuffisantes pour formaliser des directives."],
                "recommendations": []
            }

        system_prompt = """Tu es l'Agent Meta-Learner d'une plateforme d'ingénierie logicielle autonome multi-agents.
Ta mission est d'analyser les performances globales du système et d'émettre des politiques d'optimisation (Meta-Policy).

Structure JSON attendue :
{
  "fleet_health_score": 95,
  "key_insights": ["Insight 1", "Insight 2"],
  "global_policy_directives": ["Directive 1", "Directive 2"],
  "recommended_agent_adjustments": {
    "Codeur": "Ajustement recommandé",
    "AutoCorrector": "Ajustement recommandé"
  }
}"""

        user_prompt = f"""HISTORIQUE D'EXÉCUTION FLOTTE D'AGENTS :
{json.dumps(execution_logs[:10], ensure_ascii=False, indent=2)}

Formule les recommandations de méta-apprentissage pour le système."""

        try:
            raw_res = call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=DEFAULT_MODEL,
                temperature=TEMP_DISTILLATEUR,
                json_mode=True
            )
            data = json.loads(raw_res)

            record = {
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "fleet_health_score": data.get("fleet_health_score", 90),
                "key_insights": data.get("key_insights", []),
                "global_policy_directives": data.get("global_policy_directives", []),
                "recommended_agent_adjustments": data.get("recommended_agent_adjustments", {})
            }

            self.meta_store["insights"].append(record)
            self.meta_store["policy_version"] += 1
            self._save_store()

            print(f"[{self.nom}] ✅ Méta-apprentissage complété (Score Santé: {record['fleet_health_score']}/100) !")
            return record

        except Exception as e:
            print(f"[{self.nom}] ⚠️ Erreur analyse meta-learner, fallback : {e}")
            fallback = {
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "fleet_health_score": 85,
                "key_insights": ["Privilégier la modularité et l'isolation des dépendances."],
                "global_policy_directives": ["Accroître la rigueur du True TDD."],
                "recommended_agent_adjustments": {}
            }
            return fallback
