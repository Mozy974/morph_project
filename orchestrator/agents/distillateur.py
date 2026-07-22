"""
Agent Distillateur : extrait la leçon sémantique d'un run ayant utilisé la boucle de rétroaction.
"""

import json
from typing import List, Dict, Any
from orchestrator.llm import call_llm, DEFAULT_MODEL, TEMP_DISTILLATEUR


class AgentDistillateur:
    def __init__(self):
        self.nom = "Distillateur Omega"

    def executer_distillation(self, sujet: str, historique_feedback: List[Dict[str, Any]], rapport_final: str = "") -> Dict[str, Any]:
        """
        Extrait une leçon persistante d'un run ayant fonctionné grâce aux retours de l'Analyste.

        Args:
            sujet: Le sujet initial.
            historique_feedback: La liste des consignes de feedback générées par l'Analyste.
            rapport_final: Le texte du rapport final (optionnel).

        Returns:
            Dictionnaire au format DistilledSkill.
        """
        print(f"[{self.nom}] 🧠 Distillation de la leçon en cours pour le sujet : '{sujet}'...")

        system_prompt = """Tu es l'architecte de la mémoire sémantique d'un système multi-agents IA.
Un agent de recherche a eu des difficultés initiales sur un sujet et a dû corriger son travail après des retours critiques de l'Analyste.

Ta mission est d'extraire la substantifique moelle de cette expérience et d'édicter une directive corrective claire et réutilisable pour l'avenir.

Tu dois répondre UNIQUEMENT avec un objet JSON valide, sans aucun texte avant ou après.
Structure JSON attendue :
{
  "sujet_cle": "Concept central (ex: 'Sécurité API Python' ou 'Gestion des clés')",
  "contexte_erreur": "Ce qui a été initialement omis, mal compris ou insuffisant",
  "directive_corrective": "Règle stricte et explicite à appliquer pour les futures recherches sur ce thème",
  "mots_cles": ["tag1", "tag2", "tag3", "tag4"]
}

RÈGLES :
- La "directive_corrective" doit être formulée comme un ordre direct pour les futurs agents (ex: "Lors d'une recherche sur la sécurité API Python, toujours inclure l'analyse des modules d'audit (bandit), la gestion KMS/Vault et un guide de migration").
- Sois très factuel et concis."""

        user_prompt = f"""SUJET : {sujet}

HISTORIQUE DES CRITIQUES / CONSIGNES DE L'ANALYSTE :
{json.dumps(historique_feedback, ensure_ascii=False, indent=2)}

Extrais la compétence apprise (DistilledSkill) sous forme de JSON."""

        try:
            raw_response = call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=DEFAULT_MODEL,
                temperature=TEMP_DISTILLATEUR,
                json_mode=True,
            )

            skill = json.loads(raw_response)
            print(f"[{self.nom}] ✅ Compétence distillée avec succès ! (Mots-clés: {skill.get('mots_cles', [])})")
            return skill

        except json.JSONDecodeError:
            print(f"[{self.nom}] ⚠️ Réponse non-JSON, fallback sur compétence générique.")
            return {
                "sujet_cle": sujet,
                "contexte_erreur": "Manque initial de précision sur le sujet",
                "directive_corrective": f"Pour toute recherche sur '{sujet}', approfondir les exemples concrets et les outils d'audit.",
                "mots_cles": [sujet]
            }
        except RuntimeError as e:
            print(f"[{self.nom}] ❌ Erreur lors de la distillation : {e}")
            return {
                "sujet_cle": sujet,
                "contexte_erreur": str(e),
                "directive_corrective": f"Approfondir le sujet '{sujet}' avec des détails techniques et des sources fiables.",
                "mots_cles": [sujet]
            }

    def auto_tune_prompt_guidance(self, benchmark_failures: List[Dict[str, Any]]) -> str:
        """
        Auto-Tuning DSPy Style : Génère une directive d'optimisation dynamique des prompts
        système à partir des échecs ou itérations répétées détectés pendant le benchmark.
        """
        if not benchmark_failures:
            return "✅ Aucun ajustement requis : Taux Pass@1 maximal atteint."

        prompt = (
            f"Analyse ces échecs de benchmark : {json.dumps(benchmark_failures, ensure_ascii=False)}\n"
            "Formule une règle d'amélioration explicite et concise pour optimiser les consignes du Codeur."
        )

        try:
            tuned_rule = call_llm(
                system_prompt="Tu es l'optimiseur de prompts système du SuperAgent. Génère une règle d'amélioration concise.",
                user_prompt=prompt,
                model=DEFAULT_MODEL,
                temperature=0.1
            )
            print(f"[{self.nom}] 🎯 Prompt Auto-Tuning appliqué : {tuned_rule[:60]}...")
            return tuned_rule
        except Exception:
            return "Privilégier la gestion rigoureuse des exceptions et la validation des cas limites."

